import json
import pathlib
import tempfile

from konfigurator import models
from konfigurator.io import load_config, save_config, canonicalize_dict
from konfigurator.validator import validate_contract

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "valid_v1.json"


def test_load_valid():
    cfg, vr = load_config(FIXTURE)
    assert vr.ok
    assert cfg.schemaVersion == 3
    assert len(cfg.profiles) == 2
    assert cfg.activeProfileId == "standard"
    assert cfg.globalSettings.screenReaderMode == "auto"
    assert cfg.globalSettings.ttsEnabled is True
    assert cfg.profiles[0].settings.to_dict().get("speechRate") is None


def test_v1_migration_uses_the_active_profiles_voice_settings():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    raw["activeProfileId"] = "blind"
    raw["profiles"][0]["settings"]["speechRate"] = 0.2
    raw["profiles"][1]["settings"].update({
        "screenReaderMode": "off",
        "speechRate": 0.75,
        "ttsEnabled": False,
    })

    assert validate_contract(raw).ok
    cfg = models.ConfigFile.from_dict(raw)
    assert cfg.globalSettings.screenReaderMode == "off"
    assert cfg.globalSettings.speechRate == 0.75
    assert cfg.globalSettings.ttsEnabled is False


def test_invalid_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        f.write("{ not json }")
        path = f.name
    try:
        try:
            load_config(path)
            assert False, "should raise"
        except Exception:
            pass
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def test_missing_fields():
    import copy
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)
    del data["profiles"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        path = f.name
    try:
        try:
            load_config(path)
            assert False
        except ValueError as e:
            assert "Validace" in str(e) or "validation" in str(e).lower() or "profiles" in str(e)
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def test_roundtrip_canonical():
    with open(FIXTURE, encoding="utf-8") as f:
        original_raw = json.load(f)
    cfg, _ = load_config(FIXTURE)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    try:
        save_config(cfg, path)
        with open(path, encoding="utf-8") as f:
            reloaded_raw = json.load(f)
        # canonical compare: ignore createdAt/generator
        c1 = canonicalize_dict(original_raw)
        c2 = canonicalize_dict(reloaded_raw)
        # Opening a v1 file migrates profile-level voice settings to v3 globals.
        assert c1["schemaVersion"] == 1
        assert c2["schemaVersion"] == 3
        assert c1["activeProfileId"] == c2["activeProfileId"]
        assert c1["profiles"][0]["settings"]["accessibilityType"] == c2["profiles"][0]["settings"]["accessibilityType"]
        assert c2["globalSettings"]["speechRate"] == c1["profiles"][0]["settings"]["speechRate"]
        assert c2["globalSettings"]["screenReaderMode"] == c1["profiles"][0]["settings"]["screenReaderMode"]
        # metadata existence
        assert "createdAt" in reloaded_raw
        assert reloaded_raw["schemaVersion"] == 3
    finally:
        pathlib.Path(path).unlink(missing_ok=True)


def test_v3_global_options_are_preserved_on_open_and_save():
    raw = models.ConfigFile(
        profiles=[
            models.AccessibilityProfile(
                id="standard",
                name="Standardní",
                isBuiltIn=True,
                settings=models.AccessibilitySettings.defaults_standard(),
            )
        ]
    ).to_dict(include_metadata=False)
    raw["globalSettings"]["statsComputedOrder"] = ["sampleVariance", "mean"]
    raw["globalSettings"]["statsDisplayConfig"] = {"preset": "custom", "customShowN": True}
    cfg = models.ConfigFile.from_dict(raw)

    assert cfg.globalSettings.statsComputedOrder == ["sampleVariance", "mean"]
    saved = cfg.to_dict(include_metadata=False)
    assert saved["globalSettings"]["statsDisplayConfig"] == {
        "preset": "custom",
        "customShowN": True,
    }
    assert validate_contract(saved).ok


def test_atomic_save_no_partial():
    cfg, _ = load_config(FIXTURE)
    with tempfile.TemporaryDirectory() as d:
        path = pathlib.Path(d) / "out.json"
        save_config(cfg, path)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert validate_contract(data).ok


def test_unknown_keys_roundtrip_ignored():
    with open(FIXTURE, encoding="utf-8") as f:
        data = json.load(f)
    data["unknownRoot"] = 123
    # validate should be ok with warning
    vr = validate_contract(data)
    assert vr.ok
    assert len(vr.warnings) > 0
    # saving via model should drop unknown (canonical)
    cfg = models.ConfigFile.from_dict(data)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        path = tmp.name
    try:
        save_config(cfg, path)
        reloaded = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        assert "unknownRoot" not in reloaded
    finally:
        pathlib.Path(path).unlink(missing_ok=True)
