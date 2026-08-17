#!/usr/bin/env python3
"""
Interactive platform finder for games missing 'stability' or URL fields.

Usage:
    python scripts/find_missing_stability_urls.py
"""

import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
GAMES_JSON_PATH = os.path.join(ROOT_DIR, "data", "games.json")

# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def find_missing_stability(games):
    """Return games that have no 'stability' (null, empty, or missing field)."""
    return [g for g in games if not g.get("stability")]

def find_missing_urls(games):
    """Return games missing ALL of url, githubUrl, and discordUrl."""
    return [
        g for g in games 
        if not (g.get("url") or g.get("githubUrl") or g.get("discordUrl"))
    ]

# ---------------------------------------------------------------------------
# Apply decisions
# ---------------------------------------------------------------------------

def apply_decisions(games_data, decisions):
    id_to_game = {g["id"]: g for g in games_data["games"]}
    for dec in decisions:
        game_id = dec.get("gameId")
        updates = dec.get("updates", {})
        game    = id_to_game.get(game_id)
        
        if not game:
            continue
            
        for key, value in updates.items():
            if value: # Only apply if a value was provided
                game[key] = value.strip()
                
    return games_data


# ---------------------------------------------------------------------------
# Embedded HTML
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archipelago — Missing Data</title>
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
    border-bottom:1px solid var(--border);padding-bottom:6px;margin:30px 0 10px;}
  h2.section-header:hover{color:#f0b840;}
  .collapse-icon{font-size:.75rem;transition:transform .2s;display:inline-block;}
  .collapse-icon.open{transform:rotate(90deg);}
  .section-body{margin-top:10px;}
  .stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;}
  .stat{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:10px 18px;text-align:center;}
  .stat .n{font-size:1.8rem;font-weight:bold;color:var(--primary);}
  .stat .l{font-size:.75rem;color:var(--muted);margin-top:2px;}
  .btn{padding:6px 14px;border-radius:6px;border:1px solid var(--border);
    cursor:pointer;font-size:.85rem;background:#2a2a2a;color:var(--text);}
  .btn:hover{background:#3a3a3a;}
  .btn.primary{background:var(--primary);color:#000;border-color:var(--primary);font-weight:bold;}
  .btn.primary:hover{background:#f0b840;}
  .btn.accept{background:#1a3a1a;border-color:var(--green);color:var(--green);}
  .btn.warning{background:#3a2a1a;border-color:var(--yellow);color:var(--yellow);}
  .btn.danger{background:#3a1a1a;border-color:var(--red);color:var(--red);}
  .btn:disabled{opacity:.4;cursor:not-allowed;}
  .game-entry{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:10px; transition: opacity 0.2s;}
  .game-entry.resolved{border-color:var(--green);opacity:.6;}
  .game-name{font-weight:bold;font-size:1.1rem;margin-bottom:8px;}
  .actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:10px;}
  .input-group{display:flex;flex-direction:column;gap:6px;margin-top:10px;}
  .input-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
  .input-row label{width:80px;font-size:.85rem;color:var(--muted);}
  .input-row input{background:#2a2a2a;border:1px solid var(--border);border-radius:6px;
    color:var(--text);padding:6px 10px;font-size:.85rem;flex:1;min-width:250px;}
  .input-row input:focus{outline:none;border-color:var(--primary);}
  .save-section{position:sticky;bottom:0;margin-top:30px;padding:15px 20px;background:#1e1e1ebf;backdrop-filter:blur(10px);border-radius:10px 10px 0 0;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;}
  .toast{position:fixed;bottom:80px;right:20px;padding:12px 20px;border-radius:8px;font-size:.9rem;z-index:9999;display:none;}
  .toast.success{background:#1a3a1a;border:1px solid var(--green);color:var(--green);}
  .toast.error{background:#3a1a1a;border:1px solid var(--red);color:var(--red);}
</style>
</head>
<body>
<h1>&#128203; Archipelago — Missing Data Recap</h1>
<p class="subtitle">Review and update games missing their <code>stability</code> attribute or URL links.</p>

<div class="stats">
  <div class="stat"><div class="n" id="countStability">0</div><div class="l">Missing Stability</div></div>
  <div class="stat"><div class="n" id="countUrls">0</div><div class="l">Missing ALL URLs</div></div>
  <div class="stat"><div class="n" style="color:var(--green)" id="countResolved">0</div><div class="l">Changes Pending Save</div></div>
</div>

<!-- SECTION: STABILITY -->
<div class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('stabilityBody')">
    <span class="collapse-icon open" id="stabilityIcon">&#9658;</span>
    Missing Stability
  </h2>
  <div id="stabilityBody" class="section-body">
    <div id="stabilityList"></div>
  </div>
</div>

<!-- SECTION: URLS -->
<div class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('urlsBody')">
    <span class="collapse-icon open" id="urlsIcon">&#9658;</span>
    Missing URLs (Wiki, GitHub, Discord)
  </h2>
  <div id="urlsBody" class="section-body">
    <div id="urlsList"></div>
  </div>
</div>

<div class="save-section">
  <div id="saveSummary" style="color:var(--muted);font-size:0.9rem;">No changes made yet.</div>
  <button class="btn primary" id="saveBtn" onclick="saveChanges()">Apply & Save to games.json</button>
</div>

<div class="toast" id="toast"></div>

<script>
const GAMES_STABILITY = __STABILITY_JSON__;
const GAMES_URLS = __URLS_JSON__;
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

function updateCounts() {
  document.getElementById('countStability').textContent = GAMES_STABILITY.length;
  document.getElementById('countUrls').textContent = GAMES_URLS.length;
  const pendingCount = Object.keys(decisions).length;
  document.getElementById('countResolved').textContent = pendingCount;
  document.getElementById('saveSummary').textContent = pendingCount > 0 
    ? `${pendingCount} modifications ready to be saved.` 
    : "No changes made yet.";
}

function setStability(gameId, value, btnElement) {
  if (!decisions[gameId]) decisions[gameId] = { gameId, updates: {} };
  decisions[gameId].updates.stability = value;
  
  const card = document.getElementById(`stab_card_${gameId}`);
  card.classList.add('resolved');
  
  const buttons = card.querySelectorAll('button');
  buttons.forEach(b => {
    b.style.opacity = '0.4';
    b.style.border = '1px solid var(--border)';
  });
  btnElement.style.opacity = '1';
  btnElement.style.border = '1px solid var(--green)';
  
  updateCounts();
}

function setUrls(gameId) {
  const url = document.getElementById(`url_${gameId}`).value;
  const github = document.getElementById(`github_${gameId}`).value;
  const discord = document.getElementById(`discord_${gameId}`).value;
  
  if (!url && !github && !discord) return;

  if (!decisions[gameId]) decisions[gameId] = { gameId, updates: {} };
  if (url) decisions[gameId].updates.url = url;
  if (github) decisions[gameId].updates.githubUrl = github;
  if (discord) decisions[gameId].updates.discordUrl = discord;

  const card = document.getElementById(`urls_card_${gameId}`);
  card.classList.add('resolved');
  updateCounts();
  showToast('URLs temporarily saved!', 'success');
}

function renderStability() {
  const list = document.getElementById('stabilityList');
  if (GAMES_STABILITY.length === 0) {
    list.innerHTML = '<p style="color:var(--green)">All games have a stability attribute!</p>';
    return;
  }
  
  list.innerHTML = GAMES_STABILITY.map(g => `
    <div class="game-entry" id="stab_card_${g.id}">
      <div class="game-name">${escapeHtml(g.name)} <span style="font-size:0.7rem;color:var(--muted);font-weight:normal">(${g.id})</span></div>
      <div class="actions">
        <button class="btn accept" onclick="setStability('${g.id}', 'Stable', this)">&#10003; Set Stable</button>
        <button class="btn warning" onclick="setStability('${g.id}', 'Unstable', this)">&#9888; Set Unstable</button>
        <button class="btn danger" onclick="setStability('${g.id}', 'Broken', this)">&#10060; Set Broken</button>
      </div>
    </div>
  `).join('');
}

function renderUrls() {
  const list = document.getElementById('urlsList');
  if (GAMES_URLS.length === 0) {
    list.innerHTML = '<p style="color:var(--green)">All games have at least one URL!</p>';
    return;
  }
  
  list.innerHTML = GAMES_URLS.map(g => `
    <div class="game-entry" id="urls_card_${g.id}">
      <div class="game-name">${escapeHtml(g.name)} <span style="font-size:0.7rem;color:var(--muted);font-weight:normal">(${g.id})</span></div>
      <div class="input-group">
        <div class="input-row">
          <label>Wiki URL</label>
          <input type="text" id="url_${g.id}" placeholder="https://archipelago.miraheze.org/wiki/..." value="${escapeHtml(g.url || '')}">
        </div>
        <div class="input-row">
          <label>GitHub</label>
          <input type="text" id="github_${g.id}" placeholder="https://github.com/..." value="${escapeHtml(g.githubUrl || '')}">
        </div>
        <div class="input-row">
          <label>Discord</label>
          <input type="text" id="discord_${g.id}" placeholder="Discord invite link" value="${escapeHtml(g.discordUrl || '')}">
        </div>
      </div>
      <div class="actions">
        <button class="btn" style="background:#2a3a5a; border-color:var(--blue); color:var(--blue);" onclick="setUrls('${g.id}')">Save URLs for ${escapeHtml(g.name)}</button>
      </div>
    </div>
  `).join('');
}

async function saveChanges() {
  const payload = Object.values(decisions);
  if (!payload.length) { showToast('No changes to save.', 'error'); return; }
  
  const btn = document.getElementById('saveBtn');
  btn.disabled = true; btn.textContent = 'Saving…';
  
  try {
    const res = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`Done! Modifications saved. Restart script to see changes.`, 'success');
      setTimeout(() => location.reload(), 2000); // Reload to reflect changes
    } else {
      showToast('Error: ' + data.error, 'error');
    }
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

renderStability();
renderUrls();
updateCounts();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    stability_data = None
    urls_data = None
    games_json_path = None

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            page = HTML.replace(
                "__STABILITY_JSON__", json.dumps(self.stability_data, ensure_ascii=False)
            ).replace(
                "__URLS_JSON__", json.dumps(self.urls_data, ensure_ascii=False)
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
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
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

    # 1. Missing Stability
    missing_stability = find_missing_stability(games_data["games"])
    print(f"       {len(missing_stability)} games without stability")

    # 2. Missing URLs
    missing_urls = find_missing_urls(games_data["games"])
    print(f"       {len(missing_urls)} games without any URLs")

    if not missing_stability and not missing_urls:
        print("[OK] All games have stability and at least one URL. Nothing to do.")
        sys.exit(0)

    # Simplify data for the front-end to reduce payload size
    def extract_essential(g):
        return {
            "id": g["id"], 
            "name": g["name"],
            "url": g.get("url", ""),
            "githubUrl": g.get("githubUrl", ""),
            "discordUrl": g.get("discordUrl", "")
        }

    Handler.stability_data = [extract_essential(g) for g in missing_stability]
    Handler.urls_data = [extract_essential(g) for g in missing_urls]
    Handler.games_json_path = GAMES_JSON_PATH

    port   = 8769
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