import json, pathlib
from konfigurator.statistics_validator import validate_statistics

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "valid_statistics_v1.json"

def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

def test_valid():
    vr = validate_statistics(load())
    assert vr.ok, vr.errors
    assert not vr.warnings

def test_future():
    d=load(); d["schemaVersion"]=2
    assert not validate_statistics(d).ok

def test_unknown_warning():
    d=load(); d["extra"]=123
    vr=validate_statistics(d)
    assert vr.ok and len(vr.warnings)>0

def test_records_length():
    d=load(); d["sets"][0]["records"].append({"values":[1]})
    assert not validate_statistics(d).ok

def test_invalid_unit():
    d=load(); d["sets"][0]["fieldUnits"]=["BAD"]
    assert not validate_statistics(d).ok

def test_folderId_existence():
    d=load(); d["sets"][0]["folderId"]="nonexist"
    assert not validate_statistics(d).ok

def test_currentIndex_range():
    d=load(); d["currentIndex"]=99
    assert not validate_statistics(d).ok
