import copy
import json
import pathlib

import pytest

from konfigurator.validator import validate_contract

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "valid_v1.json"


def load_valid():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def test_valid():
    data = load_valid()
    vr = validate_contract(data)
    assert vr.ok, f"errors: {[e.message for e in vr.errors]}"
    assert len(vr.warnings) == 0


def test_missing_schemaVersion():
    data = load_valid()
    del data["schemaVersion"]
    vr = validate_contract(data)
    assert not vr.ok
    assert any(e.code == "required" for e in vr.errors)


def test_invalid_json_type():
    vr = validate_contract("not a dict")
    assert not vr.ok


def test_unknown_schemaVersion_future():
    data = load_valid()
    data["schemaVersion"] = 2
    vr = validate_contract(data)
    assert not vr.ok
    assert any(e.code == "futureVersion" for e in vr.errors)


def test_old_schemaVersion():
    data = load_valid()
    data["schemaVersion"] = 0
    vr = validate_contract(data)
    assert not vr.ok
    assert any(e.code == "unsupportedVersion" for e in vr.errors)


def test_missing_required_field():
    data = load_valid()
    del data["activeProfileId"]
    vr = validate_contract(data)
    assert not vr.ok


def test_unknown_fields_warning_not_error():
    data = load_valid()
    data["unknownRoot"] = 123
    data["profiles"][0]["extra"] = "x"
    data["profiles"][0]["settings"]["unknownSetting"] = True
    data["globalSettings"]["extraGlobal"] = 1
    vr = validate_contract(data)
    assert vr.ok, f"unknown should not block: {vr.errors}"
    assert len(vr.warnings) >= 3
    assert all(w.code == "unknownKey" for w in vr.warnings)


def test_invalid_type():
    data = load_valid()
    data["profiles"][0]["settings"]["fontSizeMultiplier"] = "bad"
    vr = validate_contract(data)
    assert not vr.ok


def test_invalid_range():
    data = load_valid()
    data["profiles"][0]["settings"]["speechRate"] = 5.0
    vr = validate_contract(data)
    assert not vr.ok
    assert any("speechRate" in e.path for e in vr.errors)


def test_invalid_enum():
    data = load_valid()
    data["globalSettings"]["themeMode"] = "neon"
    vr = validate_contract(data)
    assert not vr.ok


def test_duplicate_profile_id():
    data = load_valid()
    dup = copy.deepcopy(data["profiles"][0])
    data["profiles"].append(dup)
    vr = validate_contract(data)
    assert not vr.ok
    assert any(e.code == "unique" for e in vr.errors)


def test_unknown_profile_active():
    data = load_valid()
    data["activeProfileId"] = "nonexistent"
    vr = validate_contract(data)
    assert not vr.ok
    assert any("activeProfileId" in e.path for e in vr.errors)


def test_isBuiltIn_reserved():
    data = load_valid()
    data["profiles"].append({
        "id": "custom_123",
        "name": "Custom",
        "isBuiltIn": True,
        "settings": data["profiles"][0]["settings"]
    })
    vr = validate_contract(data)
    assert not vr.ok


def test_inverse_format_string():
    data = load_valid()
    data["profiles"][0]["settings"]["inverseFormatPreference"] = "invalid"
    vr = validate_contract(data)
    assert not vr.ok
    data["profiles"][0]["settings"]["inverseFormatPreference"] = "dms"
    vr = validate_contract(data)
    assert vr.ok
    data["profiles"][0]["settings"]["inverseFormatPreference"] = "decimal"
    vr = validate_contract(data)
    assert vr.ok
    data["profiles"][0]["settings"]["inverseFormatPreference"] = None
    vr = validate_contract(data)
    assert vr.ok


def test_ttsVoice_structure():
    data = load_valid()
    data["profiles"][0]["settings"]["ttsVoice"] = {"name": "Voice1", "locale": "cs-CZ"}
    vr = validate_contract(data)
    assert vr.ok
    data["profiles"][0]["settings"]["ttsVoice"] = {"name": "", "locale": "cs-CZ"}
    vr = validate_contract(data)
    assert not vr.ok


def test_stats_order_uniqueness():
    data = load_valid()
    data["globalSettings"]["statsSummaryOrder"] = ["header", "header", "computed"]
    vr = validate_contract(data)
    assert not vr.ok


def test_compatible_minVersion_format():
    data = load_valid()
    data["calculatorCompatibility"]["minVersion"] = "bad"
    vr = validate_contract(data)
    assert not vr.ok
