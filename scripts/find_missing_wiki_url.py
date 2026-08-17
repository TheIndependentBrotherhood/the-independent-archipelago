#!/usr/bin/env python3
"""
Interactive wiki URL finder for games missing a 'url' field.
Queries the Archipelago Miraheze wiki API (batch, no HTTP spam) to find and
suggest canonical page URLs.  Shows results in a local web interface.

Usage:
    python scripts/find_missing_wiki_url.py
"""

import json
import os
import re
import sys
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
GAMES_JSON_PATH = os.path.join(ROOT_DIR, "data", "games.json")
WIKI_BASE = "https://archipelago.miraheze.org/wiki/"
WIKI_API  = "https://archipelago.miraheze.org/w/api.php"

# ---------------------------------------------------------------------------
# Auto-install requests if missing
# ---------------------------------------------------------------------------
try:
    import requests as _requests
except ImportError:
    import subprocess
    print("Installing requests...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests as _requests


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def find_missing_url(games: list) -> list:
    """Return games that have no 'url' (null or missing field)."""
    return [g for g in games if not g.get("url")]


def title_to_wiki_url(title: str) -> str:
    """Convert a canonical wiki page title to a miraheze URL."""
    return WIKI_BASE + urllib.parse.quote(title.replace(" ", "_"), safe="_-:()!.")


def generate_candidates(name: str) -> list:
    """
    Generate a small list of wiki page title candidates to try for a game name.
    We try the exact name first, then common fallbacks.
    """
    cands = [name]
    # Strip trailing parenthetical: "Foo (Bar)" → "Foo"
    stripped = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    if stripped and stripped != name:
        cands.append(stripped)
    # Strip subtitle after " - ": "Foo - Bar" → "Foo"
    if " - " in name:
        base = name.split(" - ")[0].strip()
        if base and base not in cands:
            cands.append(base)
    return cands


def check_wiki_pages(names: list) -> dict:
    """
    For each game name, check the Miraheze wiki API (batched, 50 titles at a time).
    Returns dict: name → {"found": bool, "url": str|None, "canonical": str|None}
    """
    results = {n: {"found": False, "url": None, "canonical": None} for n in names}

    # Build: name → ordered list of candidate page titles to check
    name_to_cands = {n: generate_candidates(n) for n in names}

    # Deduplicated flat list of all candidate titles
    seen = set()
    all_cands = []
    for cands in name_to_cands.values():
        for c in cands:
            if c not in seen:
                seen.add(c)
                all_cands.append(c)

    print(f"[Wiki] {len(all_cands)} candidate titles for {len(names)} games — querying API…")

    session = _requests.Session()
    session.headers["User-Agent"] = "ArchipelagoURLFinder/1.0 (archipelago tracker)"

    # cand_title → canonical URL (only for titles that exist)
    found: dict = {}

    for i in range(0, len(all_cands), 50):
        batch = all_cands[i : i + 50]
        idx   = i // 50 + 1
        total = (len(all_cands) - 1) // 50 + 1
        print(f"  Batch {idx}/{total}  ({len(batch)} titles)")

        try:
            r = session.get(
                WIKI_API,
                params={
                    "action":    "query",
                    "titles":    "|".join(batch),
                    "format":    "json",
                    "redirects": "1",
                },
                timeout=20,
            )
            data = r.json()
        except Exception as e:
            print(f"  [Error] {e}")
            continue

        q = data.get("query", {})

        # Build forward chain: queried_title → final resolved title
        # MediaWiki normalises underscores to spaces, fixes capitalisation, etc.
        resolution: dict = {t: t for t in batch}
        for norm in q.get("normalized", []):
            resolution[norm["from"]] = norm["to"]
        for redir in q.get("redirects", []):
            src, tgt = redir["from"], redir["to"]
            for k in resolution:
                if resolution[k] == src:
                    resolution[k] = tgt

        # pages: canonical_title → (page_id, page_dict)
        pages_by_title: dict = {}
        for pid, page in q.get("pages", {}).items():
            pages_by_title[page.get("title", "")] = (pid, page)

        for queried in batch:
            final_title = resolution.get(queried, queried)
            pid, page   = pages_by_title.get(final_title, (None, None))

            if page and "missing" not in page and pid and int(pid) > 0:
                canonical = page.get("title", final_title)
                found[queried] = (canonical, title_to_wiki_url(canonical))

    session.close()

    # Map results back: for each game, use its first candidate that was found
    for name, cands in name_to_cands.items():
        for cand in cands:
            if cand in found:
                canonical, url = found[cand]
                results[name] = {"found": True, "url": url, "canonical": canonical}
                break

    total_found = sum(1 for v in results.values() if v["found"])
    print(f"[Wiki] Found: {total_found}/{len(names)} games have a wiki page.")
    return results


# ---------------------------------------------------------------------------
# Apply decisions
# ---------------------------------------------------------------------------

def apply_decisions(games_data: dict, decisions: list) -> dict:
    id_to_game = {g["id"]: g for g in games_data["games"]}
    for dec in decisions:
        action  = dec.get("action")
        game_id = dec.get("gameId")
        game    = id_to_game.get(game_id)
        if not game:
            continue
        if action in ("accepted", "manual"):
            url = (dec.get("url") or "").strip()
            game["url"] = url if url else None
    return games_data


# ---------------------------------------------------------------------------
# Embedded HTML
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archipelago — Missing Wiki URLs</title>
<style>
  :root {
    --primary:#e8a835;--bg:#121212;--card:#1e1e1e;--border:#333;
    --text:#e0e0e0;--muted:#999;--green:#4ade80;--yellow:#facc15;
    --red:#f87171;--blue:#6ba3ff;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);padding:20px;line-height:1.5;}
  h1{color:var(--primary);margin-bottom:6px;}
  p.subtitle{color:var(--muted);margin-bottom:16px;font-size:.9rem;}
  h2.section-header{cursor:pointer;user-select:none;display:flex;align-items:center;gap:8px;
    color:var(--primary);font-size:1.1rem;font-weight:bold;
    border-bottom:1px solid var(--border);padding-bottom:6px;margin:20px 0 0;}
  h2.section-header:hover{color:#f0b840;}
  .collapse-icon{font-size:.75rem;transition:transform .2s;display:inline-block;}
  .collapse-icon.open{transform:rotate(90deg);}
  .section-body{margin-top:10px;}
  .stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;}
  .stat{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;}
  .stat .n{font-size:1.8rem;font-weight:bold;color:var(--primary);}
  .stat .l{font-size:.75rem;color:var(--muted);margin-top:2px;}
  .section-toolbar{display:flex;gap:6px;margin-bottom:12px;}
  .btn{padding:6px 14px;border-radius:6px;border:1px solid var(--border);
    cursor:pointer;font-size:.85rem;background:#2a2a2a;color:var(--text);}
  .btn:hover{background:#3a3a3a;}
  .btn.primary{background:var(--primary);color:#000;border-color:var(--primary);font-weight:bold;}
  .btn.primary:hover{background:#f0b840;}
  .btn.accept{background:#1a3a1a;border-color:var(--green);color:var(--green);}
  .btn.skip{background:#2a2a2a;border-color:var(--border);color:var(--muted);}
  .btn.manual{background:#1a2a3a;border-color:var(--blue);color:var(--blue);}
  .btn:disabled{opacity:.4;cursor:not-allowed;}
  .game-entry{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:10px;}
  .game-entry.accepted{border-color:var(--green);opacity:.7;}
  .game-entry.skipped{border-color:var(--border);opacity:.4;}
  .game-entry.manual{border-color:var(--blue);opacity:.7;}
  .game-name{font-weight:bold;font-size:1rem;margin-bottom:4px;}
  .game-platform{font-size:.75rem;color:var(--muted);margin-bottom:6px;}
  .suggestion{font-size:.82rem;margin-bottom:8px;display:flex;align-items:center;gap:8px;}
  .suggestion a{color:var(--primary);word-break:break-all;}
  .badge-found{background:#1a3a1a;border:1px solid var(--green);color:var(--green);
    border-radius:4px;padding:1px 6px;font-size:.7rem;font-weight:bold;white-space:nowrap;}
  .badge-notfound{background:#3a1a1a;border:1px solid var(--red);color:var(--red);
    border-radius:4px;padding:1px 6px;font-size:.7rem;font-weight:bold;white-space:nowrap;}
  .actions{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .status-label{font-size:.8rem;font-style:italic;margin-left:6px;color:var(--muted);}
  .manual-row{display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap;}
  .manual-row input{background:#2a2a2a;border:1px solid var(--border);border-radius:6px;
    color:var(--text);padding:5px 10px;font-size:.85rem;flex:1;min-width:260px;}
  .manual-row input:focus{outline:none;border-color:var(--primary);}
  .save-section{margin-top:30px;padding:20px;background:var(--card);border-radius:10px;border:1px solid var(--border);}
  .save-section h3{margin-bottom:10px;}
  .save-summary{font-size:.85rem;color:var(--muted);margin-bottom:14px;}
  .save-summary span{color:var(--text);font-weight:bold;}
  .toast{position:fixed;bottom:20px;right:20px;padding:12px 20px;border-radius:8px;font-size:.9rem;z-index:9999;display:none;}
  .toast.success{background:#1a3a1a;border:1px solid var(--green);color:var(--green);}
  .toast.error{background:#3a1a1a;border:1px solid var(--red);color:var(--red);}
</style>
</head>
<body>
<h1>&#127760; Archipelago — Missing Wiki URLs</h1>
<p class="subtitle">
  Games with no <code>url</code> field. Suggestions are verified against the
  <a href="https://archipelago.miraheze.org/wiki/" target="_blank" style="color:var(--primary)">Archipelago wiki</a>
  via the MediaWiki API (no 404 guessing).
</p>

<div class="stats" id="statsPanel"></div>

<div class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('listBody')">
    <span class="collapse-icon" id="listIcon">&#9658;</span>
    Games without Wiki URL <span id="listCount"></span>
  </h2>
  <div id="listBody" class="section-body" style="display:none">
    <div class="section-toolbar">
      <button class="btn accept" onclick="acceptAll()">&#10003; Accept All Found</button>
      <button class="btn skip"   onclick="skipAll()">&#10007; Skip All</button>
    </div>
    <div id="gamesList"></div>
  </div>
</div>

<div class="save-section">
  <h3>&#128190; Save Changes</h3>
  <div class="save-summary" id="saveSummary">—</div>
  <button class="btn primary" id="saveBtn" onclick="saveChanges()">Apply & Save to games.json</button>
</div>

<div class="toast" id="toast"></div>

<script>
const GAMES = __GAMES_JSON__;
const decisions = {};

function toggleSection(bodyId) {
  const body = document.getElementById(bodyId);
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : 'block';
  const icon = document.getElementById(bodyId.replace('Body','Icon'));
  if (icon) icon.classList.toggle('open', !isOpen);
}

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderGames() {
  const list = document.getElementById('gamesList');
  document.getElementById('listCount').textContent = `(${GAMES.length})`;

  list.innerHTML = GAMES.map((g, i) => {
    const key = `g_${i}`;
    const d = decisions[key] || { action: 'pending' };
    const cardClass = d.action === 'accepted' ? 'accepted'
                    : d.action === 'skipped'  ? 'skipped'
                    : d.action === 'manual' ? 'manual' : '';

    let suggHtml;
    if (g.found) {
      suggHtml = `
        <div class="suggestion">
          <span class="badge-found">&#10003; Wiki page found</span>
          <a href="${escapeHtml(g.url)}" target="_blank">${escapeHtml(g.url)}</a>
        </div>`;
    } else {
      suggHtml = `
        <div class="suggestion">
          <span class="badge-notfound">&#10007; Not on wiki</span>
          <span style="color:var(--muted);font-size:.8rem">Enter URL manually if needed.</span>
        </div>`;
    }

    const acceptDisabled = !g.found ? 'disabled' : '';

    return `
    <div class="game-entry ${cardClass}" id="card_${key}">
      <div class="game-name">${escapeHtml(g.name)}</div>
      <div class="game-platform">${escapeHtml(g.platform || '—')}</div>
      ${suggHtml}
      <div class="actions">
        <button class="btn accept" ${acceptDisabled}
          onclick="acceptGame('${key}','${g.gameId}',${JSON.stringify(g.url)})">
          &#10003; Accept
        </button>
        <button class="btn skip" onclick="decide('${key}','${g.gameId}','skipped',null)">
          &#10007; Skip
        </button>
        <button class="btn manual" onclick="toggleManual('${key}')">&#9998; Manual</button>
        <span class="status-label" id="status_${key}">${d.action !== 'pending' ? d.action : ''}</span>
      </div>
      <div class="manual-row" id="manual_${key}" style="display:none">
        <input type="text" id="manualInput_${key}"
          placeholder="https://archipelago.miraheze.org/wiki/..."
          value="${escapeHtml(g.url || '')}">
        <button class="btn manual" onclick="confirmManual('${key}','${g.gameId}')">Set</button>
        <button class="btn" onclick="toggleManual('${key}')">Cancel</button>
      </div>
    </div>`;
  }).join('');
}

function acceptGame(key, gameId, url) {
  if (!url) return;
  decide(key, gameId, 'accepted', url);
}

function decide(key, gameId, action, url) {
  decisions[key] = { action, gameId, url };
  const card = document.getElementById(`card_${key}`);
  card.className = 'game-entry ' + (
    action === 'accepted' ? 'accepted' :
    action === 'skipped'  ? 'skipped'  : 'manual'
  );
  const status = document.getElementById(`status_${key}`);
  if (status) status.textContent = url ? `${action} \u2192 ${url.slice(0,60)}${url.length>60?'\u2026':''}` : action;
  renderStats();
}

function toggleManual(key) {
  const row = document.getElementById(`manual_${key}`);
  row.style.display = row.style.display === 'none' ? 'flex' : 'none';
}

function confirmManual(key, gameId) {
  const val = document.getElementById(`manualInput_${key}`).value.trim();
  if (!val) { showToast('Enter a URL first.', 'error'); return; }
  decide(key, gameId, 'manual', val);
  toggleManual(key);
}

function acceptAll() {
  GAMES.forEach((g, i) => {
    const key = `g_${i}`;
    if (g.found) decide(key, g.gameId, 'accepted', g.url);
    else         decide(key, g.gameId, 'skipped', null);
  });
  renderGames();
  renderStats();
}

function skipAll() {
  GAMES.forEach((g, i) => decide(`g_${i}`, g.gameId, 'skipped', null));
  renderGames();
  renderStats();
}

function renderStats() {
  const accepted = Object.values(decisions).filter(d => d.action === 'accepted' || d.action === 'manual').length;
  const skipped  = Object.values(decisions).filter(d => d.action === 'skipped').length;
  const pending  = GAMES.length - accepted - skipped;
  const found    = GAMES.filter(g => g.found).length;
  document.getElementById('statsPanel').innerHTML = `
    <div class="stat"><div class="n">${GAMES.length}</div><div class="l">Missing URL</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${found}</div><div class="l">Wiki page found</div></div>
    <div class="stat"><div class="n" style="color:var(--red)">${GAMES.length - found}</div><div class="l">Not on wiki</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${accepted}</div><div class="l">Accepted</div></div>
    <div class="stat"><div class="n" style="color:var(--muted)">${skipped}</div><div class="l">Skipped</div></div>
    <div class="stat"><div class="n" style="color:var(--yellow)">${pending}</div><div class="l">Pending</div></div>`;
  document.getElementById('saveSummary').innerHTML =
    `<span>${accepted}</span> URLs will be set. <span>${skipped}</span> skipped. <span>${pending}</span> still pending.`;
}

async function saveChanges() {
  const payload = Object.values(decisions)
    .filter(d => d.action === 'accepted' || d.action === 'manual')
    .map(d => ({ action: d.action, gameId: d.gameId, url: d.url }));
  if (!payload.length) { showToast('No decisions to save.', 'error'); return; }
  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving…';
  try {
    const res = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) showToast(`Done! ${data.applied} URLs saved.`, 'success');
    else         showToast('Error: ' + data.error, 'error');
  } catch (e) {
    showToast('Network error: ' + e.message, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Apply & Save to games.json';
  }
}

function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.className = `toast ${type}`; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

renderGames();
renderStats();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    enriched        = None
    games_json_path = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = HTML.replace(
                "__GAMES_JSON__",
                json.dumps(self.enriched, ensure_ascii=False)
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            try:
                decisions = json.loads(body)
                with open(self.games_json_path, "r", encoding="utf-8") as f:
                    games_data = json.load(f)
                updated = apply_decisions(games_data, decisions)
                with open(self.games_json_path, "w", encoding="utf-8") as f:
                    json.dump(updated, f, indent=2, ensure_ascii=False)
                applied = len([d for d in decisions if d["action"] in ("accept", "accepted", "manual")])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "applied": applied}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if not os.path.isfile(GAMES_JSON_PATH):
        print(f"[ERROR] games.json not found: {GAMES_JSON_PATH}")
        sys.exit(1)

    print("[JSON] Reading games.json…")
    with open(GAMES_JSON_PATH, "r", encoding="utf-8") as f:
        games_data = json.load(f)

    missing = find_missing_url(games_data["games"])
    print(f"       {len(missing)} games without url")

    # Check wiki pages via API
    names     = [g["name"] for g in missing]
    wiki_info = check_wiki_pages(names)

    # Build enriched list for the UI
    enriched = []
    for g in missing:
        info = wiki_info.get(g["name"], {"found": False, "url": None})
        enriched.append({
            "gameId":   g["id"],
            "name":     g["name"],
            "platform": g.get("platform", ""),
            "found":    info["found"],
            "url":      info["url"],
        })

    # Sort: found first, then alphabetical
    enriched.sort(key=lambda x: (not x["found"], x["name"].lower()))

    Handler.enriched        = enriched
    Handler.games_json_path = GAMES_JSON_PATH

    port   = 8767
    server = HTTPServer(("localhost", port), Handler)
    url    = f"http://localhost:{port}"
    print(f"\n[SERVER] Opening review interface at {url}")
    print("         Press Ctrl+C to stop.\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Server stopped.")


if __name__ == "__main__":
    main()
