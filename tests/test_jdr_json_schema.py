from __future__ import annotations

import unittest

from database.jdr_json_schema import JdrImportValidationError, validate_jdr_export_payload


def _valid_payload() -> dict[str, list[dict[str, object]]]:
    return {
        "campagne": [
            {
                "id": 1,
                "nom": "The Mines",
                "maitre_du_jeu": "Alice",
                "date_creation": "2026-01-01 12:00:00",
            }
        ],
        "personnage": [
            {
                "id": 10,
                "nom": "Lia",
                "classe": "Mage",
                "niveau": 3,
                "points_de_vie": 18,
                "id_campagne": 1,
            }
        ],
        "quete": [
            {
                "id": 20,
                "titre": "Find relic",
                "description": "Go north",
                "statut": "open",
                "id_campagne": 1,
            }
        ],
        "participation": [{"id_personnage": 10, "id_quete": 20}],
    }


class ValidateExportPayloadTests(unittest.TestCase):
    def test_accepts_valid_payload(self) -> None:
        parsed = validate_jdr_export_payload(_valid_payload())
        self.assertEqual(parsed["campagne"][0]["nom"], "The Mines")
        self.assertEqual(parsed["personnage"][0]["id"], 10)

    def test_rejects_non_dict_root(self) -> None:
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload([])
        self.assertIn("Root value must be a JSON object", str(ctx.exception))

    def test_rejects_missing_root_keys(self) -> None:
        payload = _valid_payload()
        del payload["participation"]
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("Invalid root keys", str(ctx.exception))

    def test_rejects_extra_root_keys(self) -> None:
        payload = _valid_payload()
        payload["extra"] = []
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("Invalid root keys", str(ctx.exception))

    def test_rejects_wrong_row_shape(self) -> None:
        payload = _valid_payload()
        payload["campagne"][0] = {"id": 1}
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("campagne[0]", str(ctx.exception))

    def test_rejects_zero_or_negative_ids(self) -> None:
        payload = _valid_payload()
        payload["quete"][0]["id"] = 0
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("must be positive", str(ctx.exception))

    def test_rejects_bool_for_int_fields(self) -> None:
        payload = _valid_payload()
        payload["personnage"][0]["niveau"] = True
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("expected an integer", str(ctx.exception))

    def test_rejects_duplicate_campaign_id(self) -> None:
        payload = _valid_payload()
        payload["campagne"].append(
            {
                "id": 1,
                "nom": "Another",
                "maitre_du_jeu": "Bob",
                "date_creation": "2026-02-01 00:00:00",
            }
        )
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("duplicate id", str(ctx.exception))

    def test_rejects_duplicate_campaign_nom_mj(self) -> None:
        payload = _valid_payload()
        payload["campagne"].append(
            {
                "id": 2,
                "nom": "The Mines",
                "maitre_du_jeu": "Alice",
                "date_creation": "2026-02-01 00:00:00",
            }
        )
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("duplicate (nom, maitre_du_jeu)", str(ctx.exception))

    def test_rejects_unknown_foreign_keys(self) -> None:
        payload = _valid_payload()
        payload["personnage"][0]["id_campagne"] = 999
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("unknown campaign id", str(ctx.exception))

    def test_rejects_duplicate_participation_pair(self) -> None:
        payload = _valid_payload()
        payload["participation"].append({"id_personnage": 10, "id_quete": 20})
        with self.assertRaises(JdrImportValidationError) as ctx:
            validate_jdr_export_payload(payload)
        self.assertIn("duplicate (id_personnage, id_quete)", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
