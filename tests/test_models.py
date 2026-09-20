from konfigurator import models
import copy

def test_profile_isolation():
    p1 = models.AccessibilityProfile(id="a", name="A", isBuiltIn=False, settings=models.AccessibilitySettings.defaults_standard())
    p2 = copy.deepcopy(p1)
    p2.settings.fontSizeMultiplier = 2.0
    assert p1.settings.fontSizeMultiplier == 1.0
    assert p2.settings.fontSizeMultiplier == 2.0

def test_defaults():
    s = models.AccessibilitySettings.defaults_blind()
    assert s.announceExpression is True
    s2 = models.AccessibilitySettings.defaults_low_vision()
    assert s2.thousandGroupGap == "large"
    assert s2.useSixteenSegment is True

def test_config_canonical():
    cfg = models.ConfigFile()
    cfg.profiles = [
        models.AccessibilityProfile(id="standard", name="Std", isBuiltIn=True, settings=models.AccessibilitySettings.defaults_standard())
    ]
    c = cfg.canonical()
    assert "createdAt" not in c
    assert "generator" not in c
    assert c["schemaVersion"] == 1

def test_inverse_pref_mapping():
    assert models.AccessibilitySettings(inverseFormatPreference="dms").inverseFormatPreference == "dms"
    assert models.AccessibilitySettings(inverseFormatPreference="decimal").inverseFormatPreference == "decimal"
    assert models.AccessibilitySettings(inverseFormatPreference=None).inverseFormatPreference is None
