import copy
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from scripts import find_missing_twitch


class FindMissingTwitchTests(unittest.TestCase):
    def test_missing_list_excludes_only_marked_or_already_identified_games(self):
        games = [
            {"id": "missing", "name": "Missing"},
            {"id": "empty", "name": "Empty", "twitchId": ""},
            {"id": "marked", "name": "Marked", "archipelagoOnly": True},
            {"id": "restored", "name": "Restored", "archipelagoOnly": False},
            {"id": "identified", "name": "Identified", "twitchId": "123"},
        ]
        original = copy.deepcopy(games)
        missing = find_missing_twitch.find_missing(games)
        self.assertEqual([game["id"] for game in missing], ["missing", "empty", "restored"])
        self.assertEqual(games, original)

    def test_marking_preserves_game_and_skips_future_suggestion_queries(self):
        game = {"id": "custom", "name": "Custom", "twitchId": None, "todo": ["Example"]}
        games_data = {"games": [game]}
        decision = {"action": "archipelagoOnly", "gameId": "custom", "twitchId": None}
        original = copy.deepcopy(game)

        for _ in range(2):
            find_missing_twitch.apply_decisions(games_data, [decision])
        self.assertEqual(games_data["games"], [{**original, "archipelagoOnly": True}])
        with patch.object(find_missing_twitch, "search_twitch_game") as search:
            missing = find_missing_twitch.find_missing(games_data["games"])
            self.assertEqual(
                find_missing_twitch.enrich_with_suggestions(missing, "test-token"), []
            )
            search.assert_not_called()

    def test_regular_skip_remains_temporary(self):
        games_data = {"games": [{"id": "custom", "name": "Custom", "twitchId": None}]}
        original = copy.deepcopy(games_data)
        for action in ("skip", "skipped"):
            find_missing_twitch.apply_decisions(
                games_data, [{"action": action, "gameId": "custom"}]
            )
        self.assertEqual(games_data, original)
        self.assertEqual(len(find_missing_twitch.find_missing(games_data["games"])), 1)

    def test_setting_a_twitch_id_clears_archipelago_only_marker(self):
        for action in ("accept", "accepted", "manual"):
            with self.subTest(action=action):
                games_data = {
                    "games": [{"id": "custom", "name": "Custom", "archipelagoOnly": True}]
                }
                find_missing_twitch.apply_decisions(
                    games_data,
                    [{"action": action, "gameId": "custom", "twitchId": "123"}],
                )
                self.assertEqual(games_data["games"][0]["twitchId"], "123")
                self.assertNotIn("archipelagoOnly", games_data["games"][0])

    def test_empty_manual_id_does_not_clear_persistent_marker(self):
        games_data = {"games": [{"id": "custom", "archipelagoOnly": True}]}
        find_missing_twitch.apply_decisions(
            games_data, [{"action": "manual", "gameId": "custom", "twitchId": " "}]
        )
        self.assertTrue(games_data["games"][0]["archipelagoOnly"])
        self.assertIsNone(games_data["games"][0]["twitchId"])

    def test_http_save_persists_marker_without_removing_games(self):
        original = {
            "games": [
                {"id": "custom", "name": "Custom", "twitchId": None, "url": "example"},
                {"id": "other", "name": "Other", "twitchId": None},
            ]
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            games_path = Path(temp_dir) / "games.json"
            games_path.write_text(json.dumps(original), encoding="utf-8")
            with (
                patch.object(find_missing_twitch.Handler, "games_json_path", str(games_path)),
                patch.object(find_missing_twitch.Handler, "enriched", []),
            ):
                server = HTTPServer(("127.0.0.1", 0), find_missing_twitch.Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    base_url = f"http://127.0.0.1:{server.server_port}"
                    with urlopen(base_url, timeout=5) as response:
                        self.assertIn("Archipelago-only", response.read().decode("utf-8"))
                    request = Request(
                        f"{base_url}/save",
                        data=json.dumps([{
                            "action": "archipelagoOnly",
                            "gameId": "custom",
                            "twitchId": None,
                        }]).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    with urlopen(request, timeout=5) as response:
                        self.assertEqual(json.load(response), {"ok": True, "applied": 1})
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)

            saved = json.loads(games_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["games"][0], {
                **original["games"][0], "archipelagoOnly": True,
            })
            self.assertEqual(saved["games"][1], original["games"][1])
            self.assertEqual(
                find_missing_twitch.find_missing(saved["games"]), [original["games"][1]]
            )

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for UI tests")
    def test_ui_button_bulk_actions_and_save_payload(self):
        games = [
            {"id": "custom", "name": "Custom", "candidates": [], "best": None},
            {
                "id": "other", "name": "Other", "candidates": [],
                "best": {"id": "123", "name": "Other"},
            },
        ]
        html = find_missing_twitch.HTML.replace("__GAMES_JSON__", json.dumps(games))
        script = html.split("<script>", 1)[1].split("</script>", 1)[0]
        harness = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const elements = new Map();
let payload;
const context = vm.createContext({
  document: {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { style: {} });
      return elements.get(id);
    },
  },
  setTimeout() {},
  async fetch(url, options) {
    assert.equal(url, '/save');
    payload = JSON.parse(options.body);
    return { async json() { return { ok: true, applied: payload.length }; } };
  },
});
vm.runInContext(fs.readFileSync(0, 'utf8'), context);
(async () => {
  const button = elements.get('gamesList').innerHTML.match(
    /<button class="btn archipelago-only" onclick="([^"]+)"/
  );
  assert.ok(button);
  vm.runInContext(button[1], context);
  assert.equal(elements.get('card_g_0').className, 'game-entry archipelago-only');
  assert.match(elements.get('status_g_0').textContent, /skipped on future runs/);
  assert.match(elements.get('saveSummary').innerHTML, /<span>1<\/span> still pending/);
  await vm.runInContext('saveChanges()', context);
  assert.deepEqual(payload, [
    { action: 'archipelagoOnly', gameId: 'custom', twitchId: null },
  ]);
  assert.equal(elements.get('toast').textContent, 'Done! 1 changes saved.');
  vm.runInContext('acceptAll()', context);
  assert.equal(vm.runInContext("decisions.g_0.action", context), 'archipelagoOnly');
  assert.equal(vm.runInContext("decisions.g_1.action", context), 'accepted');
  await vm.runInContext('saveChanges()', context);
  assert.deepEqual(payload, [
    { action: 'archipelagoOnly', gameId: 'custom', twitchId: null },
    { action: 'accepted', gameId: 'other', twitchId: '123' },
  ]);
  vm.runInContext('skipAll(); renderGames()', context);
  assert.equal(vm.runInContext("decisions.g_0.action", context), 'archipelagoOnly');
  assert.equal(vm.runInContext("decisions.g_1.action", context), 'skipped');
  assert.match(elements.get('gamesList').innerHTML, /game-entry archipelago-only/);
  await vm.runInContext('saveChanges()', context);
  assert.equal(payload.length, 1);
  vm.runInContext("decide('g_0', 'custom', 'accepted', '456')", context);
  await vm.runInContext('saveChanges()', context);
  assert.deepEqual(payload, [
    { action: 'accepted', gameId: 'custom', twitchId: '456' },
  ]);
})().catch(error => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            ["node", "-e", harness],
            input=script,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
