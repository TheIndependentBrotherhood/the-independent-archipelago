#!/usr/bin/env python3
"""
Interactive XLSX to JSON merger for Archipelago games.
Compares the XLSX file with games.json and provides a local web interface
to review, validate, reject, or map detected changes.

Usage:
    python scripts/merge_xlsx.py
    python scripts/merge_xlsx.py path/to/file.xlsx

Features:
    - Detects new games (in XLSX, not in JSON)
    - Detects updates: new stability info, new setup guide URLs
    - Interactive UI: Accept / Skip / Map to existing game
    - Adds stability field (Stable / Unstable / Broken)
    - Adds setupGuideUrl field for non-Github/Discord/Wiki links
    - Reports unknown link types for manual review
"""

import json
import os
import re
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
GAMES_JSON_PATH = os.path.join(ROOT_DIR, "data", "games.json")
XLSX_DEFAULT_DIR = os.path.join(ROOT_DIR, "data", "Google Sheet")

# ---------------------------------------------------------------------------
# Auto-install openpyxl if missing
# ---------------------------------------------------------------------------
try:
    import openpyxl
except ImportError:
    import subprocess
    print("Installing openpyxl...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
    import openpyxl


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Create a URL-safe slug from a game name."""
    slug = name.lower()
    slug = re.sub(r"['''\u2019\u2018]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def normalize(name: str) -> str:
    """Normalize a game name for fuzzy matching."""
    if not name:
        return ""
    n = name.lower()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return re.sub(r"\s+", " ", n).strip()


def classify_link(url: str) -> str:
    """Return the JSON field name a setup guide URL maps to."""
    if not url:
        return None
    if "discord.com" in url:
        return "discordUrl"
    if "archipelago.miraheze.org/wiki" in url or "archipelago.gg" in url:
        return "url"
    # github.com, github.io, gitlab.com, git.*.* domains → githubUrl
    from urllib.parse import urlparse as _up
    domain = _up(url).netloc.lower()
    if (
        "github.com" in domain
        or "github.io" in domain
        or "gitlab.com" in domain
        or "gitlab.io" in domain
        or domain.startswith("git.")
    ):
        return "githubUrl"
    # Everything else → githubUrl anyway (release/setup pages)
    return "githubUrl"


def is_unknown_link_type(text: str, url: str) -> bool:
    """Return True if the link goes to githubUrl but is NOT a standard
    git-forge domain (github.com, github.io, gitlab.com, git.*.*)."""
    if not url or not text or text == "N/A":
        return False
    from urllib.parse import urlparse as _up
    domain = _up(url).netloc.lower()
    is_git_forge = (
        "github.com" in domain
        or "github.io" in domain
        or "gitlab.com" in domain
        or "gitlab.io" in domain
        or domain.startswith("git.")
        or "discord.com" in domain
        or "archipelago.miraheze.org" in url
        or "archipelago.gg" in url
    )
    return not is_git_forge


def find_latest_xlsx(directory: str) -> str | None:
    """Find the most recent .xlsx file in the given directory."""
    if not os.path.isdir(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".xlsx") and not f.startswith("~$")
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


# ---------------------------------------------------------------------------
# XLSX parsing
# ---------------------------------------------------------------------------

def parse_xlsx(xlsx_path: str) -> tuple[list, list]:
    """
    Parse the XLSX and return (xlsx_games, unknown_links).

    xlsx_games: list of dicts with keys:
        xlsxName, stability, guideText, guideUrl, guideField
    unknown_links: list of dicts with keys:
        game, text, url, domain
    """
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active

    xlsx_games = []
    unknown_links = []

    for row in ws.iter_rows(min_row=2):
        name_cell, stab_cell, guide_cell = row[0], row[1], row[2]
        if not name_cell.value:
            continue

        name = str(name_cell.value).strip()
        stability_raw = str(stab_cell.value).strip() if stab_cell.value else None
        # Normalize stability label
        stability = (
            "Broken" if stability_raw == "Broken on Main"
            else stability_raw
        )

        guide_text = str(guide_cell.value).strip() if guide_cell.value else None
        guide_url = guide_cell.hyperlink.target if guide_cell.hyperlink else None

        guide_field = classify_link(guide_url) if guide_url else None

        if is_unknown_link_type(guide_text, guide_url):
            unknown_links.append({
                "game": name,
                "text": guide_text,
                "url": guide_url,
                "domain": urlparse(guide_url).netloc
            })

        xlsx_games.append({
            "xlsxName": name,
            "stability": stability,
            "guideText": guide_text,
            "guideUrl": guide_url,
            "guideField": guide_field,
        })

    return xlsx_games, unknown_links


# ---------------------------------------------------------------------------
# Diff generation
# ---------------------------------------------------------------------------

def build_diff(xlsx_games: list, json_games: list) -> dict:
    """
    Compare XLSX games with JSON games.
    Returns a dict with:
        new_games: games in XLSX with no JSON match
        updates:   games in both with stability or URL changes
        matched:   games matched with no changes
    """
    norm_to_json = {normalize(g["name"]): g for g in json_games}
    id_to_json = {g["id"]: g for g in json_games}

    # Build a list of all JSON game names for autocomplete
    all_json_names = [{"id": g["id"], "name": g["name"]} for g in json_games]

    new_games = []
    updates = []
    matched = []

    for xg in xlsx_games:
        norm_xlsx = normalize(xg["xlsxName"])

        # --- Try to find a matching JSON game ---
        json_game = norm_to_json.get(norm_xlsx)

        # Fallback: partial match
        if json_game is None:
            for norm_json, jg in norm_to_json.items():
                if norm_xlsx in norm_json or norm_json in norm_xlsx:
                    json_game = jg
                    break

        if json_game is None:
            new_games.append({
                **xg,
                "suggestedId": slugify(xg["xlsxName"]),
                "suggestedName": xg["xlsxName"],
            })
            continue

        # --- Detect changes ---
        changes = {}

        # Stability
        if xg["stability"] and json_game.get("stability") != xg["stability"]:
            changes["stability"] = {
                "old": json_game.get("stability"),
                "new": xg["stability"],
            }

        # Setup guide URL
        field = xg["guideField"]
        url = xg["guideUrl"]
        if field and url and json_game.get(field) != url:
            changes[field] = {
                "old": json_game.get(field),
                "new": url,
            }

        entry = {
            **xg,
            "matchedId": json_game["id"],
            "matchedName": json_game["name"],
        }

        if changes:
            entry["changes"] = changes
            updates.append(entry)
        else:
            matched.append(entry)

    return {
        "new_games": new_games,
        "updates": updates,
        "matched": matched,
        "all_json_names": all_json_names,
    }


# ---------------------------------------------------------------------------
# Apply accepted changes to games.json
# ---------------------------------------------------------------------------

def apply_changes(games_data: dict, decisions: list) -> dict:
    """
    Apply accepted/mapped decisions to games_data.

    decisions: list of dicts:
        action: "accept" | "skip" | "map"
        type:   "new" | "update"
        data:   the diff entry
        mapToId: (only for action="map") existing game ID
    """
    id_to_game = {g["id"]: g for g in games_data["games"]}
    new_games = []

    for decision in decisions:
        action = decision["action"]
        dtype = decision["type"]
        data = decision["data"]

        if action == "skip":
            continue

        if dtype == "update" and action == "accept":
            game = id_to_game.get(data["matchedId"])
            if not game:
                continue
            for field, change in data.get("changes", {}).items():
                game[field] = change["new"]

        elif dtype == "new" and action == "accept":
            # Create a new minimal game entry
            new_game = {
                "id": data["suggestedId"],
                "name": data["suggestedName"],
                "platform": "",
                "url": None,
                "description": f"Archipelago randomizer for {data['suggestedName']}",
                "githubUrl": None,
                "discordUrl": None,
                "completed": [],
                "todo": [],
                "inProgress": [],
                "twitchId": None,
            }
            if data.get("stability"):
                new_game["stability"] = data["stability"]
            field = data.get("guideField")
            url = data.get("guideUrl")
            if field and url:
                new_game[field] = url
            new_games.append(new_game)

        elif dtype == "new" and action == "map":
            # Map XLSX entry to an existing game
            map_id = decision.get("mapToId")
            game = id_to_game.get(map_id)
            if not game:
                continue
            if data.get("stability"):
                game["stability"] = data["stability"]
            field = data.get("guideField")
            url = data.get("guideUrl")
            if field and url and not game.get(field):
                game[field] = url

    # Insert new games and re-sort
    games_data["games"].extend(new_games)
    games_data["games"].sort(key=lambda g: normalize(g["name"]))

    return games_data


# ---------------------------------------------------------------------------
# Embedded HTML interface
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Archipelago — XLSX Import Review</title>
<style>
  :root {
    --primary: #e8a835;
    --bg: #121212;
    --card: #1e1e1e;
    --border: #333;
    --text: #e0e0e0;
    --muted: #999;
    --green: #4ade80;
    --yellow: #facc15;
    --red: #f87171;
    --blue: #6ba3ff;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: var(--bg); color: var(--text);
         line-height: 1.5; padding: 20px; }
  h1 { color: var(--primary); margin-bottom: 6px; }
  h2 { color: var(--primary); margin: 20px 0 10px; font-size: 1.1rem; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
  p.subtitle { color: var(--muted); margin-bottom: 16px; font-size: 0.9rem; }

  .stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
  .stat { background: var(--card); border: 1px solid var(--border); border-radius: 8px;
          padding: 10px 18px; text-align: center; }
  .stat .n { font-size: 1.8rem; font-weight: bold; color: var(--primary); }
  .stat .l { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

  .toolbar { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
  .btn { padding: 6px 14px; border-radius: 6px; border: 1px solid var(--border);
         cursor: pointer; font-size: 0.85rem; background: #2a2a2a; color: var(--text); }
  .btn:hover { background: #3a3a3a; }
  .btn.primary { background: var(--primary); color: #000; border-color: var(--primary); font-weight: bold; }
  .btn.primary:hover { background: #f0b840; }
  .btn.accept { background: #1a3a1a; border-color: var(--green); color: var(--green); }
  .btn.accept:hover { background: #1f4a1f; }
  .btn.skip { background: #2a2a2a; border-color: var(--border); color: var(--muted); }
  .btn.skip:hover { background: #3a3a3a; }
  .btn.map { background: #1a2a3a; border-color: var(--blue); color: var(--blue); }
  .btn.map:hover { background: #1f3a4f; }
  .btn.danger { background: #3a1a1a; border-color: var(--red); color: var(--red); }
  .btn.danger:hover { background: #4a2a2a; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .game-entry { background: var(--card); border: 1px solid var(--border); border-radius: 10px;
                padding: 14px; margin-bottom: 10px; }
  .game-entry.accepted { border-color: var(--green); opacity: 0.7; }
  .game-entry.skipped { border-color: var(--border); opacity: 0.4; }
  .game-entry.mapped { border-color: var(--blue); opacity: 0.7; }

  .game-name { font-weight: bold; font-size: 1rem; margin-bottom: 4px; }
  .game-meta { font-size: 0.8rem; color: var(--muted); display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: bold; }
  .badge.stable { background: #1a3a1a; color: var(--green); }
  .badge.unstable { background: #3a3a1a; color: var(--yellow); }
  .badge.broken { background: #3a1a1a; color: var(--red); }
  .badge.new { background: #1a2a3a; color: var(--blue); }
  .badge.unknown { background: #2a2a2a; color: var(--muted); }

  .changes { display: flex; flex-direction: column; gap: 4px; margin-bottom: 8px; }
  .change-row { font-size: 0.82rem; display: flex; align-items: center; gap: 6px; }
  .change-field { color: var(--primary); font-weight: bold; min-width: 120px; }
  .change-old { color: var(--red); text-decoration: line-through; max-width: 240px;
                overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .change-new { color: var(--green); max-width: 340px;
                overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .arrow { color: var(--muted); }

  .actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  .status-label { font-size: 0.8rem; font-style: italic; margin-left: 6px; }

  .map-row { display: flex; gap: 8px; align-items: center; margin-top: 6px; flex-wrap: wrap; }
  .autocomplete-wrap { position: relative; flex: 1; min-width: 200px; }
  .autocomplete-wrap input { width: 100%; background: #2a2a2a; border: 1px solid var(--border);
    border-radius: 6px; color: var(--text); padding: 5px 10px; font-size: 0.85rem; }
  .autocomplete-wrap input:focus { outline: none; border-color: var(--primary); }
  .autocomplete-list { position: absolute; top: 100%; left: 0; right: 0; background: #2a2a2a;
    border: 1px solid var(--border); border-radius: 6px; max-height: 200px; overflow-y: auto;
    z-index: 999; margin-top: 2px; }
  .autocomplete-list div { padding: 6px 10px; cursor: pointer; font-size: 0.82rem; }
  .autocomplete-list div:hover, .autocomplete-list div.selected { background: #3a3a3a; }

  .unknown-links { background: #2a1a0a; border: 1px solid #8a5500; border-radius: 10px;
                   padding: 14px; margin-bottom: 20px; }
  .unknown-links h3 { color: var(--yellow); margin-bottom: 8px; font-size: 0.95rem; }
  .unknown-links p { font-size: 0.82rem; color: var(--muted); margin-bottom: 8px; }
  .unknown-links table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
  .unknown-links th { color: var(--muted); text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--border); }
  .unknown-links td { padding: 4px 8px; border-bottom: 1px solid #2a2a2a; }
  .unknown-links td a { color: var(--primary); }
  .unknown-links .domain { color: var(--yellow); font-size: 0.75rem; }

  .progress-bar-wrap { background: #2a2a2a; border-radius: 4px; height: 6px; margin-top: 8px; }
  .progress-bar { background: var(--primary); height: 6px; border-radius: 4px; transition: width 0.3s; }

  .save-section { margin-top: 30px; padding: 20px; background: var(--card); border-radius: 10px;
                  border: 1px solid var(--border); }
  .save-section h3 { margin-bottom: 10px; }
  .save-summary { font-size: 0.85rem; color: var(--muted); margin-bottom: 14px; }
  .save-summary span { color: var(--text); font-weight: bold; }

  .toast { position: fixed; bottom: 20px; right: 20px; padding: 12px 20px; border-radius: 8px;
           font-size: 0.9rem; z-index: 9999; display: none; }
  .toast.success { background: #1a3a1a; border: 1px solid var(--green); color: var(--green); }
  .toast.error { background: #3a1a1a; border: 1px solid var(--red); color: var(--red); }

  .section-toolbar { display: flex; gap: 6px; margin-bottom: 12px; }

  .collapsible-section { margin-bottom: 10px; }
  .section-header {
    cursor: pointer; user-select: none;
    display: flex; align-items: center; gap: 8px;
    color: var(--primary); font-size: 1.1rem; font-weight: bold;
    border-bottom: 1px solid var(--border); padding-bottom: 6px;
    margin: 20px 0 0;
  }
  .section-header:hover { color: #f0b840; }
  .collapse-icon { font-size: 0.75rem; transition: transform 0.2s; display: inline-block; }
  .collapse-icon.open { transform: rotate(90deg); }
  .section-body { margin-top: 10px; }

  @media (max-width: 600px) {
    .stats { gap: 8px; }
    .stat .n { font-size: 1.3rem; }
  }
</style>
</head>
<body>

<h1>🏝️ Archipelago — XLSX Import Review</h1>
<p class="subtitle">Compare the XLSX data with <code>data/games.json</code> and validate each change before saving.</p>

<div class="stats" id="statsPanel"></div>

<div id="unknownLinksSection"></div>

<div id="newGamesSection" class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('newGamesBody')">
    <span class="collapse-icon" id="newGamesIcon">▶</span>
    New Games <span id="newGamesCount"></span>
  </h2>
  <div id="newGamesBody" class="section-body" style="display:none">
    <p class="subtitle">Games found in the XLSX but not matched in games.json. Accept to create, Map to link to an existing game, or Skip.</p>
    <div class="section-toolbar">
      <button class="btn" onclick="acceptAll('new')">Accept All</button>
      <button class="btn" onclick="skipAll('new')">Skip All</button>
    </div>
    <div id="newGamesList"></div>
  </div>
</div>

<div id="updatesSection" class="collapsible-section">
  <h2 class="section-header" onclick="toggleSection('updatesBody')">
    <span class="collapse-icon" id="updatesIcon">▶</span>
    Updates <span id="updatesCount"></span>
  </h2>
  <div id="updatesBody" class="section-body" style="display:none">
    <p class="subtitle">Existing games with new stability info or setup guide URLs from the XLSX.</p>
    <div class="section-toolbar">
      <button class="btn" onclick="acceptAll('update')">Accept All</button>
      <button class="btn" onclick="skipAll('update')">Skip All</button>
    </div>
    <div id="updatesList"></div>
  </div>
</div>

<div class="save-section">
  <h3>💾 Save Changes</h3>
  <div class="save-summary" id="saveSummary">—</div>
  <button class="btn primary" id="saveBtn" onclick="saveChanges()">Apply & Save to games.json</button>
</div>

<div class="toast" id="toast"></div>

<script>
// Data injected by Python
const DIFF = __DIFF_JSON__;
const ALL_JSON_NAMES = DIFF.all_json_names || [];

// State: decision per entry
// key: xlsxName, value: { action: 'accept'|'skip'|'map', mapToId }
const decisions = {};

function stability(s) {
  if (!s) return '<span class="badge unknown">—</span>';
  const cls = s.toLowerCase();
  return `<span class="badge ${cls}">${s}</span>`;
}

function guideLink(entry) {
  if (!entry.guideUrl) return '<span style="color:var(--muted)">—</span>';
  const text = entry.guideText || entry.guideField || 'Link';
  return `<a href="${entry.guideUrl}" target="_blank" style="color:var(--primary);font-size:0.8rem">[${text}]</a>`;
}

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ---------------------------------------------------------------------------
// Toggle sections
// ---------------------------------------------------------------------------
function toggleSection(bodyId) {
  const body = document.getElementById(bodyId);
  const isOpen = body.style.display !== 'none';
  body.style.display = isOpen ? 'none' : 'block';
  // Update arrow icon
  const iconId = bodyId.replace('Body', 'Icon');
  const icon = document.getElementById(iconId);
  if (icon) icon.classList.toggle('open', !isOpen);
}

// ---------------------------------------------------------------------------
// Render new games
// ---------------------------------------------------------------------------
function renderNewGames() {
  const list = document.getElementById('newGamesList');
  const count = document.getElementById('newGamesCount');
  count.textContent = `(${DIFF.new_games.length})`;

  if (!DIFF.new_games.length) {
    list.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:8px 0">No new games detected.</p>';
    return;
  }

  list.innerHTML = DIFF.new_games.map((g, i) => {
    const key = `new_${i}`;
    const d = decisions[key] || { action: 'pending' };
    const cardClass = d.action === 'accept' ? 'accepted' : d.action === 'skip' ? 'skipped' : d.action === 'map' ? 'mapped' : '';

    return `
    <div class="game-entry ${cardClass}" id="card_${key}">
      <div class="game-name">${escapeHtml(g.xlsxName)} <span class="badge new">NEW</span></div>
      <div class="game-meta">
        <span>Stability: ${stability(g.stability)}</span>
        <span>Setup Guide: ${guideLink(g)}</span>
      </div>
      <div class="actions">
        <button class="btn accept" onclick="decide('${key}','new','accept')">✓ Accept</button>
        <button class="btn skip" onclick="decide('${key}','new','skip')">✗ Skip</button>
        <button class="btn map" onclick="toggleMapRow('${key}')">🔗 Map to existing</button>
        <span class="status-label" id="status_${key}">${d.action !== 'pending' ? d.action : ''}</span>
      </div>
      <div class="map-row" id="maprow_${key}" style="display:none">
        <div class="autocomplete-wrap">
          <input type="text" id="mapinput_${key}" placeholder="Type game name..."
                 oninput="filterAutocomplete('${key}', this.value)"
                 onkeydown="acKeydown(event,'${key}')">
          <div class="autocomplete-list" id="aclist_${key}" style="display:none"></div>
        </div>
        <button class="btn map" onclick="confirmMap('${key}')">Confirm Map</button>
        <button class="btn" onclick="toggleMapRow('${key}')">Cancel</button>
      </div>
    </div>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Render updates
// ---------------------------------------------------------------------------
function renderUpdates() {
  const list = document.getElementById('updatesList');
  const count = document.getElementById('updatesCount');
  count.textContent = `(${DIFF.updates.length})`;

  if (!DIFF.updates.length) {
    list.innerHTML = '<p style="color:var(--muted);font-size:0.85rem;margin:8px 0">No updates detected.</p>';
    return;
  }

  list.innerHTML = DIFF.updates.map((g, i) => {
    const key = `upd_${i}`;
    const d = decisions[key] || { action: 'pending' };
    const cardClass = d.action === 'accept' ? 'accepted' : d.action === 'skip' ? 'skipped' : '';
    const changes = g.changes || {};

    const changeRows = Object.entries(changes).map(([field, c]) => `
      <div class="change-row">
        <span class="change-field">${field}</span>
        <span class="arrow">→</span>
        ${c.old ? `<span class="change-old" title="${escapeHtml(c.old)}">${escapeHtml(c.old)}</span><span class="arrow">→</span>` : ''}
        <span class="change-new" title="${escapeHtml(c.new)}">${escapeHtml(c.new)}</span>
      </div>`).join('');

    return `
    <div class="game-entry ${cardClass}" id="card_${key}">
      <div class="game-name">${escapeHtml(g.matchedName)}</div>
      <div class="game-meta">
        <span style="color:var(--muted)">XLSX: ${escapeHtml(g.xlsxName)}</span>
      </div>
      <div class="changes">${changeRows}</div>
      <div class="actions">
        <button class="btn accept" onclick="decide('${key}','update','accept')">✓ Accept</button>
        <button class="btn skip" onclick="decide('${key}','update','skip')">✗ Skip</button>
        <span class="status-label" id="status_${key}">${d.action !== 'pending' ? d.action : ''}</span>
      </div>
    </div>`;
  }).join('');
}

// ---------------------------------------------------------------------------
// Render unknown links warning
// ---------------------------------------------------------------------------
function renderUnknownLinks() {
  const section = document.getElementById('unknownLinksSection');
  const links = DIFF.unknown_links || [];
  if (!links.length) return;

  const rows = links.map(l => `
    <tr>
      <td>${escapeHtml(l.game)}</td>
      <td>${escapeHtml(l.text)}</td>
      <td><span class="domain">${escapeHtml(l.domain)}</span></td>
      <td><a href="${escapeHtml(l.url)}" target="_blank">${escapeHtml(l.url.slice(0, 60))}${l.url.length > 60 ? '…' : ''}</a></td>
    </tr>`).join('');

  section.innerHTML = `
    <div class="unknown-links">
      <h3>⚠️ Liens non-standards dans <code>githubUrl</code> (${links.length} liens — domaines hors github.com)</h3>
      <p>Ces liens sont stockés dans <code>githubUrl</code> mais pointent vers des domaines autres que github.com
         (gitlab, codeberg, itch, modrinth, sites perso, etc.). Vérifiez qu'ils sont corrects.</p>
      <table>
        <thead><tr><th>Game</th><th>Type</th><th>Domain</th><th>URL</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
}

// ---------------------------------------------------------------------------
// Stats
// ---------------------------------------------------------------------------
function renderStats() {
  const accepted = Object.values(decisions).filter(d => d.action === 'accept').length;
  const skipped = Object.values(decisions).filter(d => d.action === 'skip').length;
  const mapped = Object.values(decisions).filter(d => d.action === 'map').length;
  const total = DIFF.new_games.length + DIFF.updates.length;
  const pending = total - accepted - skipped - mapped;

  document.getElementById('statsPanel').innerHTML = `
    <div class="stat"><div class="n">${DIFF.new_games.length}</div><div class="l">New Games</div></div>
    <div class="stat"><div class="n">${DIFF.updates.length}</div><div class="l">Updates</div></div>
    <div class="stat"><div class="n">${DIFF.matched.length}</div><div class="l">Already Matched</div></div>
    <div class="stat"><div class="n" style="color:var(--green)">${accepted + mapped}</div><div class="l">Accepted</div></div>
    <div class="stat"><div class="n" style="color:var(--muted)">${skipped}</div><div class="l">Skipped</div></div>
    <div class="stat"><div class="n" style="color:var(--yellow)">${pending}</div><div class="l">Pending</div></div>`;

  document.getElementById('saveSummary').innerHTML =
    `<span>${accepted + mapped}</span> changes will be applied. <span>${skipped}</span> skipped. <span>${pending}</span> still pending.`;
}

// ---------------------------------------------------------------------------
// Decision logic
// ---------------------------------------------------------------------------
function decide(key, type, action) {
  decisions[key] = { action, type };
  const card = document.getElementById(`card_${key}`);
  card.className = `game-entry ${action === 'accept' ? 'accepted' : action === 'skip' ? 'skipped' : 'mapped'}`;
  const statusEl = document.getElementById(`status_${key}`);
  if (statusEl) statusEl.textContent = action;
  renderStats();
}

function acceptAll(type) {
  const items = type === 'new' ? DIFF.new_games : DIFF.updates;
  const prefix = type === 'new' ? 'new_' : 'upd_';
  items.forEach((_, i) => decide(`${prefix}${i}`, type, 'accept'));
  type === 'new' ? renderNewGames() : renderUpdates();
  renderStats();
}

function skipAll(type) {
  const items = type === 'new' ? DIFF.new_games : DIFF.updates;
  const prefix = type === 'new' ? 'new_' : 'upd_';
  items.forEach((_, i) => decide(`${prefix}${i}`, type, 'skip'));
  type === 'new' ? renderNewGames() : renderUpdates();
  renderStats();
}

// ---------------------------------------------------------------------------
// Autocomplete for map-to-existing
// ---------------------------------------------------------------------------
let acSelected = {};  // key -> selected index

function toggleMapRow(key) {
  const row = document.getElementById(`maprow_${key}`);
  row.style.display = row.style.display === 'none' ? 'flex' : 'none';
}

function filterAutocomplete(key, query) {
  const list = document.getElementById(`aclist_${key}`);
  if (!query.trim()) { list.style.display = 'none'; return; }

  const q = query.toLowerCase();
  const matches = ALL_JSON_NAMES.filter(g =>
    g.name.toLowerCase().includes(q)
  ).slice(0, 12);

  if (!matches.length) { list.style.display = 'none'; return; }

  acSelected[key] = 0;
  list.innerHTML = matches.map((g, i) =>
    `<div data-id="${escapeHtml(g.id)}" data-name="${escapeHtml(g.name)}"
          class="${i === 0 ? 'selected' : ''}"
          onmousedown="selectAcItem('${key}', '${escapeHtml(g.id)}', '${escapeHtml(g.name).replace(/'/g, "\\'")}')"
     >${escapeHtml(g.name)}</div>`
  ).join('');
  list.style.display = 'block';
}

function selectAcItem(key, id, name) {
  const input = document.getElementById(`mapinput_${key}`);
  input.value = name;
  input.dataset.selectedId = id;
  document.getElementById(`aclist_${key}`).style.display = 'none';
}

function acKeydown(e, key) {
  const list = document.getElementById(`aclist_${key}`);
  const items = list.querySelectorAll('div');
  if (!items.length) return;
  if (e.key === 'ArrowDown') {
    acSelected[key] = Math.min((acSelected[key] || 0) + 1, items.length - 1);
    items.forEach((el, i) => el.classList.toggle('selected', i === acSelected[key]));
    e.preventDefault();
  } else if (e.key === 'ArrowUp') {
    acSelected[key] = Math.max((acSelected[key] || 0) - 1, 0);
    items.forEach((el, i) => el.classList.toggle('selected', i === acSelected[key]));
    e.preventDefault();
  } else if (e.key === 'Enter') {
    const sel = items[acSelected[key] || 0];
    if (sel) selectAcItem(key, sel.dataset.id, sel.dataset.name);
    e.preventDefault();
  } else if (e.key === 'Escape') {
    list.style.display = 'none';
  }
}

function confirmMap(key) {
  const input = document.getElementById(`mapinput_${key}`);
  const mapToId = input.dataset.selectedId;
  if (!mapToId) { showToast('Please select a game from the list first.', 'error'); return; }
  decisions[key] = { action: 'map', type: 'new', mapToId };
  const card = document.getElementById(`card_${key}`);
  card.className = 'game-entry mapped';
  const statusEl = document.getElementById(`status_${key}`);
  if (statusEl) statusEl.textContent = `mapped → ${input.value}`;
  document.getElementById(`maprow_${key}`).style.display = 'none';
  renderStats();
}

// ---------------------------------------------------------------------------
// Save
// ---------------------------------------------------------------------------
async function saveChanges() {
  const payload = [];

  DIFF.new_games.forEach((g, i) => {
    const key = `new_${i}`;
    const d = decisions[key];
    if (!d || d.action === 'pending') return;
    payload.push({ action: d.action, type: 'new', data: g, mapToId: d.mapToId || null });
  });

  DIFF.updates.forEach((g, i) => {
    const key = `upd_${i}`;
    const d = decisions[key];
    if (!d || d.action === 'pending') return;
    payload.push({ action: d.action, type: 'update', data: g, mapToId: null });
  });

  if (!payload.length) {
    showToast('No decisions to save yet.', 'error');
    return;
  }

  const saveBtn = document.getElementById('saveBtn');
  saveBtn.disabled = true;
  saveBtn.textContent = 'Saving...';

  try {
    const res = await fetch('/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.ok) {
      showToast(`✅ Saved! ${data.applied} changes applied to games.json.`, 'success');
    } else {
      showToast('❌ Error: ' + data.error, 'error');
    }
  } catch (e) {
    showToast('❌ Network error: ' + e.message, 'error');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Apply & Save to games.json';
  }
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 4000);
}

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
renderUnknownLinks();
renderNewGames();
renderUpdates();
renderStats();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    diff_data = None
    games_json_path = None

    def log_message(self, format, *args):
        pass  # Suppress default access logs

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            html = HTML_TEMPLATE.replace(
                "__DIFF_JSON__",
                json.dumps(self.diff_data, ensure_ascii=False)
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
                with open(self.games_json_path, "r", encoding="utf-8") as f:
                    games_data = json.load(f)

                updated = apply_changes(games_data, decisions)

                with open(self.games_json_path, "w", encoding="utf-8") as f:
                    json.dump(updated, f, indent=2, ensure_ascii=False)

                applied = len([d for d in decisions if d["action"] in ("accept", "map")])
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
    # Find XLSX
    if len(sys.argv) > 1:
        xlsx_path = sys.argv[1]
    else:
        xlsx_path = find_latest_xlsx(XLSX_DEFAULT_DIR)
        if not xlsx_path:
            print(f"❌ No .xlsx file found in: {XLSX_DEFAULT_DIR}")
            print("Usage: python scripts/merge_xlsx.py [path/to/file.xlsx]")
            sys.exit(1)

    if not os.path.isfile(xlsx_path):
        print(f"❌ File not found: {xlsx_path}")
        sys.exit(1)

    if not os.path.isfile(GAMES_JSON_PATH):
        print(f"❌ games.json not found: {GAMES_JSON_PATH}")
        sys.exit(1)

    print(f"[XLSX] Reading: {os.path.basename(xlsx_path)}")
    xlsx_games, unknown_links = parse_xlsx(xlsx_path)
    print(f"       {len(xlsx_games)} games found in XLSX")

    print("[JSON] Reading games.json...")
    with open(GAMES_JSON_PATH, "r", encoding="utf-8") as f:
        games_data = json.load(f)
    json_games = games_data["games"]
    print(f"       {len(json_games)} games in JSON")

    print("[DIFF] Generating diff...")
    diff = build_diff(xlsx_games, json_games)
    diff["unknown_links"] = unknown_links

    print(f"       {len(diff['new_games'])} new games")
    print(f"       {len(diff['updates'])} updates")
    print(f"       {len(diff['matched'])} already matched")
    if unknown_links:
        print(f"       WARNING: {len(unknown_links)} unknown link types (see UI for details)")

    # Start HTTP server
    Handler.diff_data = diff
    Handler.games_json_path = GAMES_JSON_PATH

    port = 8765
    server = HTTPServer(("localhost", port), Handler)

    url = f"http://localhost:{port}"
    print(f"\n[SERVER] Opening review interface at {url}")
    print("         Press Ctrl+C to stop the server.\n")

    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped.")


if __name__ == "__main__":
    main()
