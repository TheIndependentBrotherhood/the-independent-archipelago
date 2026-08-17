#!/usr/bin/env python3
"""
Interactive Twitch ID finder for games missing a twitchId.
Queries the Twitch Helix API, shows suggestions in a local web interface,
and lets you accept, reject, or manually set each value before saving.

Usage:
    python scripts/find_missing_twitch.py
"""

import json
import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
GAMES_JSON_PATH = os.path.join(ROOT_DIR, "data", "games.json")

# ---------------------------------------------------------------------------
# Twitch credentials (same as fetch_twitch_games.py)
# ---------------------------------------------------------------------------
CLIENT_ID = "tmouo7p8oqhx6e6qa10m1wd0mhhcm3"
CLIENT_SECRET = "sc5a9y8ncq64ihe2he5uwn8mw3e307"
REFRESH_TOKEN = "9zh5zst9a9pon8uijo247tkwhbmrk4h2aof95ygh4roypfg5io"

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
# Twitch API
# ---------------------------------------------------------------------------

def get_access_token() -> str | None:
    url = "https://id.twitch.tv/oauth2/token"
    try:
        r = _requests.post(url, data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        }, timeout=10)
        r.raise_for_status()
        token = r.json().get("access_token")
        if token:
            print("[Twitch] Authenticated")
        return token
    except Exception as e:
        print(f"[Twitch] Auth failed: {e}")
        return None


def search_twitch_game(name: str, token: str) -> list[dict]:
    """Returns up to 5 Twitch game candidates for the given name."""
    headers = {"Client-ID": CLIENT_ID, "Authorization": f"Bearer {token}"}
    results = []

    # 1. Exact name
    try:
        r = _requests.get(
            "https://api.twitch.tv/helix/games",
            headers=headers,
            params={"name": name},
            timeout=8,
        )
        if r.ok:
            for g in r.json().get("data", []):
                results.append({"id": g["id"], "name": g["name"], "match": "exact"})
    except Exception:
        pass

    # 2. Search if exact returned nothing
    if not results:
        try:
            r = _requests.get(
                "https://api.twitch.tv/helix/search/categories",
                headers=headers,
                params={"query": name, "first": 5},
                timeout=8,
            )
            if r.ok:
                for g in r.json().get("data", []):
                    results.append({"id": g["id"], "name": g["name"], "match": "search"})
        except Exception:
            pass

    return results[:5]


# ---------------------------------------------------------------------------
# Build the missing list
# ---------------------------------------------------------------------------

def find_missing(games: list) -> list:
    """Returns games that have no twitchId (null or missing)."""
    return [g for g in games if not g.get("twitchId")]


def enrich_with_suggestions(missing: list, token: str | None) -> list:
    """For each missing game, query Twitch and attach candidates."""
    total = len(missing)
    enriched = []
    for i, game in enumerate(missing, 1):
        name = game["name"]
        print(f"  [{i}/{total}] {name}")
        candidates = search_twitch_game(name, token) if token else []
        enriched.append({
            "id": game["id"],
            "name": name,
            "candidates": candidates,
            # Best guess: first exact or first search result
            "best": candidates[0] if candidates else None,
        })
    return enriched


# ---------------------------------------------------------------------------
# Apply decisions
# ---------------------------------------------------------------------------

def apply_decisions(games_data: dict, decisions: list) -> dict:
    id_to_game = {g["id"]: g for g in games_data["games"]}
    for dec in decisions:
        action = dec.get("action")
        game_id = dec.get("gameId")
        game = id_to_game.get(game_id)
        if not game:
            continue
        if action == "accept" or action == "accepted":
            game["twitchId"] = dec.get("twitchId")
        elif action == "manual":
            val = dec.get("twitchId", "").strip()
            game["twitchId"] = val if val else None
        # "skip" → leave as null
    return games_data


