#!/usr/bin/env python3
"""
Interactive platform finder for games missing a 'platform' field.
Scrapes the Archipelago Miraheze wiki page (when a wiki url is available)
to extract the platform listed in the game's portable infobox.

Usage:
    python scripts/find_missing_platform.py
"""

import html as _html_mod
import json
import os
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
GAMES_JSON_PATH = os.path.join(ROOT_DIR, "data", "games.json")
WIKI_BASE = "https://archipelago.miraheze.org/wiki/"

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

def find_missing_platform(games):
    """Return games that have no 'platform' (null, empty, or missing field)."""
    return [g for g in games if not g.get("platform")]


def extract_platform_from_html(page_html):
    """
    Parse the Miraheze wiki portable infobox to extract the Platform value.

    Infobox HTML shape:
        <div ... data-source="platform">
          <h3>Platform</h3>
          <div class="pi-data-value pi-font">
            <a href="...">PC</a>
          </div>
        </div>
    """
    # Grab the content of the pi-data-value div inside data-source="platform"
    m = re.search(
        r'data-source=["\']platform["\'][^>]*>.*?<div[^>]*pi-data-value[^>]*>(.*?)</div>',
        page_html,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return None

    inner = m.group(1)

    # Strip all HTML tags — keeps text nodes from multiple <a> / <br/> etc.
    text = re.sub(r"<[^>]+>", " ", inner)
    text = _html_mod.unescape(text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize common separators (comma, slash, newline) → ", "
    text = re.sub(r"\s*[,/]\s*", ", ", text)
    text = re.sub(r",\s*,", ",", text).strip(", ")

    return text if text else None


def scrape_platforms(games):
    """
    For each game that has a Miraheze wiki URL, fetch the page and extract
    the platform from the infobox.

    Returns dict: game_id → {"found": bool, "platform": str|None, "wiki_url": str|None}
    """
    results = {}
    session = _requests.Session()
    session.headers["User-Agent"] = "ArchipelagoPlatformFinder/1.0"

    wiki_games   = [g for g in games if (g.get("url") or "").startswith(WIKI_BASE)]
    no_url_games = [g for g in games if not (g.get("url") or "").startswith(WIKI_BASE)]

    for g in no_url_games:
        results[g["id"]] = {"found": False, "platform": None, "wiki_url": None}

    total = len(wiki_games)
    print(f"[Wiki] {len(no_url_games)} games have no wiki URL — skipping scrape.")
    print(f"[Wiki] Scraping {total} wiki pages for platform info…")

    for i, g in enumerate(wiki_games):
        wiki_url = g["url"]
        print(f"  [{i+1}/{total}] {g['name']}")
        try:
            r = session.get(wiki_url, timeout=15)
            if r.status_code == 200:
                platform = extract_platform_from_html(r.text)
                results[g["id"]] = {
                    "found":    bool(platform),
                    "platform": platform,
                    "wiki_url": wiki_url,
                }
            else:
                print(f"    [HTTP {r.status_code}]")
                results[g["id"]] = {"found": False, "platform": None, "wiki_url": wiki_url}
        except Exception as e:
            print(f"    [Error] {e}")
            results[g["id"]] = {"found": False, "platform": None, "wiki_url": wiki_url}

        if i < total - 1:
            time.sleep(0.25)  # be polite to the wiki

    session.close()

    found_count = sum(1 for v in results.values() if v["found"])
    print(f"[Wiki] Platform found for {found_count}/{len(games)} games.")
    return results


# ---------------------------------------------------------------------------
# Apply decisions
# ---------------------------------------------------------------------------

def apply_decisions(games_data, decisions):
    id_to_game = {g["id"]: g for g in games_data["games"]}
    for dec in decisions:
        action  = dec.get("action")
        game_id = dec.get("gameId")
        game    = id_to_game.get(game_id)
        if not game:
            continue
        if action in ("accepted", "manual"):
            value = (dec.get("platform") or "").strip()
            game["platform"] = value if value else None
    return games_data


# ---------------------------------------------------------------------------
# Embedded HTML
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archipelago — Missing Platforms</title>
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
  .game-name{font-weight:bold;font-size:1rem;margin-bottom:2px;}
  .game-meta{font-size:.75rem;color:var(--muted);margin-bottom:6px;display:flex;gap:12px;flex-wrap:wrap;align-items:center;}
  .game-meta a{color:var(--muted);text-decoration:none;}
  .game-meta a:hover{color:var(--primary);}
  .suggestion{font-size:.82rem;margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
  .platform-chip{background:#2a2a2a;border:1px solid var(--primary);border-radius:20px;
    padding:2px 12px;font-size:.82rem;color:var(--primary);font-weight:bold;}
  .badge-found{background:#1a3a1a;border:1px solid var(--green);color:var(--green);
    border-radius:4px;padding:1px 6px;font-size:.7rem;font-weight:bold;white-space:nowrap;}
  .badge-nourl{background:#3a2a1a;border:1px solid var(--yellow);color:var(--yellow);
    border-radius:4px;padding:1px 6px;font-size:.7rem;font-weight:bold;white-space:nowrap;}
  .badge-notfound{background:#3a1a1a;border:1px solid var(--red);color:var(--red);
    border-radius:4px;padding:1px 6px;font-size:.7rem;font-weight:bold;white-space:nowrap;}
  .actions{display:flex;gap:6px;align-items:center;flex-wrap:wrap;}
  .status-label{font-size:.8rem;font-style:italic;margin-left:6px;color:var(--muted);}
  .manual-row{display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap;}
  .manual-row input{background:#2a2a2a;border:1px solid var(--border);border-radius:6px;
    color:var(--text);padding:5px 10px;font-size:.85rem;flex:1;min-width:200px;}
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
<h1>&#127918; Archipelago — Missing Platforms</h1>
<p class="subtitle">
  Games with no <code>platform</code> field. Suggestions are scraped directly
  from each game's
  <a href="https://archipelago.miraheze.org/wiki/" target="_blank" style="color:var(--primary)">Archipelago wiki</a>
  infobox.
</p>

<div class="stats" id="statsPanel"></div>

<div class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('listBody')">
    <span class="collapse-icon" id="listIcon">&#9658;</span>
    Games without Platform <span id="listCount"></span>
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
  const icon = document.getElementById(bodyId.replace('Body', 'Icon'));
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
    const key     = `g_${i}`;
    const d       = decisions[key] || { action: 'pending' };
    const cardCls = d.action === 'accepted' ? 'accepted'
                  : d.action === 'skipped'  ? 'skipped'
                  : d.action === 'manual'   ? 'manual' : '';

    let suggHtml;
    if (g.found) {
      suggHtml = `
        <div class="suggestion">
          <span class="badge-found">&#10003; Infobox found</span>
          <span class="platform-chip">${escapeHtml(g.platform)}</span>
          ${g.wiki_url ? `<a href="${escapeHtml(g.wiki_url)}" target="_blank" style="color:var(--muted);font-size:.75rem">&#128279; wiki</a>` : ''}
        </div>`;
    } else if (!g.wiki_url) {
      suggHtml = `
        <div class="suggestion">
          <span class="badge-nourl">&#9888; No wiki URL</span>
          <span style="color:var(--muted);font-size:.8rem">Set platform manually.</span>
        </div>`;
    } else {
      suggHtml = `
        <div class="suggestion">
          <span class="badge-notfound">&#10007; Not in infobox</span>
          <a href="${escapeHtml(g.wiki_url)}" target="_blank" style="color:var(--muted);font-size:.75rem">&#128279; wiki</a>
          <span style="color:var(--muted);font-size:.8rem">Platform field missing in infobox.</span>
        </div>`;
    }

    const acceptDisabled = !g.found ? 'disabled' : '';
    const defaultInput   = g.found ? escapeHtml(g.platform) : '';

    return `
    <div class="game-entry ${cardCls}" id="card_${key}">
      <div class="game-name">${escapeHtml(g.name)}</div>
      <div class="game-meta">
        ${g.url ? `<a href="${escapeHtml(g.url)}" target="_blank">&#127760; ${escapeHtml(g.url.replace('https://',''))}</a>` : '<span>no url</span>'}
      </div>
      ${suggHtml}
      <div class="actions">
        <button class="btn accept" ${acceptDisabled}
          data-key="${key}" data-id="${g.gameId}" data-platform="${escapeHtml(g.platform || '')}"
          onmousedown="acceptGame(this)">
          &#10003; Accept
        </button>
        <button class="btn skip"
          data-key="${key}" data-id="${g.gameId}"
          onmousedown="skipGame(this)">
          &#10007; Skip
        </button>
        <button class="btn manual"
          data-key="${key}"
          onmousedown="toggleManual(this.dataset.key)">
          &#9998; Manual
        </button>
        <span class="status-label" id="status_${key}">${d.action !== 'pending' ? d.action : ''}</span>
      </div>
      <div class="manual-row" id="manual_${key}" style="display:none">
        <input type="text" id="manualInput_${key}"
          placeholder="PC, Mac, …"
          value="${defaultInput}">
        <button class="btn manual"
          data-key="${key}" data-id="${g.gameId}"
          onmousedown="confirmManual(this.dataset.key, this.dataset.id)">Set</button>
        <button class="btn" data-key="${key}" onmousedown="toggleManual(this.dataset.key)">Cancel</button>
      </div>
    </div>`;
  }).join('');
}

function acceptGame(btn) {
  const key      = btn.dataset.key;
  const gameId   = btn.dataset.id;
  const platform = btn.dataset.platform;
  if (!platform) return;
  decide(key, gameId, 'accepted', platform);
}

function skipGame(btn) {
  decide(btn.dataset.key, btn.dataset.id, 'skipped', null);
}

function decide(key, gameId, action, platform) {
  decisions[key] = { action, gameId, platform };
  const card = document.getElementById(`card_${key}`);
  card.className = 'game-entry ' + (
    action === 'accepted' ? 'accepted' :
    action === 'skipped'  ? 'skipped'  : 'manual'
  );
  const status = document.getElementById(`status_${key}`);
  if (status) status.textContent = platform ? `${action} → ${platform}` : action;
  renderStats();
}

function toggleManual(key) {
  const row = document.getElementById(`manual_${key}`);
  row.style.display = row.style.display === 'none' ? 'flex' : 'none';
  if (row.style.display === 'flex') {
    const input = document.getElementById(`manualInput_${key}`);
    if (input) setTimeout(() => input.focus(), 0);
  }
}

function confirmManual(key, gameId) {
  const val = (document.getElementById(`manualInput_${key}`).value || '').trim();
  if (!val) { showToast('Saisir une valeur de platform.', 'error'); return; }
  decide(key, gameId, 'manual', val);
  toggleManual(key);
}

function acceptAll() {
  GAMES.forEach((g, i) => {
    const key = `g_${i}`;
    if (g.found) decide(key, g.gameId, 'accepted', g.platform);
    else         decide(key, g.gameId, 'skipped',  null);
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
  const noUrl    = GAMES.filter(g => !g.wiki_url).length;

  document.getElementById('statsPanel').innerHTML = `
    <div class="stat"><div class="n">${GAMES.length}</div><div class="l">Missing Platform</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${found}</div><div class="l">Wiki infobox found</div></div>
    <div class="stat"><div class="n" style="color:var(--yellow)">${noUrl}</div><div class="l">No wiki URL</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${accepted}</div><div class="l">Accepted</div></div>
    <div class="stat"><div class="n" style="color:var(--muted)">${skipped}</div><div class="l">Skipped</div></div>
    <div class="stat"><div class="n" style="color:var(--yellow)">${pending}</div><div class="l">Pending</div></div>`;

  document.getElementById('saveSummary').innerHTML =
    `<span>${accepted}</span> platforms will be set. <span>${skipped}</span> skipped. <span>${pending}</span> still pending.`;
}

async function saveChanges() {
  const payload = Object.values(decisions)
    .filter(d => d.action === 'accepted' || d.action === 'manual')
    .map(d => ({ action: d.action, gameId: d.gameId, platform: d.platform }));
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
    if (data.ok) showToast(`Done! ${data.applied} platforms saved.`, 'success');
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
            page = HTML.replace(
                "__GAMES_JSON__",
                json.dumps(self.enriched, ensure_ascii=False),
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
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
                applied = len([
                    d for d in decisions
                    if d.get("action") in ("accepted", "manual")
                ])
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

    missing = find_missing_platform(games_data["games"])
    print(f"       {len(missing)} games without platform")

    if not missing:
        print("[OK] No games with missing platform. Nothing to do.")
        sys.exit(0)

    # Scrape wiki pages for platform info
    scrape_info = scrape_platforms(missing)

    # Build enriched list for the UI
    enriched = []
    for g in missing:
        info = scrape_info.get(g["id"], {"found": False, "platform": None, "wiki_url": None})
        enriched.append({
            "gameId":   g["id"],
            "name":     g["name"],
            "url":      g.get("url", ""),
            "found":    info["found"],
            "platform": info["platform"],
            "wiki_url": info["wiki_url"],
        })

    # Sort: found first, then no-url, then not-found — all alphabetical within groups
    def sort_key(x):
        if x["found"]:          return (0, x["name"].lower())
        if not x["wiki_url"]:   return (2, x["name"].lower())
        return                         (1, x["name"].lower())

    enriched.sort(key=sort_key)

    Handler.enriched        = enriched
    Handler.games_json_path = GAMES_JSON_PATH

    port   = 8768
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
