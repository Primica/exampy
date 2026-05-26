from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import shell.commands as commands


class _CampaignRow:
    def __init__(self, cid: int, nom: str, mj: str, created: str = "2026-01-01") -> None:
        self.id = cid
        self.nom = nom
        self.maitre_du_jeu = mj
        self.date_creation = created


class _CharacterCampaignRow:
    def __init__(
        self,
        pid: int,
        nom: str,
        classe: str,
        niveau: int,
        points_de_vie: int,
        id_campagne: int,
        nom_campagne: str,
    ) -> None:
        self.id = pid
        self.nom = nom
        self.classe = classe
        self.niveau = niveau
        self.points_de_vie = points_de_vie
        self.id_campagne = id_campagne
        self.nom_campagne = nom_campagne


class _QuestRow:
    def __init__(self, qid: int, titre: str, description: str, statut: str, id_campagne: int) -> None:
        self.id = qid
        self.titre = titre
        self.description = description
        self.statut = statut
        self.id_campagne = id_campagne


class _CharacterQuestRow:
    def __init__(self, pid: int, nom: str, classe: str, niveau: int, points_de_vie: int) -> None:
        self.id = pid
        self.nom = nom
        self.classe = classe
        self.niveau = niveau
        self.points_de_vie = points_de_vie


class _QuestCharacterRow:
    def __init__(self, qid: int, titre: str, statut: str, id_campagne: int) -> None:
        self.id = qid
        self.titre = titre
        self.statut = statut
        self.id_campagne = id_campagne


class FakeRepo:
    def __init__(self) -> None:
        self.find_map: dict[str, list[tuple[int, str]]] = {}
        self.created_campaigns: list[tuple[str, str]] = []
        self.created_characters: list[tuple[str, str, int, int, int]] = []
        self.created_quests: list[tuple[str, str, str, int]] = []
        self.participations: list[tuple[int, int]] = []

    def find_campagnes_by_nom_exact(self, nom: str) -> list[tuple[int, str]]:
        return self.find_map.get(nom, [])

    def create_campagne(self, nom: str, mj: str) -> int:
        self.created_campaigns.append((nom, mj))
        return 101

    def add_personnage(
        self, nom: str, classe: str, niveau: int, points_de_vie: int, id_campagne: int
    ) -> int:
        self.created_characters.append((nom, classe, niveau, points_de_vie, id_campagne))
        return 202

    def create_quete(self, titre: str, description: str, statut: str, id_campagne: int) -> int:
        self.created_quests.append((titre, description, statut, id_campagne))
        return 303

    def inscrire_participation(self, id_personnage: int, id_quete: int) -> None:
        self.participations.append((id_personnage, id_quete))


class FakeLists:
    def __init__(self) -> None:
        self.export_payload: dict[str, Any] = {
            "campagne": [],
            "personnage": [],
            "quete": [],
            "participation": [],
        }
        self.import_counts: dict[str, int] = {
            "campagne": 1,
            "personnage": 2,
            "quete": 3,
            "participation": 4,
        }
        self.received_import_payload: Any = None
        self.campaign_rows = [_CampaignRow(1, "World", "Alice")]
        self.characters_by_campaign = [_CharacterCampaignRow(10, "Lia", "Mage", 3, 18, 1, "World")]
        self.quests_by_campaign = [_QuestRow(20, "Find relic", "Go north", "open", 1)]
        self.characters_by_quest = [_CharacterQuestRow(10, "Lia", "Mage", 3, 18)]
        self.quests_by_character = [_QuestCharacterRow(20, "Find relic", "open", 1)]

    def export_database_as_dicts(self) -> dict[str, Any]:
        return self.export_payload

    def import_database_from_dicts(self, data: Any) -> dict[str, int]:
        self.received_import_payload = data
        return self.import_counts

    def list_toutes_campagnes(self) -> list[_CampaignRow]:
        return self.campaign_rows

    def list_personnages_par_campagne(self, _id_campagne: int) -> list[_CharacterCampaignRow]:
        return self.characters_by_campaign

    def list_quetes_par_campagne(self, _id_campagne: int) -> list[_QuestRow]:
        return self.quests_by_campaign

    def list_personnages_par_quete(self, _id_quete: int) -> list[_CharacterQuestRow]:
        return self.characters_by_quest

    def list_quetes_par_personnage(self, _id_personnage: int) -> list[_QuestCharacterRow]:
        return self.quests_by_character


class DispatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = FakeRepo()
        self.lists = FakeLists()

    def _dispatch_with_output(self, tokens: list[str]) -> tuple[bool, str]:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            keep_running = commands.dispatch(self.repo, self.lists, tokens)
        return keep_running, buf.getvalue()

    def test_empty_tokens_keep_shell_running(self) -> None:
        keep_running, out = self._dispatch_with_output([])
        self.assertTrue(keep_running)
        self.assertEqual(out, "")

    def test_exit_stops_shell(self) -> None:
        keep_running, _ = self._dispatch_with_output(["exit"])
        self.assertFalse(keep_running)

    def test_help_prints_help_text(self) -> None:
        keep_running, out = self._dispatch_with_output(["help"])
        self.assertTrue(keep_running)
        self.assertIn("Commands (domain order", out)

    def test_clear_with_extra_tokens_prints_usage(self) -> None:
        keep_running, out = self._dispatch_with_output(["clear", "oops"])
        self.assertTrue(keep_running)
        self.assertIn("Usage: clear", out)

    def test_unknown_command_prints_error(self) -> None:
        keep_running, out = self._dispatch_with_output(["wat"])
        self.assertTrue(keep_running)
        self.assertIn("Unknown command", out)

    def test_export_stdout_prints_json(self) -> None:
        keep_running, out = self._dispatch_with_output(["export"])
        self.assertTrue(keep_running)
        parsed = json.loads(out)
        self.assertEqual(parsed, self.lists.export_payload)

    def test_export_to_path_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "nested" / "export.json"
            keep_running, out = self._dispatch_with_output(["export", str(out_file)])
            self.assertTrue(keep_running)
            self.assertTrue(out_file.is_file())
            self.assertIn("Exported to", out)

    def test_export_with_too_many_args_prints_usage(self) -> None:
        keep_running, out = self._dispatch_with_output(["export", "a", "b"])
        self.assertTrue(keep_running)
        self.assertIn("Usage: export [path]", out)

    def test_import_reads_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            in_file = Path(tmpdir) / "input.json"
            payload = {
                "campagne": [],
                "personnage": [],
                "quete": [],
                "participation": [],
            }
            in_file.write_text(json.dumps(payload), encoding="utf-8")
            keep_running, out = self._dispatch_with_output(["import", str(in_file)])
            self.assertTrue(keep_running)
            self.assertEqual(self.lists.received_import_payload, payload)
            self.assertIn("Import complete", out)

    def test_import_missing_file(self) -> None:
        keep_running, out = self._dispatch_with_output(["import", "nope.json"])
        self.assertTrue(keep_running)
        self.assertIn("File not found", out)

    def test_import_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            in_file = Path(tmpdir) / "broken.json"
            in_file.write_text("{not json", encoding="utf-8")
            keep_running, out = self._dispatch_with_output(["import", str(in_file)])
            self.assertTrue(keep_running)
            self.assertIn("Invalid JSON", out)

    def test_campaign_list_outputs_table(self) -> None:
        keep_running, out = self._dispatch_with_output(["campaign", "list"])
        self.assertTrue(keep_running)
        self.assertIn("dungeon_master", out)
        self.assertIn("World", out)

    def test_character_list_resolves_campaign_by_id(self) -> None:
        keep_running, out = self._dispatch_with_output(["character", "list", "1"])
        self.assertTrue(keep_running)
        self.assertIn("campaign_id", out)
        self.assertIn("Lia", out)

    def test_character_list_campaign_not_found(self) -> None:
        keep_running, out = self._dispatch_with_output(["character", "list", "Unknown"])
        self.assertTrue(keep_running)
        self.assertIn("No campaign named", out)

    def test_character_list_with_ambiguous_campaign_and_prompt_choice(self) -> None:
        self.repo.find_map["World"] = [(1, "Alice"), (2, "Bob")]
        with patch("shell.commands._prompt_line", side_effect=["2"]):
            keep_running, out = self._dispatch_with_output(["character", "list", "World"])
        self.assertTrue(keep_running)
        self.assertIn("Multiple campaigns named", out)
        self.assertIn("dungeon master: Alice", out)

    def test_character_list_with_invalid_ambiguous_choice_then_valid(self) -> None:
        self.repo.find_map["World"] = [(1, "Alice"), (2, "Bob")]
        with patch("shell.commands._prompt_line", side_effect=["99", "Bob"]):
            keep_running, out = self._dispatch_with_output(["character", "list", "World"])
        self.assertTrue(keep_running)
        self.assertIn("Invalid number", out)

    def test_character_quests_with_non_integer_argument(self) -> None:
        keep_running, out = self._dispatch_with_output(["character", "quests", "abc"])
        self.assertTrue(keep_running)
        self.assertIn("character_id must be an integer", out)

    def test_quest_characters_with_non_integer_argument(self) -> None:
        keep_running, out = self._dispatch_with_output(["quest", "characters", "abc"])
        self.assertTrue(keep_running)
        self.assertIn("quest_id must be an integer", out)

    def test_campaign_create_calls_repo(self) -> None:
        keep_running, out = self._dispatch_with_output(["campaign", "create", "The", "Alice"])
        self.assertTrue(keep_running)
        self.assertEqual(self.repo.created_campaigns, [("The", "Alice")])
        self.assertIn("Campaign created, id = 101", out)

    def test_character_add_calls_repo(self) -> None:
        keep_running, out = self._dispatch_with_output(
            ["character", "add", "Lia", "Mage", "3", "18", "1"]
        )
        self.assertTrue(keep_running)
        self.assertEqual(self.repo.created_characters, [("Lia", "Mage", 3, 18, 1)])
        self.assertIn("Character created, id = 202", out)

    def test_character_add_rejects_non_integer_numbers(self) -> None:
        keep_running, out = self._dispatch_with_output(
            ["character", "add", "Lia", "Mage", "x", "18", "1"]
        )
        self.assertTrue(keep_running)
        self.assertIn("level and hit_points must be integers", out)

    def test_quest_create_calls_repo(self) -> None:
        keep_running, out = self._dispatch_with_output(
            ["quest", "create", "Find relic", "Go north", "open", "1"]
        )
        self.assertTrue(keep_running)
        self.assertEqual(self.repo.created_quests, [("Find relic", "Go north", "open", 1)])
        self.assertIn("Quest created, id = 303", out)

    def test_participation_add_calls_repo(self) -> None:
        keep_running, out = self._dispatch_with_output(["participation", "add", "10", "20"])
        self.assertTrue(keep_running)
        self.assertEqual(self.repo.participations, [(10, 20)])
        self.assertIn("Participation recorded", out)

    def test_participation_add_rejects_non_integer(self) -> None:
        keep_running, out = self._dispatch_with_output(["participation", "add", "foo", "20"])
        self.assertTrue(keep_running)
        self.assertIn("character_id and quest_id must be integers", out)

    def test_ensure_command_tokens_prompts_for_missing_values(self) -> None:
        with patch("shell.commands._prompt_non_empty", side_effect=["A", "B"]):
            completed = commands._ensure_campaign_create(["campaign", "create"])
        self.assertEqual(completed, ["campaign", "create", "A", "B"])

    def test_ensure_command_tokens_uses_int_prompt(self) -> None:
        with patch("shell.commands._prompt_int", side_effect=[7, 42]):
            completed = commands._ensure_participation_add(["participation", "add"])
        self.assertEqual(completed, ["participation", "add", "7", "42"])

    def test_parse_int_arg_returns_none_and_prints_usage(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            value = commands._parse_int_arg("abc", "need int")
        self.assertIsNone(value)
        self.assertIn("need int", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
