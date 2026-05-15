from __future__ import annotations

from typing import cast

EXPORT_ROOT_KEYS = frozenset({"campagne", "personnage", "quete", "participation"})

_CAMPAIGNE_FIELDS = frozenset({"id", "nom", "maitre_du_jeu", "date_creation"})
_PERSONNAGE_FIELDS = frozenset(
    {"id", "nom", "classe", "niveau", "points_de_vie", "id_campagne"}
)
_QUETE_FIELDS = frozenset({"id", "titre", "description", "statut", "id_campagne"})
_PARTICIPATION_FIELDS = frozenset({"id_personnage", "id_quete"})


class JdrImportValidationError(ValueError):
    pass


def _is_int(value: object) -> bool:
    return type(value) is int


def _require_str(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JdrImportValidationError(f"{label}: expected a non-empty string.")
    return value


def _require_int(value: object, label: str) -> int:
    if not _is_int(value):
        raise JdrImportValidationError(f"{label}: expected an integer.")
    return cast(int, value)


def _require_row_dict(
    row: object, table: str, index: int, fields: frozenset[str]
) -> dict[str, object]:
    if not isinstance(row, dict):
        raise JdrImportValidationError(
            f"{table}[{index}]: expected an object, got {type(row).__name__}."
        )
    keys = frozenset(row.keys())
    if keys != fields:
        missing = fields - keys
        extra = keys - fields
        parts: list[str] = []
        if missing:
            parts.append(f"missing {sorted(missing)}")
        if extra:
            parts.append(f"unexpected {sorted(extra)}")
        raise JdrImportValidationError(f"{table}[{index}]: {', '.join(parts)}.")
    return row


def validate_jdr_export_payload(data: object) -> dict[str, list[dict[str, object]]]:
    if not isinstance(data, dict):
        raise JdrImportValidationError("Root value must be a JSON object.")

    keys = frozenset(data.keys())
    if keys != EXPORT_ROOT_KEYS:
        missing = EXPORT_ROOT_KEYS - keys
        extra = keys - EXPORT_ROOT_KEYS
        parts: list[str] = []
        if missing:
            parts.append(f"missing keys {sorted(missing)}")
        if extra:
            parts.append(f"unexpected keys {sorted(extra)}")
        raise JdrImportValidationError(f"Invalid root keys: {', '.join(parts)}.")

    out: dict[str, list[dict[str, object]]] = {}
    for table in sorted(EXPORT_ROOT_KEYS):
        rows = data[table]
        if not isinstance(rows, list):
            raise JdrImportValidationError(f"{table}: expected an array.")
        parsed: list[dict[str, object]] = []
        for i, row in enumerate(rows):
            parsed.append(_parse_row(table, row, i))
        out[table] = parsed

    _validate_referential_integrity(out)
    return out


def _parse_row(table: str, row: object, index: int) -> dict[str, object]:
    if table == "campagne":
        d = _require_row_dict(row, table, index, _CAMPAIGNE_FIELDS)
        cid = _require_int(d["id"], f"{table}[{index}].id")
        if cid <= 0:
            raise JdrImportValidationError(f"{table}[{index}].id: must be positive.")
        nom = _require_str(d["nom"], f"{table}[{index}].nom")
        mj = _require_str(d["maitre_du_jeu"], f"{table}[{index}].maitre_du_jeu")
        dc = d["date_creation"]
        if not isinstance(dc, (str, int, float)) and dc is not None:
            raise JdrImportValidationError(
                f"{table}[{index}].date_creation: expected a string or number."
            )
        return {
            "id": cid,
            "nom": nom,
            "maitre_du_jeu": mj,
            "date_creation": dc,
        }

    if table == "personnage":
        d = _require_row_dict(row, table, index, _PERSONNAGE_FIELDS)
        pid = _require_int(d["id"], f"{table}[{index}].id")
        if pid <= 0:
            raise JdrImportValidationError(f"{table}[{index}].id: must be positive.")
        cid = _require_int(d["id_campagne"], f"{table}[{index}].id_campagne")
        if cid <= 0:
            raise JdrImportValidationError(
                f"{table}[{index}].id_campagne: must be positive."
            )
        niveau = _require_int(d["niveau"], f"{table}[{index}].niveau")
        pv = _require_int(d["points_de_vie"], f"{table}[{index}].points_de_vie")
        return {
            "id": pid,
            "nom": _require_str(d["nom"], f"{table}[{index}].nom"),
            "classe": _require_str(d["classe"], f"{table}[{index}].classe"),
            "niveau": niveau,
            "points_de_vie": pv,
            "id_campagne": cid,
        }

    if table == "quete":
        d = _require_row_dict(row, table, index, _QUETE_FIELDS)
        qid = _require_int(d["id"], f"{table}[{index}].id")
        if qid <= 0:
            raise JdrImportValidationError(f"{table}[{index}].id: must be positive.")
        cid = _require_int(d["id_campagne"], f"{table}[{index}].id_campagne")
        if cid <= 0:
            raise JdrImportValidationError(
                f"{table}[{index}].id_campagne: must be positive."
            )
        return {
            "id": qid,
            "titre": _require_str(d["titre"], f"{table}[{index}].titre"),
            "description": _require_str(d["description"], f"{table}[{index}].description"),
            "statut": _require_str(d["statut"], f"{table}[{index}].statut"),
            "id_campagne": cid,
        }

    d = _require_row_dict(row, table, index, _PARTICIPATION_FIELDS)
    pid = _require_int(d["id_personnage"], f"{table}[{index}].id_personnage")
    qid = _require_int(d["id_quete"], f"{table}[{index}].id_quete")
    if pid <= 0 or qid <= 0:
        raise JdrImportValidationError(f"{table}[{index}]: ids must be positive.")
    return {"id_personnage": pid, "id_quete": qid}


def _validate_referential_integrity(data: dict[str, list[dict[str, object]]]) -> None:
    campagnes = data["campagne"]
    personnages = data["personnage"]
    quetes = data["quete"]
    participations = data["participation"]

    campagne_ids: set[int] = set()
    seen_nom_mj: set[tuple[object, object]] = set()
    for i, row in enumerate(campagnes):
        cid = row["id"]
        assert isinstance(cid, int)
        if cid in campagne_ids:
            raise JdrImportValidationError(f"campagne[{i}].id: duplicate id {cid}.")
        campagne_ids.add(cid)
        key = (row["nom"], row["maitre_du_jeu"])
        if key in seen_nom_mj:
            raise JdrImportValidationError(
                f"campagne[{i}]: duplicate (nom, maitre_du_jeu)."
            )
        seen_nom_mj.add(key)

    personnage_ids: set[int] = set()
    seen_pers: set[tuple[object, object, int]] = set()
    for i, row in enumerate(personnages):
        pid = row["id"]
        assert isinstance(pid, int)
        if pid in personnage_ids:
            raise JdrImportValidationError(f"personnage[{i}].id: duplicate id {pid}.")
        personnage_ids.add(pid)
        cid = row["id_campagne"]
        assert isinstance(cid, int)
        if cid not in campagne_ids:
            raise JdrImportValidationError(
                f"personnage[{i}].id_campagne: unknown campaign id {cid}."
            )
        ukey = (row["nom"], row["classe"], cid)
        if ukey in seen_pers:
            raise JdrImportValidationError(
                f"personnage[{i}]: duplicate (nom, classe, id_campagne)."
            )
        seen_pers.add(ukey)

    quete_ids: set[int] = set()
    seen_quete: set[tuple[object, int]] = set()
    for i, row in enumerate(quetes):
        qid = row["id"]
        assert isinstance(qid, int)
        if qid in quete_ids:
            raise JdrImportValidationError(f"quete[{i}].id: duplicate id {qid}.")
        quete_ids.add(qid)
        cid = row["id_campagne"]
        assert isinstance(cid, int)
        if cid not in campagne_ids:
            raise JdrImportValidationError(
                f"quete[{i}].id_campagne: unknown campaign id {cid}."
            )
        ukey = (row["titre"], cid)
        if ukey in seen_quete:
            raise JdrImportValidationError(
                f"quete[{i}]: duplicate (titre, id_campagne)."
            )
        seen_quete.add(ukey)

    seen_part: set[tuple[int, int]] = set()
    for i, row in enumerate(participations):
        pid = row["id_personnage"]
        qid = row["id_quete"]
        assert isinstance(pid, int) and isinstance(qid, int)
        if pid not in personnage_ids:
            raise JdrImportValidationError(
                f"participation[{i}].id_personnage: unknown character id {pid}."
            )
        if qid not in quete_ids:
            raise JdrImportValidationError(
                f"participation[{i}].id_quete: unknown quest id {qid}."
            )
        key = (pid, qid)
        if key in seen_part:
            raise JdrImportValidationError(
                f"participation[{i}]: duplicate (id_personnage, id_quete)."
            )
        seen_part.add(key)
