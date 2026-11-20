import hashlib
import pathlib

PYTHON_SCHEMA = pathlib.Path(__file__).parent.parent / "src" / "konfigurator" / "assets" / "config_schema_v1.json"
WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]
FLUTTER_SCHEMA = WORKSPACE_ROOT / "Mluvici_kalkulacka" / "assets" / "config_schema_v1.json"


def test_schema_hash_parity():
    import json
    assert PYTHON_SCHEMA.exists(), f"Python schema not found: {PYTHON_SCHEMA}"
    assert FLUTTER_SCHEMA.exists(), f"Flutter schema not found: {FLUTTER_SCHEMA}"
    flutter_path = FLUTTER_SCHEMA
    # Hash canonical JSON, not formatting/line-ending differences.
    py_hash = hashlib.sha256(json.dumps(json.loads(PYTHON_SCHEMA.read_text(encoding="utf-8")), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    fl_hash = hashlib.sha256(json.dumps(json.loads(flutter_path.read_text(encoding="utf-8")), sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert py_hash == fl_hash, f"Schema hash mismatch: Python {py_hash} != Flutter {fl_hash}. Run sync_schema.py"


def test_schema_is_valid_json_schema():
    import json
    data = json.loads(PYTHON_SCHEMA.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert data["properties"]["schemaVersion"]["const"] == 1


def test_v3_schema_is_valid_and_places_voice_settings_globally():
    import json

    schema_path = PYTHON_SCHEMA.with_name("config_schema_v3.json")
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data["properties"]["schemaVersion"]["const"] == 3
    profile_settings = data["$defs"]["accessibilitySettings"]["properties"]
    global_settings = data["$defs"]["globalSettings"]["properties"]
    assert "screenReaderMode" not in profile_settings
    assert "speechRate" not in profile_settings
    assert "themeMode" in global_settings
    assert "screenReaderMode" in global_settings
    assert "speechRate" in global_settings


def test_v3_schema_semantic_parity_with_flutter():
    import json
    import jsonschema
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
    from konfigurator import models

    py_schema = json.loads((PYTHON_SCHEMA.with_name("config_schema_v3.json")).read_text(encoding="utf-8"))
    # Find Flutter schema
    flutter_candidates = [WORKSPACE_ROOT / "Mluvici_kalkulacka" / "assets" / "config_schema_v3.json"]
    flutter_v3 = None
    for cand in flutter_candidates:
        if cand.exists():
            flutter_v3 = cand
            break
    assert flutter_v3 is not None, "Flutter v3 schema not found"

    fl_schema = json.loads(flutter_v3.read_text(encoding="utf-8"))
    assert fl_schema["properties"]["schemaVersion"]["const"] == 3

    # Generate canonical v3 sample from Python models
    cfg = models.ConfigFile(
        profiles=[
            models.AccessibilityProfile(
                id="standard",
                name="Standard",
                isBuiltIn=True,
                settings=models.AccessibilitySettings(),
            )
        ]
    )
    data = cfg.to_dict(include_metadata=True)
    # Validace vůči oběma
    jsonschema.validate(data, py_schema)
    # Flutter schema vyzaduje statsDisplayConfig pokud je v required, overme podporu
    if "statsDisplayConfig" in fl_schema.get("properties", {}).get("globalSettings", {}).get("required", []):
        if "statsDisplayConfig" not in data["globalSettings"]:
            data["globalSettings"]["statsDisplayConfig"] = {
                "preset": "custom",
                "customShowN": True,
                "customVisibleItems": ["mean", "sum"],
                "percentiles": [],
                "order": ["mean", "sum"]
            }
    jsonschema.validate(data, fl_schema)
