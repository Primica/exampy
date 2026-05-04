"""Commandes du shell JDR (écriture + listes)."""

from __future__ import annotations

import mysql.connector
from tabulate import tabulate

from database import JdrListRepository, JdrRepository

HELP_TEXT = """
Commandes (ordre métier : campagne → personnage / quête → participation) :

  Tab : complétion (sous-commandes, libellés et ids issus de la base).

  help
  exit | quit

  Écriture :
  campagne create <nom> <maitre_du_jeu>
  personnage add <nom> <classe> <niveau> <points_de_vie> <id_campagne>
  quete create <titre> <description> <statut> <id_campagne>
  participation add <id_personnage> <id_quete>

  Listes :
  campagne list
  personnage list <id_campagne>
  quete list <id_campagne>
  quete personnages <id_quete>
  personnage quetes <id_personnage>

Utilisez des guillemets pour les libellés contenant des espaces, par ex. :
  campagne create "Les mines" "Alice"
  quete create "Première quête" "Aller au nord." ouverte 1
""".strip()


def _usage(msg: str) -> None:
    print(msg)


def _print_table(headers: list[str], rows: list[list[object]]) -> None:
    if not rows:
        print("(aucun résultat)")
        return
    print(tabulate(rows, headers=headers, tablefmt="github"))


def dispatch(repo: JdrRepository, lists: JdrListRepository, tokens: list[str]) -> bool:
    """Exécute une commande. Retourne False pour arrêter le shell."""
    if not tokens:
        return True

    root = tokens[0].lower()
    if root in ("exit", "quit"):
        return False
    if root == "help":
        print(HELP_TEXT)
        return True

    try:
        if root == "campagne" and len(tokens) >= 2 and tokens[1].lower() == "list":
            if len(tokens) != 2:
                _usage("Usage : campagne list")
                return True
            data = lists.list_toutes_campagnes()
            _print_table(
                ["id", "nom", "maître du jeu", "création"],
                [[c.id, c.nom, c.maitre_du_jeu, c.date_creation] for c in data],
            )
            return True

        if root == "personnage" and len(tokens) >= 2 and tokens[1].lower() == "list":
            if len(tokens) != 3:
                _usage("Usage : personnage list <id_campagne>")
                return True
            try:
                id_c = int(tokens[2])
            except ValueError:
                _usage("id_campagne doit être un entier.")
                return True
            data = lists.list_personnages_par_campagne(id_c)
            _print_table(
                [
                    "id",
                    "nom",
                    "classe",
                    "niveau",
                    "PV",
                    "id_campagne",
                    "campagne",
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

        if root == "personnage" and len(tokens) >= 2 and tokens[1].lower() == "quetes":
            if len(tokens) != 3:
                _usage("Usage : personnage quetes <id_personnage>")
                return True
            try:
                id_p = int(tokens[2])
            except ValueError:
                _usage("id_personnage doit être un entier.")
                return True
            data = lists.list_quetes_par_personnage(id_p)
            _print_table(
                ["id", "titre", "statut", "id_campagne"],
                [[q.id, q.titre, q.statut, q.id_campagne] for q in data],
            )
            return True

        if root == "quete" and len(tokens) >= 2 and tokens[1].lower() == "list":
            if len(tokens) != 3:
                _usage("Usage : quete list <id_campagne>")
                return True
            try:
                id_c = int(tokens[2])
            except ValueError:
                _usage("id_campagne doit être un entier.")
                return True
            data = lists.list_quetes_par_campagne(id_c)
            _print_table(
                ["id", "titre", "description", "statut", "id_campagne"],
                [
                    [q.id, q.titre, q.description, q.statut, q.id_campagne]
                    for q in data
                ],
            )
            return True

        if root == "quete" and len(tokens) >= 2 and tokens[1].lower() == "personnages":
            if len(tokens) != 3:
                _usage("Usage : quete personnages <id_quete>")
                return True
            try:
                id_q = int(tokens[2])
            except ValueError:
                _usage("id_quete doit être un entier.")
                return True
            data = lists.list_personnages_par_quete(id_q)
            _print_table(
                ["id", "nom", "classe", "niveau", "PV"],
                [
                    [p.id, p.nom, p.classe, p.niveau, p.points_de_vie]
                    for p in data
                ],
            )
            return True

        if root == "campagne" and len(tokens) >= 2 and tokens[1].lower() == "create":
            if len(tokens) != 4:
                _usage("Usage : campagne create <nom> <maitre_du_jeu>")
                return True
            _, _, nom, mj = tokens
            cid = repo.create_campagne(nom, mj)
            print(f"Campagne créée, id = {cid}.")
            return True

        if root == "personnage" and len(tokens) >= 2 and tokens[1].lower() == "add":
            if len(tokens) != 7:
                _usage(
                    "Usage : personnage add <nom> <classe> <niveau> <points_de_vie> <id_campagne>"
                )
                return True
            _, _, nom, classe, niveau_s, pv_s, camp_s = tokens
            try:
                niveau = int(niveau_s)
                pv = int(pv_s)
                id_campagne = int(camp_s)
            except ValueError:
                _usage("niveau, points_de_vie et id_campagne doivent être des entiers.")
                return True
            pid = repo.add_personnage(nom, classe, niveau, pv, id_campagne)
            print(f"Personnage créé, id = {pid}.")
            return True

        if root == "quete" and len(tokens) >= 2 and tokens[1].lower() == "create":
            if len(tokens) != 6:
                _usage(
                    "Usage : quete create <titre> <description> <statut> <id_campagne>"
                )
                return True
            _, _, titre, description, statut, camp_s = tokens
            try:
                id_campagne = int(camp_s)
            except ValueError:
                _usage("id_campagne doit être un entier.")
                return True
            qid = repo.create_quete(titre, description, statut, id_campagne)
            print(f"Quête créée, id = {qid}.")
            return True

        if root == "participation" and len(tokens) >= 2 and tokens[1].lower() == "add":
            if len(tokens) != 4:
                _usage("Usage : participation add <id_personnage> <id_quete>")
                return True
            _, _, p_s, q_s = tokens
            try:
                id_p = int(p_s)
                id_q = int(q_s)
            except ValueError:
                _usage("id_personnage et id_quete doivent être des entiers.")
                return True
            repo.inscrire_participation(id_p, id_q)
            print("Participation enregistrée.")
            return True

    except mysql.connector.Error as err:
        print(f"Erreur SQL : {err}")
        return True
    except RuntimeError as err:
        print(f"Erreur : {err}")
        return True

    print(f"Commande inconnue : {tokens[0]!r}. Tapez help.")
    return True
