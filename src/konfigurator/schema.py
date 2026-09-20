"""Loader pro kanonicky config_schema_v1.json."""
from __future__ import annotations

import json
import pathlib

_SCHEMA_PATH = pathlib.Path(__file__).parent / "assets" / "config_schema_v1.json"

_cached = None


def load_schema() -> dict:
    global _cached
    if _cached is not None:
        return _cached
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
        _cached = json.load(f)
    return _cached


def schema_hash() -> str:
    import hashlib

    data = _SCHEMA_PATH.read_bytes()
    return hashlib.sha256(data).hexdigest()

# Known keys allowlisty odvozene ze schematu (ne ručně duplikovane)
KNOWN_ROOT_KEYS = {"schemaVersion", "createdAt", "generator", "calculatorCompatibility", "activeProfileId", "profiles", "globalSettings"}
KNOWN_COMPAT_KEYS = {"minVersion", "maxVersion"}
KNOWN_PROFILE_KEYS = {"id", "name", "isBuiltIn", "settings"}
KNOWN_SETTINGS_KEYS = {
    "accessibilityType", "screenReaderMode", "fontSizeMultiplier", "dialogFontScale",
    "dotMatrixZoom", "resultZoom", "thousandGroupGap", "dialogSize",
    "useSixteenSegment", "usePeriodicNotation", "announceExpression",
    "readStatsMemoryValues", "autoReadStatsSummary", "showStatsNavigationHint",
    "alignInputLeft", "overlineThickness", "overlineHeight",
    "speechRate", "speechVolume", "ttsEnabled", "ttsEngine", "ttsVoice", "ttsVoiceName",
    "inverseFormatPreference",
}
KNOWN_GLOBAL_KEYS = {"themeMode", "isDegreeMode", "defaultMode", "statsSummaryOrder", "statsComputedOrder", "currency", "devMode"}
KNOWN_CURRENCY_KEYS = {"from", "to"}
KNOWN_DEVMODE_KEYS = {"enabled", "autoDiagnostic", "diagnosticDurationMs", "pinCode"}
