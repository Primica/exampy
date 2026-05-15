from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import mysql.connector
from tabulate import tabulate

from database import JdrImportValidationError, JdrListRepository, JdrRepository

HELP_TEXT = """
Commands (domain order: campaign → character / quest → participation):

  Tab: completion (subcommands, labels from the database).

  help
  exit | quit
  clear

  Writes:
  campaign create <name> <dungeon_master>
  character add <name> <class> <level> <hit_points> <campaign_name>
  quest create <title> <description> <status> <campaign_name>
  participation add <character_id> <quest_id>

  Lists:
  campaign list
  character list <campaign_name>
  quest list <campaign_name>
  quest characters <quest_id>
  character quests <character_id>

  export [path]
    Dump all tables to JSON (stdout if path is omitted).

  import <path>
    Replace all database rows with a JSON export file (schema validated first).

  Campaigns are picked by exact name; you may still pass a numeric campaign id.
  If several campaigns share the same name, you will be asked for the dungeon master.

Use quotes for values that contain spaces, e.g.:
  campaign create "The Mines" "Alice"
  quest create "First quest" "Go north." open "World"
""".strip()


def _usage(msg: str) -> None:
    print(msg)


def _prompt_line(label: str) -> str:
    return input(f"{label}: ").strip()


def _prompt_non_empty(label: str) -> str:
    while True:
        value = _prompt_line(label)
        if value:
            return value
        print("(Required value cannot be empty.)")


def _prompt_int(label: str) -> int:
    while True:
        raw = _prompt_line(label)
        try:
            return int(raw)
        except ValueError:
            print("Value must be an integer.")


def _resolve_campagne_id(repo: JdrRepository, raw: str) -> int | None:
    t = raw.strip()
    if t.isdigit():
        return int(t)
    matches = repo.find_campagnes_by_nom_exact(t)
    if not matches:
        print(f"No campaign named {t!r}.")
        return None
    if len(matches) == 1:
        return matches[0][0]
    print(f"Multiple campaigns named {t!r}:")
    for i, (_cid, mj) in enumerate(matches, 1):
        print(f"  {i}. dungeon master: {mj}")
    while True:
        choice = _prompt_line(
            f"Enter 1–{len(matches)} or the dungeon master name"
        ).strip()
        if choice.isdigit():
            n = int(choice)
            if 1 <= n <= len(matches):
                return matches[n - 1][0]
            print("Invalid number.")
            continue
        cl = choice.lower()
        dms = [m for m in matches if m[1].lower() == cl]
        if len(dms) == 1:
            return dms[0][0]
        print("Unknown or ambiguous dungeon master; try again.")


def _clear_screen() -> None:
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "cls"], check=False, capture_output=True)
    else:
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()


def _print_table(headers: list[str], rows: list[list[object]]) -> None:
    if not rows:
        print("(no rows)")
        return
    print(tabulate(rows, headers=headers, tablefmt="github"))


