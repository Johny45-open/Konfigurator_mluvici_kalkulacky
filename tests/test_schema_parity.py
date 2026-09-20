import hashlib
import pathlib

PYTHON_SCHEMA = pathlib.Path(__file__).parent.parent / "src" / "konfigurator" / "assets" / "config_schema_v1.json"
FLUTTER_SCHEMA = pathlib.Path(r"C:\Users\kaliv\AppData\Local\Temp\opencode\Mluvici_kalkulacka\assets\config_schema_v1.json")


def test_schema_hash_parity():
    assert PYTHON_SCHEMA.exists(), f"Python schema not found: {PYTHON_SCHEMA}"
    # Flutter schema may not exist in CI without clone; try to find alternative
    flutter_path = FLUTTER_SCHEMA
    if not flutter_path.exists():
        # Try relative to this file's parent if kalkulacka is sibling
        alt = pathlib.Path(__file__).parent.parent.parent / "Mluvici_kalkulacka" / "assets" / "config_schema_v1.json"
        if alt.exists():
            flutter_path = alt
        else:
            # If Flutter schema not available, just check Python schema is valid JSON
            import json
            json.loads(PYTHON_SCHEMA.read_text(encoding="utf-8"))
            return
    py_hash = hashlib.sha256(PYTHON_SCHEMA.read_bytes()).hexdigest()
    fl_hash = hashlib.sha256(flutter_path.read_bytes()).hexdigest()
    assert py_hash == fl_hash, f"Schema hash mismatch: Python {py_hash} != Flutter {fl_hash}. Run sync_schema.py"


def test_schema_is_valid_json_schema():
    import json
    data = json.loads(PYTHON_SCHEMA.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert data["properties"]["schemaVersion"]["const"] == 1
