import json
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen

from openpyxl import Workbook

from scripts import merge_xlsx


GENERIC_TUTORIAL_URL = "https://archipelago.gg/tutorial/"
SPECIFIC_TUTORIAL_URL = "https://archipelago.gg/tutorial/Example/setup/en"


def make_xlsx_game(name, guide_url, stability="Stable"):
    return {
        "xlsxName": name,
        "stability": stability,
        "guideText": "Setup",
        "guideUrl": guide_url,
        "guideField": merge_xlsx.classify_link(guide_url),
    }


def make_json_game(name="Existing Game", url=SPECIFIC_TUTORIAL_URL):
    return {
        "id": merge_xlsx.slugify(name),
        "name": name,
        "stability": "Stable",
        "url": url,
    }


class MergeXlsxTests(unittest.TestCase):
    def test_generic_tutorial_variants_do_not_create_updates(self):
        generic_urls = (
            GENERIC_TUTORIAL_URL,
            "https://archipelago.gg/tutorial",
            "http://archipelago.gg/tutorial/",
            "http://archipelago.gg:80/tutorial/",
            "HTTPS://ARCHIPELAGO.GG/tutorial/",
            "https://archipelago.gg:443/tutorial/",
        )
        for guide_url in generic_urls:
            for existing_url in (SPECIFIC_TUTORIAL_URL, None, "", GENERIC_TUTORIAL_URL):
                with self.subTest(guide_url=guide_url, existing_url=existing_url):
                    game = make_json_game(url=existing_url)
                    diff = merge_xlsx.build_diff(
                        [make_xlsx_game(game["name"], guide_url)], [game], {}
                    )

                    self.assertEqual(diff["updates"], [])
                    self.assertEqual(len(diff["matched"]), 1)
                    self.assertEqual(game["url"], existing_url)

    def test_other_changes_remain_actionable_without_overwriting_url(self):
        game = make_json_game()
        xlsx_game = make_xlsx_game(game["name"], GENERIC_TUTORIAL_URL, "Unstable")
        diff = merge_xlsx.build_diff([xlsx_game], [game], {})

        self.assertEqual(len(diff["updates"]), 1)
        self.assertEqual(
            diff["updates"][0]["changes"],
            {"stability": {"old": "Stable", "new": "Unstable"}},
        )
        updated, _ = merge_xlsx.apply_changes(
            {"games": [game]},
            [{"action": "accept", "type": "update", "data": diff["updates"][0]}],
            {},
        )
        self.assertEqual(updated["games"][0]["stability"], "Unstable")
        self.assertEqual(updated["games"][0]["url"], SPECIFIC_TUTORIAL_URL)

    def test_more_specific_tutorial_urls_remain_updates(self):
        specific_urls = (
            "https://archipelago.gg/tutorial/Another/setup/en",
            "https://archipelago.gg/tutorial/?game=Another",
            "https://archipelago.gg/tutorial/#another",
            "https://archipelago.gg/tutorial/;game=Another",
            "https://archipelago.gg/tutorials/",
            "https://archipelago.gg:8443/tutorial/",
            "http://archipelago.gg:443/tutorial/",
            "https://archipelago.gg.example.com/tutorial/",
        )
        for guide_url in specific_urls:
            for existing_url in (None, GENERIC_TUTORIAL_URL, SPECIFIC_TUTORIAL_URL):
                with self.subTest(guide_url=guide_url, existing_url=existing_url):
                    game = make_json_game(url=existing_url)
                    diff = merge_xlsx.build_diff(
                        [make_xlsx_game(game["name"], guide_url)], [game], {}
                    )

                    self.assertEqual(len(diff["updates"]), 1)
                    self.assertEqual(
                        diff["updates"][0]["changes"]["url"],
                        {"old": existing_url, "new": guide_url},
                    )

    def test_generic_url_check_does_not_fail_on_unrelated_malformed_links(self):
        self.assertFalse(
            merge_xlsx.is_generic_tutorial_url("https://[archipelago.gg/tutorial/")
        )

    def test_generic_url_check_rejects_similar_domains(self):
        self.assertFalse(
            merge_xlsx.is_generic_tutorial_url("https://arch\u0131pelago.gg/tutorial/")
        )

    def test_discord_and_github_update_rules_are_unchanged(self):
        discord_url = "https://discord.com/new"
        game = make_json_game()
        game["discordUrl"] = "https://discord.com/old"
        diff = merge_xlsx.build_diff(
            [make_xlsx_game(game["name"], discord_url)], [game], {}
        )
        self.assertEqual(
            diff["updates"][0]["changes"]["discordUrl"],
            {"old": "https://discord.com/old", "new": discord_url},
        )

        github_url = "https://github.com/example/setup"
        for current in (None, "https://github.com/example/release"):
            with self.subTest(current=current):
                game = make_json_game()
                game["githubUrl"] = current
                diff = merge_xlsx.build_diff(
                    [make_xlsx_game(game["name"], github_url)], [game], {}
                )
                if current:
                    self.assertEqual(diff["updates"], [])
                else:
                    self.assertEqual(
                        diff["updates"][0]["changes"]["githubUrl"],
                        {"old": None, "new": github_url},
                    )

    def test_new_game_keeps_generic_tutorial_url(self):
        diff = merge_xlsx.build_diff(
            [make_xlsx_game("New Game", GENERIC_TUTORIAL_URL)], [], {}
        )
        self.assertEqual(len(diff["new_games"]), 1)

        updated, _ = merge_xlsx.apply_changes(
            {"games": []},
            [{"action": "accept", "type": "new", "data": diff["new_games"][0]}],
            {},
        )
        self.assertEqual(updated["games"][0]["url"], GENERIC_TUTORIAL_URL)

    def test_manual_mapping_ignores_generic_url_and_keeps_other_changes(self):
        for existing_url in (SPECIFIC_TUTORIAL_URL, None):
            with self.subTest(existing_url=existing_url):
                game = make_json_game(url=existing_url)
                xlsx_game = make_xlsx_game("Another Name", GENERIC_TUTORIAL_URL, "Unstable")
                diff = merge_xlsx.build_diff([xlsx_game], [game], {})
                self.assertEqual(len(diff["new_games"]), 1)

                updated, mappings = merge_xlsx.apply_changes(
                    {"games": [game]},
                    [{
                        "action": "map",
                        "type": "new",
                        "data": diff["new_games"][0],
                        "mapToId": game["id"],
                    }],
                    {},
                )

                self.assertEqual(updated["games"][0]["url"], existing_url)
                self.assertEqual(updated["games"][0]["stability"], "Unstable")
                self.assertEqual(mappings, {"Another Name": game["id"]})

    def test_manual_mapping_still_fills_a_missing_specific_url(self):
        game = make_json_game(url=None)
        diff = merge_xlsx.build_diff(
            [make_xlsx_game("Another Name", SPECIFIC_TUTORIAL_URL)], [game], {}
        )
        updated, _ = merge_xlsx.apply_changes(
            {"games": [game]},
            [{
                "action": "map",
                "type": "new",
                "data": diff["new_games"][0],
                "mapToId": game["id"],
            }],
            {},
        )
        self.assertEqual(updated["games"][0]["url"], SPECIFIC_TUTORIAL_URL)

    def test_xlsx_review_and_save_preserve_specific_urls(self):
        new_specific_url = "https://archipelago.gg/tutorial/Another/setup/en"
        rows = (
            ("Generic Only", "Stable", GENERIC_TUTORIAL_URL),
            ("Stability Change", "Unstable", GENERIC_TUTORIAL_URL),
            ("Specific Change", "Stable", new_specific_url),
        )
        games_data = {"games": [make_json_game(name) for name, _, _ in rows]}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            workbook_path = temp_path / "games.xlsx"
            games_path = temp_path / "games.json"
            mappings_path = temp_path / "mappings.json"

            workbook = Workbook()
            sheet = workbook.active
            sheet.append(["Game", "Stability", "Setup Guide"])
            for name, stability, guide_url in rows:
                sheet.append([name, stability, "Setup"])
                sheet.cell(row=sheet.max_row, column=3).hyperlink = guide_url
            workbook.save(workbook_path)
            workbook.close()
            games_path.write_text(json.dumps(games_data), encoding="utf-8")

            xlsx_games, unknown_links = merge_xlsx.parse_xlsx(str(workbook_path))
            diff = merge_xlsx.build_diff(xlsx_games, games_data["games"], {})
            diff["unknown_links"] = unknown_links
            self.assertEqual(unknown_links, [])
            self.assertEqual(len(diff["matched"]), 1)
            self.assertEqual(len(diff["updates"]), 2)

            with (
                patch.object(merge_xlsx, "MAPPINGS_PATH", str(mappings_path)),
                patch.object(merge_xlsx.Handler, "games_json_path", str(games_path)),
                patch.object(merge_xlsx.Handler, "diff_data", diff),
            ):
                server = HTTPServer(("127.0.0.1", 0), merge_xlsx.Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    base_url = f"http://127.0.0.1:{server.server_port}"
                    with urlopen(base_url, timeout=5) as response:
                        html = response.read().decode("utf-8")
                    ui_diff = json.loads(
                        html.split("const DIFF = ", 1)[1].split(";\n", 1)[0]
                    )
                    self.assertEqual(ui_diff["updates"], diff["updates"])

                    decisions = [
                        {"action": "accept", "type": "update", "data": entry}
                        for entry in ui_diff["updates"]
                    ]
                    request = Request(
                        f"{base_url}/save",
                        data=json.dumps(decisions).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    with urlopen(request, timeout=5) as response:
                        self.assertEqual(json.load(response)["applied"], 2)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)

            saved_games = {
                game["name"]: game
                for game in json.loads(games_path.read_text(encoding="utf-8"))["games"]
            }
            self.assertEqual(saved_games["Generic Only"]["url"], SPECIFIC_TUTORIAL_URL)
            self.assertEqual(saved_games["Stability Change"]["url"], SPECIFIC_TUTORIAL_URL)
            self.assertEqual(saved_games["Stability Change"]["stability"], "Unstable")
            self.assertEqual(saved_games["Specific Change"]["url"], new_specific_url)


if __name__ == "__main__":
    unittest.main()