def _ensure_campaign_create(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 4:
        _usage("Usage: campaign create <name> <dungeon_master>")
        return None
    while len(t) < 4:
        if len(t) <= 2:
            t.append(_prompt_non_empty("Campaign name"))
        elif len(t) == 3:
            t.append(_prompt_non_empty("Dungeon master"))
    return t


def _ensure_character_add(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 7:
        _usage(
            "Usage: character add <name> <class> <level> <hit_points> <campaign_name>"
        )
        return None
    while len(t) < 7:
        if len(t) <= 2:
            t.append(_prompt_non_empty("Character name"))
        elif len(t) == 3:
            t.append(_prompt_non_empty("Class"))
        elif len(t) == 4:
            t.append(str(_prompt_int("Level")))
        elif len(t) == 5:
            t.append(str(_prompt_int("Hit points")))
        elif len(t) == 6:
            t.append(_prompt_non_empty("Campaign name or id"))
    return t


def _ensure_quest_create(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 6:
        _usage("Usage: quest create <title> <description> <status> <campaign_name>")
        return None
    while len(t) < 6:
        if len(t) <= 2:
            t.append(_prompt_non_empty("Quest title"))
        elif len(t) == 3:
            t.append(_prompt_non_empty("Description"))
        elif len(t) == 4:
            t.append(_prompt_non_empty("Status"))
        elif len(t) == 5:
            t.append(_prompt_non_empty("Campaign name or id"))
    return t


def _ensure_participation_add(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 4:
        _usage("Usage: participation add <character_id> <quest_id>")
        return None
    while len(t) < 4:
        if len(t) <= 2:
            t.append(str(_prompt_int("Character id")))
        elif len(t) == 3:
            t.append(str(_prompt_int("Quest id")))
    return t


def _ensure_character_list(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 3:
        _usage("Usage: character list <campaign_name>")
        return None
    while len(t) < 3:
        t.append(_prompt_non_empty("Campaign name or id"))
    return t


def _ensure_quest_list(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 3:
        _usage("Usage: quest list <campaign_name>")
        return None
    while len(t) < 3:
        t.append(_prompt_non_empty("Campaign name or id"))
    return t


def _ensure_character_quests(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 3:
        _usage("Usage: character quests <character_id>")
        return None
    while len(t) < 3:
        t.append(str(_prompt_int("Character id")))
    return t


def _ensure_quest_characters(tokens: list[str]) -> list[str] | None:
    t = list(tokens)
    if len(t) > 3:
        _usage("Usage: quest characters <quest_id>")
        return None
    while len(t) < 3:
        t.append(str(_prompt_int("Quest id")))
    return t


def dispatch(repo: JdrRepository, lists: JdrListRepository, tokens: list[str]) -> bool:
    if not tokens:
        return True

    root = tokens[0].lower()
    if root in ("exit", "quit"):
        return False
    if root == "help":
        print(HELP_TEXT)
        return True

    if root == "clear":
        if len(tokens) != 1:
            _usage("Usage: clear")
            return True
        _clear_screen()
        sys.stdout.flush()
        return True

    try:
        if root == "export":
            if len(tokens) > 2:
                _usage("Usage: export [path]")
                return True
            data = lists.export_database_as_dicts()
            text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            if len(tokens) == 1:
                print(text)
                return True
            out_path = Path(tokens[1]).expanduser()
            try:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(text, encoding="utf-8")
            except OSError as err:
                print(f"Could not write file: {err}")
                return True
            print(f"Exported to {out_path.resolve()}.")
            return True

        if root == "import":
            if len(tokens) != 2:
                _usage("Usage: import <path>")
                return True
            in_path = Path(tokens[1]).expanduser()
            if not in_path.is_file():
                print(f"File not found: {in_path}")
                return True
            try:
                raw = json.loads(in_path.read_text(encoding="utf-8"))
            except OSError as err:
                print(f"Could not read file: {err}")
                return True
            except json.JSONDecodeError as err:
                print(f"Invalid JSON: {err}")
                return True
            try:
                counts = lists.import_database_from_dicts(raw)
            except JdrImportValidationError as err:
                print(f"Invalid export schema: {err}")
                return True
            print(
                "Import complete: "
                f"{counts['campagne']} campaign(s), "
                f"{counts['personnage']} character(s), "
                f"{counts['quete']} quest(s), "
                f"{counts['participation']} participation(s)."
            )
            return True

        if root == "campaign" and len(tokens) >= 2 and tokens[1].lower() == "list":
            if len(tokens) != 2:
                _usage("Usage: campaign list")
                return True
            data = lists.list_toutes_campagnes()
            _print_table(
                ["id", "name", "dungeon_master", "created"],
                [[c.id, c.nom, c.maitre_du_jeu, c.date_creation] for c in data],
            )
            return True

        if root == "character" and len(tokens) >= 2 and tokens[1].lower() == "list":
            filled = _ensure_character_list(tokens)
            if filled is None:
                return True
            id_c = _resolve_campagne_id(repo, filled[2])
            if id_c is None:
                return True
            data = lists.list_personnages_par_campagne(id_c)
            _print_table(
                [
                    "id",
                    "name",
                    "class",
                    "level",
                    "HP",
                    "campaign_id",
                    "campaign",
                ],
                [
                    [
                        p.id,
                        p.nom,
                        p.classe,
                        p.niveau,
                        p.points_de_vie,
                        p.id_campagne,
                        p.nom_campagne,
                    ]
                    for p in data
                ],
            )
            return True

        if root == "character" and len(tokens) >= 2 and tokens[1].lower() == "quests":
            filled = _ensure_character_quests(tokens)
            if filled is None:
                return True
            try:
                id_p = int(filled[2])
            except ValueError:
                _usage("character_id must be an integer.")
                return True
            data = lists.list_quetes_par_personnage(id_p)
            _print_table(
                ["id", "title", "status", "campaign_id"],
                [[q.id, q.titre, q.statut, q.id_campagne] for q in data],
            )
            return True

        if root == "quest" and len(tokens) >= 2 and tokens[1].lower() == "list":
            filled = _ensure_quest_list(tokens)
            if filled is None:
                return True
            id_c = _resolve_campagne_id(repo, filled[2])
            if id_c is None:
                return True
            data = lists.list_quetes_par_campagne(id_c)
            _print_table(
                ["id", "title", "description", "status", "campaign_id"],
                [
                    [q.id, q.titre, q.description, q.statut, q.id_campagne]
                    for q in data
                ],
            )
            return True

        if root == "quest" and len(tokens) >= 2 and tokens[1].lower() == "characters":
            filled = _ensure_quest_characters(tokens)
            if filled is None:
                return True
            try:
                id_q = int(filled[2])
            except ValueError:
                _usage("quest_id must be an integer.")
                return True
            data = lists.list_personnages_par_quete(id_q)
            _print_table(
                ["id", "name", "class", "level", "HP"],
                [
                    [p.id, p.nom, p.classe, p.niveau, p.points_de_vie]
                    for p in data
                ],
            )
            return True

        if root == "campaign" and len(tokens) >= 2 and tokens[1].lower() == "create":
            filled = _ensure_campaign_create(tokens)
            if filled is None:
                return True
            _, _, nom, mj = filled
            cid = repo.create_campagne(nom, mj)
            print(f"Campaign created, id = {cid}.")
            return True

        if root == "character" and len(tokens) >= 2 and tokens[1].lower() == "add":
            filled = _ensure_character_add(tokens)
            if filled is None:
                return True
            _, _, nom, classe, niveau_s, pv_s, camp_s = filled
            try:
                niveau = int(niveau_s)
                pv = int(pv_s)
            except ValueError:
                _usage("level and hit_points must be integers.")
                return True
            id_campagne = _resolve_campagne_id(repo, camp_s)
            if id_campagne is None:
                return True
            pid = repo.add_personnage(nom, classe, niveau, pv, id_campagne)
            print(f"Character created, id = {pid}.")
            return True

        if root == "quest" and len(tokens) >= 2 and tokens[1].lower() == "create":
            filled = _ensure_quest_create(tokens)
            if filled is None:
                return True
            _, _, titre, description, statut, camp_s = filled
            id_campagne = _resolve_campagne_id(repo, camp_s)
            if id_campagne is None:
                return True
            qid = repo.create_quete(titre, description, statut, id_campagne)
            print(f"Quest created, id = {qid}.")
            return True

        if root == "participation" and len(tokens) >= 2 and tokens[1].lower() == "add":
            filled = _ensure_participation_add(tokens)
            if filled is None:
                return True
            _, _, p_s, q_s = filled
            try:
                id_p = int(p_s)
                id_q = int(q_s)
            except ValueError:
                _usage("character_id and quest_id must be integers.")
                return True
            repo.inscrire_participation(id_p, id_q)
            print("Participation recorded.")
            return True

    except mysql.connector.Error as err:
        print(f"SQL error: {err}")
        return True
    except RuntimeError as err:
        print(f"Error: {err}")
        return True

    print(f"Unknown command: {tokens[0]!r}. Type help.")
    return True