# ---------------------------------------------------------------------------
# Embedded HTML
# ---------------------------------------------------------------------------

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archipelago — Missing Twitch IDs</title>
<style>
  :root {
    --primary: #e8a835; --bg: #121212; --card: #1e1e1e; --border: #333;
    --text: #e0e0e0; --muted: #999; --green: #4ade80; --yellow: #facc15;
    --red: #f87171; --blue: #6ba3ff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); padding: 20px; line-height: 1.5; }
  h1 { color: var(--primary); margin-bottom: 6px; }
  p.subtitle { color: var(--muted); margin-bottom: 16px; font-size: 0.9rem; }
  h2.section-header { cursor: pointer; user-select: none; display: flex; align-items: center; gap: 8px;
    color: var(--primary); font-size: 1.1rem; font-weight: bold;
    border-bottom: 1px solid var(--border); padding-bottom: 6px; margin: 20px 0 0; }
  h2.section-header:hover { color: #f0b840; }
  .collapse-icon { font-size: 0.75rem; transition: transform 0.2s; display: inline-block; }
  .collapse-icon.open { transform: rotate(90deg); }
  .section-body { margin-top: 10px; }

  .stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .stat { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 10px 18px; text-align: center; }
  .stat .n { font-size: 1.8rem; font-weight: bold; color: var(--primary); }
  .stat .l { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

  .section-toolbar { display: flex; gap: 6px; margin-bottom: 12px; }
  .btn { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
    cursor: pointer; font-size: 0.85rem; background: #2a2a2a; color: var(--text); }
  .btn:hover { background: #3a3a3a; }
  .btn.primary { background: var(--primary); color: #000; border-color: var(--primary); font-weight: bold; }
  .btn.primary:hover { background: #f0b840; }
  .btn.accept { background: #1a3a1a; border-color: var(--green); color: var(--green); }
  .btn.accept:hover { background: #1f4a1f; }
  .btn.skip { background: #2a2a2a; border-color: var(--border); color: var(--muted); }
  .btn.manual { background: #1a2a3a; border-color: var(--blue); color: var(--blue); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .game-entry { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px; margin-bottom: 10px; }
  .game-entry.accepted { border-color: var(--green); opacity: 0.7; }
  .game-entry.skipped  { border-color: var(--border); opacity: 0.4; }
  .game-entry.manual   { border-color: var(--blue); opacity: 0.7; }
  .game-name { font-weight: bold; font-size: 1rem; margin-bottom: 6px; }

  .candidates { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
  .candidate { background: #2a2a2a; border: 1px solid var(--border); border-radius: 6px;
    padding: 4px 10px; font-size: 0.8rem; cursor: pointer; }
  .candidate:hover { border-color: var(--primary); }
  .candidate.selected { border-color: var(--green); background: #1a3a1a; color: var(--green); }
  .candidate .cid { color: var(--muted); font-size: 0.72rem; margin-left: 4px; }
  .candidate .match { font-size: 0.68rem; color: var(--yellow); }
  .no-match { font-size: 0.82rem; color: var(--muted); font-style: italic; }

  .preview-img { width: 36px; height: 48px; border-radius: 4px; object-fit: cover;
    vertical-align: middle; margin-right: 6px; border: 1px solid var(--border); }

  .actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
  .status-label { font-size: 0.8rem; font-style: italic; margin-left: 6px; color: var(--muted); }

  .manual-row { display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }
  .manual-row input { background: #2a2a2a; border: 1px solid var(--border); border-radius: 6px;
    color: var(--text); padding: 5px 10px; font-size: 0.85rem; width: 160px; }
  .manual-row input:focus { outline: none; border-color: var(--primary); }

  .save-section { margin-top: 30px; padding: 20px; background: var(--card); border-radius: 10px; border: 1px solid var(--border); }
  .save-section h3 { margin-bottom: 10px; }
  .save-summary { font-size: 0.85rem; color: var(--muted); margin-bottom: 14px; }
  .save-summary span { color: var(--text); font-weight: bold; }
  .toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 20px; border-radius: 8px;
    font-size: 0.9rem; z-index: 9999; display: none; }
  .toast.success { background: #1a3a1a; border: 1px solid var(--green); color: var(--green); }
  .toast.error   { background: #3a1a1a; border: 1px solid var(--red);   color: var(--red);   }
</style>
</head>
<body>
<h1>🎮 Archipelago — Missing Twitch IDs</h1>
<p class="subtitle">Games with no <code>twitchId</code>. Suggestions are fetched from the Twitch API. Accept, skip, or set manually.</p>

<div class="stats" id="statsPanel"></div>

<div class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('listBody')">
    <span class="collapse-icon" id="listIcon">&#9658;</span>
    Games without Twitch ID <span id="listCount"></span>
  </h2>
  <div id="listBody" class="section-body" style="display:none">
    <div class="section-toolbar">
      <button class="btn accept" onclick="acceptAll()">Accept All Suggestions</button>
      <button class="btn skip"   onclick="skipAll()">Skip All</button>
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
  const iconId = bodyId.replace('Body', 'Icon');
  const icon = document.getElementById(iconId);
  if (icon) icon.classList.toggle('open', !isOpen);
}

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function twitchImg(id) {
  if (!id) return '';
  const url = `https://static-cdn.jtvnw.net/ttv-boxart/${id}-36x48.jpg`;
  return `<img class="preview-img" src="${url}" onerror="this.style.display='none'" alt="">`;
}

function renderGames() {
  const list = document.getElementById('gamesList');
  document.getElementById('listCount').textContent = `(${GAMES.length})`;

  list.innerHTML = GAMES.map((g, i) => {
    const key = `g_${i}`;
    const d = decisions[key] || { action: 'pending' };
    const cardClass = d.action === 'accepted' ? 'accepted' : d.action === 'skipped' ? 'skipped' : d.action === 'manual' ? 'manual' : '';

    const candidatesHtml = g.candidates.length
      ? g.candidates.map((c, ci) => {
          const sel = d.selectedCandidate === ci ? 'selected' : '';
          return `<span class="candidate ${sel}"
            data-ci="${ci}" data-id="${escapeHtml(c.id)}" data-name="${escapeHtml(c.name)}"
            onclick="selectCandidate('${key}', this)">
            ${twitchImg(c.id)}
            <strong>${escapeHtml(c.name)}</strong>
            <span class="cid">${escapeHtml(c.id)}</span>
            <span class="match">${c.match}</span>
          </span>`;
        }).join('')
      : '<span class="no-match">No Twitch match found — use manual input.</span>';

    return `
    <div class="game-entry ${cardClass}" id="card_${key}">
      <div class="game-name">${escapeHtml(g.name)}</div>
      <div class="candidates">${candidatesHtml}</div>
      <div class="actions">
        <button class="btn accept" onclick="acceptSelected('${key}','${g.id}')" ${!d.twitchId && !g.best ? 'disabled' : ''}>
          &#10003; Accept ${d.twitchId ? `(${d.twitchId})` : g.best ? `(${g.best.id})` : ''}
        </button>
        <button class="btn skip" onclick="decide('${key}','${g.id}','skipped',null)">&#10007; Skip</button>
        <button class="btn manual" onclick="toggleManual('${key}')">&#9998; Manual</button>
        <span class="status-label" id="status_${key}">${d.action !== 'pending' ? d.action : ''}</span>
      </div>
      <div class="manual-row" id="manual_${key}" style="display:none">
        <input type="text" id="manualInput_${key}" placeholder="Twitch ID...">
        <button class="btn manual" onclick="confirmManual('${key}','${g.id}')">Set</button>
        <button class="btn" onclick="toggleManual('${key}')">Cancel</button>
      </div>
    </div>`;
  }).join('');
}

function selectCandidate(key, el) {
  const ci = parseInt(el.dataset.ci);
  const id = el.dataset.id;
  const name = el.dataset.name;
  if (!decisions[key]) decisions[key] = { action: 'pending' };
  decisions[key].selectedCandidate = ci;
  decisions[key].twitchId = id;
  // Refresh just the candidates highlight
  const card = document.getElementById(`card_${key}`);
  card.querySelectorAll('.candidate').forEach((e, i) => e.classList.toggle('selected', i === ci));
  // Update accept button label
  const acceptBtn = card.querySelector('.btn.accept');
  if (acceptBtn) acceptBtn.textContent = `\u2713 Accept (${id})`;
  acceptBtn.disabled = false;
}

function acceptSelected(key, gameId) {
  const d = decisions[key] || {};
  // Find the game to get the best fallback
  const gameIndex = parseInt(key.replace('g_', ''));
  const g = GAMES[gameIndex];
  const twitchId = d.twitchId || (g.best ? g.best.id : null);
  if (!twitchId) return;
  decide(key, gameId, 'accepted', twitchId);
}

function decide(key, gameId, action, twitchId) {
  decisions[key] = { action, gameId, twitchId, ...(decisions[key] || {}) };
  decisions[key].action = action;
  decisions[key].gameId = gameId;
  decisions[key].twitchId = twitchId;
  const card = document.getElementById(`card_${key}`);
  card.className = `game-entry ${action === 'accepted' ? 'accepted' : action === 'skipped' ? 'skipped' : 'manual'}`;
  const status = document.getElementById(`status_${key}`);
  if (status) status.textContent = twitchId ? `${action} → ${twitchId}` : action;
  renderStats();
}

function toggleManual(key) {
  const row = document.getElementById(`manual_${key}`);
  row.style.display = row.style.display === 'none' ? 'flex' : 'none';
}

function confirmManual(key, gameId) {
  const val = document.getElementById(`manualInput_${key}`).value.trim();
  if (!val) { showToast('Enter a Twitch ID first.', 'error'); return; }
  decide(key, gameId, 'manual', val);
  toggleManual(key);
}

function acceptAll() {
  GAMES.forEach((g, i) => {
    const key = `g_${i}`;
    const twitchId = (decisions[key] && decisions[key].twitchId) || (g.best ? g.best.id : null);
    if (twitchId) decide(key, g.id, 'accepted', twitchId);
    else decide(key, g.id, 'skipped', null);
  });
  renderGames();
  renderStats();
}

function skipAll() {
  GAMES.forEach((g, i) => decide(`g_${i}`, g.id, 'skipped', null));
  renderGames();
  renderStats();
}

function renderStats() {
  const accepted = Object.values(decisions).filter(d => d.action === 'accepted' || d.action === 'manual').length;
  const skipped  = Object.values(decisions).filter(d => d.action === 'skipped').length;
  const pending  = GAMES.length - accepted - skipped;
  document.getElementById('statsPanel').innerHTML = `
    <div class="stat"><div class="n">${GAMES.length}</div><div class="l">Missing</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${accepted}</div><div class="l">Accepted</div></div>
    <div class="stat"><div class="n" style="color:var(--muted)">${skipped}</div><div class="l">Skipped</div></div>
    <div class="stat"><div class="n" style="color:var(--yellow)">${pending}</div><div class="l">Pending</div></div>`;
  document.getElementById('saveSummary').innerHTML =
    `<span>${accepted}</span> Twitch IDs will be set. <span>${skipped}</span> skipped. <span>${pending}</span> still pending.`;
}

async function saveChanges() {
  const payload = Object.values(decisions)
    .filter(d => d.action === 'accepted' || d.action === 'manual')
    .map(d => ({ action: d.action, gameId: d.gameId, twitchId: d.twitchId }));

  if (!payload.length) { showToast('No decisions to save.', 'error'); return; }

  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving...';

  try {
    const res = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) showToast(`Done! ${data.applied} Twitch IDs saved.`, 'success');
    else showToast('Error: ' + data.error, 'error');
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

// Init
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
    games_data = None
    enriched = None
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
            body = self.rfile.read(length)
            try:
                decisions = json.loads(body)
                # Re-read from disk to get latest state
                with open(self.games_json_path, "r", encoding="utf-8") as f:
                    games_data = json.load(f)
                updated = apply_decisions(games_data, decisions)
                with open(self.games_json_path, "w", encoding="utf-8") as f:
                    json.dump(updated, f, indent=2, ensure_ascii=False)
                applied = len([d for d in decisions if d.get("action") in ("accept", "accepted", "manual")])
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

    print("[JSON] Reading games.json...")
    with open(GAMES_JSON_PATH, "r", encoding="utf-8") as f:
        games_data = json.load(f)

    missing = find_missing(games_data["games"])
    print(f"       {len(missing)} games without twitchId")

    print("[Twitch] Authenticating...")
    token = get_access_token()

    print("[Twitch] Fetching suggestions...")
    enriched = enrich_with_suggestions(missing, token)

    found = sum(1 for g in enriched if g["best"])
    print(f"       {found}/{len(enriched)} games with at least one candidate")

    Handler.games_data = games_data
    Handler.enriched = enriched
    Handler.games_json_path = GAMES_JSON_PATH

    port = 8766
    server = HTTPServer(("localhost", port), Handler)

    url = f"http://localhost:{port}"
    print(f"\n[SERVER] Opening review interface at {url}")
    print("         Press Ctrl+C to stop.\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[OK] Server stopped.")


if __name__ == "__main__":
    main()
