import hashlib, pathlib

PY = pathlib.Path(__file__).parent.parent / "src" / "konfigurator" / "assets" / "statistics_schema_v1.json"
FL = pathlib.Path(r"C:\Users\kaliv\AppData\Local\Temp\opencode\Mluvici_kalkulacka\assets\statistics_schema_v1.json")

def test_parity():
    assert PY.exists()
    if not FL.exists():
        import json; json.loads(PY.read_text(encoding="utf-8")); return
    assert hashlib.sha256(PY.read_bytes()).hexdigest()==hashlib.sha256(FL.read_bytes()).hexdigest()

def test_valid_schema():
    import json
    d=json.loads(PY.read_text(encoding="utf-8"))
    assert d["properties"]["schemaVersion"]["const"]==1
