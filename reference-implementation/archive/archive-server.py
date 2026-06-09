#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
archive-server.py
Indexable Knowledge Archive — local AI search server ("Third Brain")

Run:     python archive-server.py
Open:    http://localhost:5174
Share:   python archive-server.py --share   (binds 0.0.0.0 for LAN access)

What it does:
  - Serves archive.html over HTTP (avoids file:// CORS limits)
  - POST /query runs a retrieval step (BM25) then asks a local Claude CLI
  - Extracts the most relevant article passages and feeds them as context
  - No API key needed — reuses your local `claude` CLI session

Design notes:
  - Retrieval uses BM25 over char-2gram tokens, which works well for Korean
    text and short codes. Falls back to a simple term-count scorer if the
    `rank_bm25` package is not installed.
  - This is a portfolio/demo build that ships with a small, fully fictional
    sample archive (archive.html). No real organization data is included.
    Set ORG_NAME below to brand it for your own knowledge base.
"""

import re, json, subprocess, threading, webbrowser, shutil, os, socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
from datetime import datetime

# Branding — shown in the assistant's system prompt. Change to your org/domain.
ORG_NAME = os.environ.get("ARCHIVE_ORG_NAME", "Demo Org")

# BM25 ranking (core of search quality). Graceful fallback to term-count if missing.
try:
    from rank_bm25 import BM25Okapi
    _HAS_BM25 = True
except Exception:
    BM25Okapi = None
    _HAS_BM25 = False

# Locate the `claude` CLI automatically
def _find_claude():
    # 1) PATH lookup
    p = shutil.which("claude")
    if p: return p
    # 2) APPDATA / LOCALAPPDATA based lookup
    for appdata in [os.environ.get("APPDATA",""), os.environ.get("LOCALAPPDATA","")]:
        for name in ["claude.CMD", "claude.cmd", "claude.exe", "claude"]:
            c = Path(appdata) / "npm" / name
            if c.exists(): return str(c)
    # 3) known user paths (fallback)
    import glob
    patterns = [
        r"C:\Users\*\AppData\Roaming\npm\claude.CMD",
        r"C:\Users\*\AppData\Roaming\npm\claude.cmd",
        r"C:\Users\*\AppData\Local\Programs\claude\claude.exe",
    ]
    for pat in patterns:
        hits = glob.glob(pat)
        if hits: return hits[0]
    return None

CLAUDE_PATH = _find_claude()

PORT     = 5174
BASE     = Path(__file__).parent
HTML     = BASE / "archive.html"
CONV_LOG = BASE / "conversations.jsonl"   # Q/A log (query/answer/time/ip/sources) — 1 line = 1 turn

def log_conversation(ip, query, answer, sources):
    """Append every Q/A to JSONL, one line per turn. Failures never affect serving."""
    try:
        rec = {
            "time":    datetime.now().isoformat(timespec="seconds"),
            "ip":      ip,
            "query":   query,
            "answer":  answer,
            "sources": sources,
        }
        with open(CONV_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # logging is best-effort; search takes priority

# ── Archive parsing (loaded once at server start) ────────────────────
_html   = None
_arts   = []
_bm25     = None   # BM25Okapi instance (built once in build_index())
_bm25_ids = []     # corpus index ↔ article id mapping (same order)

def load():
    global _html, _arts
    _html = HTML.read_text(encoding="utf-8")
    _arts = []
    for m in re.finditer(r'<article[^>]+id="([^"]+)"', _html):
        seg     = _html[m.start(): m.start() + 600]
        title_m = re.search(r'class="at">([^<]+)', seg)
        badge_m = re.search(r'class="badge[^"]*">([^<]+)', seg)
        tags_m  = re.search(r'data-tags="([^"]*)"', _html[m.start(): m.start() + 400])
        # estimate end of article body
        end_m   = re.search(r'</article>', _html[m.start():m.start() + 30000])
        end     = m.start() + end_m.end() if end_m else m.start() + 15000
        _arts.append({
            "id":    m.group(1),
            "title": re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else "?",
            "cat":   re.sub(r"\s+", " ", badge_m.group(1)).strip() if badge_m else "?",
            "tags":  tags_m.group(1) if tags_m else "",
            "pos":   m.start(),
            "end":   end,
        })
    build_index()

def strip_tags(s): return re.sub(r"<[^>]+>", "", s)
def norm(s):       return re.sub(r"\s+", " ", s).strip()

def article_at(pos):
    best = _arts[0] if _arts else None
    for a in _arts:
        if a["pos"] <= pos: best = a
        else: break
    return best

# ── BM25 index (search ranking) ──────────────────────────────────────
def _tok_char2(s):
    """char-2gram tokenizer: strip whitespace, take adjacent 2-char windows.
    Strong for Korean and short codes; IDF (common-code noise) and document-length
    normalization (long-doc bias) are handled by BM25Okapi."""
    s = re.sub(r"\s+", "", s.lower())
    return [s[i:i+2] for i in range(len(s) - 1)] if len(s) >= 2 else ([s] if s else [])

def _doc_text(a):
    """BM25 corpus text for one article = title + tags + body (tags stripped, ws normalized).
    Title/tags go before the body so title terms appear once more in the corpus — a natural
    field boost."""
    body = norm(strip_tags(_html[a["pos"]:a["end"]]))
    return a["title"] + " " + a.get("tags", "") + " " + body

def build_index():
    """Built once (at end of load()) — tokenize each article to char-2grams and build the
    BM25 index. If rank_bm25 is unavailable, leave the index empty and fall back to scoring."""
    global _bm25, _bm25_ids
    if not _HAS_BM25 or not _arts:
        _bm25, _bm25_ids = None, []
        return
    _bm25_ids = [a["id"] for a in _arts]
    _bm25 = BM25Okapi([_tok_char2(_doc_text(a)) for a in _arts])

# Query synonym expansion — bridges the gap between how users phrase things and
# the archive's own terminology. Codes below are illustrative sample codes
# (ZSD*/ZMM* are fictional; SU01/FD32/VF11/VL09/VKM4 are standard SAP).
SEARCH_SYNONYMS = {
    "월초":   ["월초", "월별", "월말", "결산", "마감", "정기", "ZSD070", "ZSD143"],
    "월간":   ["월별", "월말", "마감", "결산", "정기", "ZSD143"],
    "월별":   ["월별", "월말", "결산", "정기", "ZSD070", "ZSD143"],
    "정기":   ["정기", "월별", "월말", "결산", "매달"],
    "매달":   ["매달", "월별", "월말", "결산", "정기"],
    "이번달": ["이번달", "월별", "월말", "결산", "마감", "정기"],
    "마감":   ["월말", "결산", "마감"],
    "결산":   ["월말", "마감", "결산", "ZSD143", "ZCO143"],
    "월말":   ["월말", "마감", "결산", "ZSD143"],
    "매출취소": ["취소요청", "빌링취소", "ZSD030", "ZSD034"],
    "취소":   ["취소", "ZSD030", "ZSD034", "VF11"],
    "출고":   ["출고", "납품", "VL09", "ZSD025"],
    "권한":   ["권한", "SU01", "역할"],
    "여신":   ["여신", "Credit", "BLOCK", "FD32", "VKM4"],
    "신규":   ["신규", "입사", "계정", "SU01"],
    "입사":   ["입사", "신규", "계정"],
    "반품":   ["반품", "RE", "ZSD035", "CR", "DR"],
    "세금계산서": ["세금계산서", "계산서", "ZSD010"],
    "오더":   ["오더", "판매오더", "내부오더", "IO"],
    "차변":   ["차변", "대변", "분개", "회계문서"],
    "대변":   ["대변", "차변", "CreditMemo", "대변메모"],
    "전표흐름": ["전표흐름", "VA03", "역추적", "취소순서"],
    "판매단가": ["판매단가", "NETPR", "ZSD077", "ZTSD010"],
    "NETPR":  ["NETPR", "판매단가", "ZTSD010", "단가"],
    "계산서":  ["계산서", "세금계산서", "발행", "ZSD010"],
}

def expand_query(keywords):
    out = list(keywords)
    for kw in keywords:
        for base, syns in SEARCH_SYNONYMS.items():
            if base in kw or kw in base:
                out.extend(syns)
    return list(dict.fromkeys(out))

def make_pattern(kw):
    # short ASCII codes (RE, CR, DR …) get word-boundary matching → avoids substring noise inside English words
    if len(kw) <= 3 and re.fullmatch(r"[A-Za-z0-9]+", kw):
        return re.compile(r"(?<![A-Za-z])" + re.escape(kw) + r"(?![A-Za-z])")
    return re.compile(re.escape(kw), re.I)

def extract_passage(a, keywords, opening_chars=300, window=2200):
    """Long articles lose their tail if you only send the head. So: find where a keyword first
    matches and excerpt around it, prepending the article head (title/intro) for context."""
    seg_s, seg_e = a["pos"], a["end"]
    earliest = None
    for kw in keywords:
        m = make_pattern(kw).search(_html, seg_s, seg_e)
        if m and (earliest is None or m.start() < earliest):
            earliest = m.start()
    # no match, or match is in the head (intro) → take from the top
    if earliest is None or earliest <= seg_s + opening_chars:
        return norm(strip_tags(_html[seg_s: seg_e]))[:window]
    # match is deeper in the article → head (title/intro) + excerpt around the match
    opening = norm(strip_tags(_html[seg_s: seg_s + opening_chars]))
    s = max(seg_s, earliest - 400)
    e = min(seg_e, earliest + (window - 600))
    passage = norm(strip_tags(_html[s:e]))
    return (opening + " … " + passage)[:window]

def _extract_keywords(query):
    """Extract search terms from the query then synonym-expand (shared by BM25/legacy)."""
    keywords = re.findall(r"[A-Za-z가-힣][A-Za-z가-힣0-9_]{1,}", query)
    if not keywords:
        keywords = query.split()[:4]
    return expand_query(keywords)

def _rank_legacy_scored(keywords, top_n):
    """Legacy scoring (body term-count + title/tags ×3). Fallback path when BM25 is unavailable.
    Returns: [(article_id, score)] top N (score>0)."""
    scores = defaultdict(int)
    for kw in keywords:                      # 1) body hits
        pat = make_pattern(kw)
        for m in pat.finditer(_html):
            a = article_at(m.start())
            if a: scores[a["id"]] += 1
    for a in _arts:                          # 2) title/tags hits ×3
        hay = (a["title"] + " " + a.get("tags", "")).lower()
        for kw in keywords:
            if make_pattern(kw).search(hay):
                scores[a["id"]] += 3
    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_n]
    return [(aid, s) for aid, s in ranked if s > 0]

def _rank_scored(query, top_n):
    """BM25 (char-2gram) ranking → [(id, score)] top N.
    BM25 ranking tokenizes the *raw query* into char-2grams. Synonym expansion (expand_query)
    is intentionally NOT applied to ranking — in measured evals, injecting synonyms into ranking
    HURT recall@1 (common code-synonyms pull unrelated articles up; IDF already handles this).
    Synonym expansion is kept only for choosing which passage to excerpt (extract_passage) and
    for the legacy fallback.
    Falls back to legacy term-count (+synonyms) scoring if BM25 is unavailable."""
    if _bm25 is None:
        return _rank_legacy_scored(_extract_keywords(query), top_n)
    q_tok = _tok_char2(query)
    if not q_tok:
        return []
    scores = _bm25.get_scores(q_tok)
    order  = sorted(range(len(_bm25_ids)), key=lambda i: -scores[i])
    return [(_bm25_ids[i], float(scores[i])) for i in order[:top_n]]

def rank_article_ids(query, top_n=3):
    """Pure ranking of the deployed searcher — top N article ids (entry point an eval script
    can call directly). Returns top N regardless of score sign (eval reproducibility)."""
    return [aid for aid, _ in _rank_scored(query, top_n)]

def search_relevant(query, top_n=3):
    """Top N relevant article excerpts: BM25 ranking → passage extraction.
    Ranking is BM25 (raw-query char-2gram). Synonym expansion is kept for the passage-extraction
    step (not ranking — see _rank_scored). Passage extraction logic is unchanged."""
    keywords = _extract_keywords(query)
    ranked   = _rank_scored(query, top_n)
    # if any positive-score candidate exists, drop non-positive (effectively irrelevant) ones
    if any(s > 0 for _, s in ranked):
        ranked = [(aid, s) for aid, s in ranked if s > 0]

    art_map  = {a["id"]: a for a in _arts}
    contexts = []
    for art_id, _ in ranked:
        a = art_map.get(art_id)
        if not a: continue
        body = extract_passage(a, keywords)
        contexts.append(f"[Article: #{a['id']} — {a['title']} ({a['cat']})]\n{body}")
    return contexts

def build_prompt(query, contexts):
    ctx_text = "\n\n".join(contexts) if contexts else "(no related article)"
    return f"""당신은 {ORG_NAME}의 운영 지식 아카이브 AI 검색 도우미입니다.

아래는 질문과 관련된 아카이브 내용입니다:
{ctx_text}

---
사용자 질문: {query}

위 내용을 바탕으로 한국어로 간결하게 답변하세요.
- T-Code 언급 시 "T-Code — 화면명" 형식으로 표기하세요.
- 아카이브에 없는 내용은 "아카이브에 없는 내용"임을 명시한 뒤 보완하세요.
- 답변은 간결하게, 필요하면 번호 목록으로 정리하세요.
- 당신은 페이지에 임베드된 챗봇이며, 답변 직후 관련 아티클로 페이지가 자동 스크롤·강조됩니다.
  따라서 "직접 이동시킬 수 없다"고 말하지 마세요. 대신 "아래 [페이지에서 이 내용 보기] 버튼을
  누르거나, 방금 강조된 위치를 확인하세요"라고 안내하세요. 출처는 시스템이 자동으로 표시하므로
  답변 본문에 '참조:' 를 직접 적지 마세요."""

def call_claude(prompt):
    """Run a single response via `claude -p` (Korean-encoding-safe)."""
    import tempfile
    if not CLAUDE_PATH:
        return "[error] claude CLI not found. Make sure Claude Code is installed and logged in."

    # write the prompt to a UTF-8 temp file → avoids CMD argument encoding issues
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        ) as f:
            f.write(prompt)
            tmp = Path(f.name)

        env = {**os.environ, "PYTHONUTF8": "1"}

        # pass the prompt over stdin — sidesteps Korean encoding issues entirely.
        # chcp 65001 forces cmd.exe output to UTF-8.
        shell_cmd = f'chcp 65001 >nul && "{CLAUDE_PATH}" -p -'
        result = subprocess.run(
            shell_cmd,
            input=prompt.encode("utf-8"),
            capture_output=True,
            timeout=90,
            shell=True,
            env=env,
        )

        # CMD (shell=True) output may be CP949, otherwise UTF-8 — auto-fallback
        def safe_decode(b):
            for enc in ("utf-8", "cp949", "euc-kr"):
                try:
                    return b.decode(enc).strip()
                except (UnicodeDecodeError, AttributeError):
                    continue
            return b.decode("utf-8", errors="replace").strip()

        stdout = safe_decode(result.stdout)
        stderr = safe_decode(result.stderr)

        if stdout:
            return stdout
        return f"[error] empty response. stderr: {stderr[:200]}" if stderr else "[error] claude returned an empty response."
    except subprocess.TimeoutExpired:
        return "[error] response timed out (90s). Try again."
    except Exception as e:
        return f"[error] {e}"
    finally:
        if tmp and tmp.exists():
            tmp.unlink(missing_ok=True)

# ── HTTP handler ─────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silence default access logs

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            content = HTML.read_text(encoding="utf-8")
            # inject the AI panel script just before </body>
            content = content.replace("</body>", AI_PANEL_HTML + "\n</body>")
            data = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type",   "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/query":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                raw      = self.rfile.read(length)
                # request-body encoding defense (UTF-8 first, CP949 fallback)
                try:
                    body_str = raw.decode("utf-8")
                except UnicodeDecodeError:
                    body_str = raw.decode("cp949", errors="replace")
                body  = json.loads(body_str)
                query = body.get("query", "").strip()

                if not query:
                    resp = json.dumps({"answer": "질문을 입력하세요.", "sources": []})
                else:
                    contexts = search_relevant(query)
                    prompt   = build_prompt(query, contexts)
                    answer   = call_claude(prompt)
                    sources  = []
                    for c in contexts:
                        m = re.search(r"#([^\s—]+)", c)
                        if m: sources.append("#" + m.group(1))
                    log_conversation(self.client_address[0], query, answer, sources)
                    resp = json.dumps({
                        "answer":  answer,
                        "sources": sources,
                    }, ensure_ascii=False)
            except Exception as e:
                resp = json.dumps({"answer": f"[server error] {e}", "sources": []})

            data = resp.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type",   "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self._cors()
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

# ── AI panel HTML/CSS/JS (injected into archive.html) ────────────────
AI_PANEL_HTML = """
<style>
#ai-toggle {
  position: fixed; top: 72px; right: 0;
  width: 36px; height: 72px;
  background: #1d4ed8; color: #fff;
  border: none; border-radius: 8px 0 0 8px;
  cursor: pointer; font-size: 18px;
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; box-shadow: -2px 2px 8px rgba(0,0,0,.2);
  writing-mode: vertical-rl; letter-spacing: 2px;
  font-weight: 700; font-size: 12px; padding: 8px 6px;
}
#ai-toggle:hover { background: #1e40af; }
#ai-panel {
  position: fixed; top: 0; right: -400px; width: 380px; height: 100vh;
  background: #f8fafc; border-left: 2px solid #e2e8f0;
  box-shadow: -4px 0 16px rgba(0,0,0,.12);
  display: flex; flex-direction: column;
  transition: right .3s ease; z-index: 999;
  font-family: 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
}
#ai-panel.open { right: 0; }
#ai-header {
  padding: 16px; background: #1d4ed8; color: #fff;
  display: flex; align-items: center; justify-content: space-between;
  flex-shrink: 0;
}
#ai-header h3 { margin: 0; font-size: 14px; font-weight: 700; }
#ai-header span { font-size: 11px; opacity: .8; }
#ai-close { background: none; border: none; color: #fff; font-size: 20px; cursor: pointer; padding: 0 4px; }
#ai-body { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 8px; }
#ai-input-area { padding: 12px; border-top: 1px solid #e2e8f0; flex-shrink: 0; background: #fff; }
#ai-input {
  width: 100%; box-sizing: border-box;
  border: 1px solid #cbd5e1; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; resize: none; height: 64px;
  outline: none;
}
#ai-input:focus { border-color: #1d4ed8; box-shadow: 0 0 0 2px rgba(29,78,216,.15); }
#ai-send {
  margin-top: 6px; width: 100%;
  background: #1d4ed8; color: #fff;
  border: none; border-radius: 8px;
  padding: 8px; font-size: 13px; font-weight: 600;
  cursor: pointer;
}
#ai-send:hover { background: #1e40af; }
#ai-send:disabled { background: #94a3b8; cursor: not-allowed; }
.ai-bubble { padding: 10px 12px; border-radius: 10px; font-size: 13px; line-height: 1.6; }
.ai-bubble.user { background: #dbeafe; color: #1e3a5f; align-self: flex-end; max-width: 90%; }
.ai-bubble.bot  { background: #fff; border: 1px solid #e2e8f0; color: #1e293b; align-self: flex-start; max-width: 100%; }
.ai-bubble.loading { color: #64748b; background: #f1f5f9; font-style: italic; }
.ai-sources { font-size: 11px; color: #64748b; margin-top: 6px; padding: 6px 8px; background: #f8fafc; border-radius: 4px; }
.ai-src-btn {
  display: inline-block; margin: 2px 4px 2px 0;
  background: #eff6ff; color: #1d4ed8;
  border: 1px solid #bfdbfe; border-radius: 6px;
  padding: 3px 9px; font-size: 11px; font-weight: 600;
  cursor: pointer; text-decoration: none;
}
.ai-src-btn:hover { background: #1d4ed8; color: #fff; }
.ai-goto {
  display: block; margin-top: 8px; width: 100%;
  background: #0ea5e9; color: #fff;
  border: none; border-radius: 8px;
  padding: 7px; font-size: 12px; font-weight: 700; cursor: pointer;
}
.ai-goto:hover { background: #0284c7; }
@keyframes ai-flash {
  0%   { background: #fde68a; box-shadow: 0 0 0 4px #fde68a; }
  100% { background: transparent; box-shadow: 0 0 0 0 transparent; }
}
.ai-highlight { animation: ai-flash 2.2s ease-out; border-radius: 8px; }
</style>

<button id="ai-toggle" onclick="toggleAI()" title="AI search">AI</button>

<div id="ai-panel">
  <div id="ai-header">
    <div>
      <h3>Claude AI Search</h3>
      <span>archive-grounded · local CLI</span>
    </div>
    <button id="ai-close" onclick="toggleAI()">✕</button>
  </div>
  <div id="ai-body"></div>
  <div id="ai-input-area">
    <textarea id="ai-input" placeholder="e.g. ZSD030 매출취소 절차가 뭐야?&#10;Enter = send  /  Shift+Enter = newline"></textarea>
    <button id="ai-send" onclick="sendQuery()">Ask</button>
  </div>
</div>

<script>
function toggleAI() {
  document.getElementById('ai-panel').classList.toggle('open');
}

document.getElementById('ai-input').addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuery(); }
});

// scroll to + highlight the article on the page
function scrollToArticle(id) {
  const cleanId = id.replace('#','');
  const el = document.getElementById(cleanId);
  if (!el) { alert('Article (#' + cleanId + ') not found on the page.'); return; }
  el.scrollIntoView({behavior: 'smooth', block: 'start'});
  el.classList.remove('ai-highlight');
  void el.offsetWidth;            // force reflow → replay animation
  el.classList.add('ai-highlight');
  setTimeout(() => el.classList.remove('ai-highlight'), 2400);
}

function addBubble(text, cls, sources) {
  const body = document.getElementById('ai-body');
  const div  = document.createElement('div');
  div.className = 'ai-bubble ' + cls;
  div.innerHTML = text.replace(/\\n/g, '<br>');
  body.appendChild(div);
  if (sources && sources.length) {
    const s = document.createElement('div');
    s.className = 'ai-sources';
    s.innerHTML = 'Related: ' + sources.map(id =>
      `<a class="ai-src-btn" onclick="scrollToArticle('${id.replace('#','')}')">${id}</a>`
    ).join('');
    const first = sources[0].replace('#','');
    s.innerHTML += `<button class="ai-goto" onclick="scrollToArticle('${first}')">📍 See this on the page (${sources[0]})</button>`;
    body.appendChild(s);
  }
  body.scrollTop = body.scrollHeight;
  return div;
}

async function sendQuery() {
  const input = document.getElementById('ai-input');
  const btn   = document.getElementById('ai-send');
  const query = input.value.trim();
  if (!query) return;

  input.value = '';
  addBubble(query, 'user');
  const loading = addBubble('Generating…', 'loading');
  btn.disabled = true;

  try {
    const res  = await fetch(window.location.origin + '/query', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({query}),
    });
    const data = await res.json();
    loading.remove();
    addBubble(data.answer, 'bot', data.sources);
    if (data.sources && data.sources.length) {
      setTimeout(() => scrollToArticle(data.sources[0]), 400);
    }
  } catch(e) {
    loading.remove();
    addBubble('Could not reach the server.<br><small>Is archive-server.py running?</small>', 'bot');
  } finally {
    btn.disabled = false;
    input.focus();
  }
}
</script>
"""

# ── Server boot ──────────────────────────────────────────────────────
class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", action="store_true",
                    help="LAN share mode (bind 0.0.0.0 → reachable from the same network)")
    cli = ap.parse_args()

    HOST = "0.0.0.0" if cli.share else "localhost"
    ip   = lan_ip()

    print(f"\n  Loading archive…")
    load()
    print(f"  Loaded {len(_arts)} articles" + ("" if _HAS_BM25 else "  (rank_bm25 not installed → fallback scorer)"))
    print(f"  claude CLI : {CLAUDE_PATH or '!! not found !!'}")
    print(f"\n  Server: http://localhost:{PORT}")
    if cli.share:
        print(f"  ┌──────────────────────────────────────────────┐")
        print(f"  │  LAN link (share with teammates on the LAN):  ")
        print(f"  │     http://{ip}:{PORT}")
        print(f"  └──────────────────────────────────────────────┘")
        print(f"  * If a firewall blocks it, run once in an admin shell:")
        print(f"    netsh advfirewall firewall add rule name=\"archive5174\" dir=in action=allow protocol=TCP localport={PORT}")
    print(f"  Stop: Ctrl+C\n")

    browse_host = ip if cli.share else "localhost"

    def open_browser():
        import time; time.sleep(1)
        webbrowser.open(f"http://{browse_host}:{PORT}")

    threading.Thread(target=open_browser, daemon=True).start()

    server = ReuseHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
