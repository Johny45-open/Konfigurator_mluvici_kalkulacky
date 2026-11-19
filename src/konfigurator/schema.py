"""Loader schémat přenositelného konfiguračního kontraktu."""
from __future__ import annotations

import json
import pathlib

_SCHEMA_DIR = pathlib.Path(__file__).parent / "assets"

_cached: dict[int, dict] = {}


def load_schema(version: int = 3) -> dict:
    if version not in _cached:
        schema_path = _SCHEMA_DIR / f"config_schema_v{version}.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            _cached[version] = json.load(f)
    return _cached[version]


def schema_hash(version: int = 3) -> str:
    import hashlib

    data = (_SCHEMA_DIR / f"config_schema_v{version}.json").read_bytes()
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
KNOWN_GLOBAL_KEYS = {
    "themeMode", "screenReaderMode", "ttsEnabled", "speechRate", "speechVolume",
    "ttsEngine", "ttsVoice", "ttsVoiceName", "resultDisplayMode",
    "announceFractionAvailability", "resultNotationPreference",
    "historyExactFormat", "statsDisplayConfig", "isDegreeMode", "defaultMode",
    "statsSummaryOrder", "statsComputedOrder", "currency", "devMode",
}
KNOWN_CURRENCY_KEYS = {"from", "to"}
KNOWN_DEVMODE_KEYS = {"enabled", "autoDiagnostic", "diagnosticDurationMs", "pinCode"}
