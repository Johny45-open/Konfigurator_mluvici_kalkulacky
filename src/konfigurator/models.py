"""Datove modely odpovidajici config_schema_v1.json a internim enumum kalkulacky."""
from __future__ import annotations

import copy
import dataclasses
import datetime
import hashlib
import random
from dataclasses import dataclass, field
from typing import Optional

APP_VERSION = "11.5.0"
SCHEMA_VERSION = 1

# --- enums jako stringy (verejny kontrakt) ---
ACCESSIBILITY_TYPES = ("none", "blind", "visuallyImpaired")
SCREEN_READER_MODES = ("auto", "on", "off")
THOUSAND_GAPS = ("small", "medium", "large")
DIALOG_SIZES = ("compact", "wide", "fullscreen")
CALCULATOR_MODES = ("basic", "scientific", "statistics", "electrician", "unitConversion", "time", "currency")
THEMES = ("light", "dark")
STATS_SUMMARY_SECTIONS = ("header", "dataValues", "computed")
STATS_COMPUTED_ITEMS = ("mean", "sum", "variance", "sd", "median", "min", "max", "mode", "cv", "wmean")
INVERSE_PREFS = ("dms", "decimal")


def generate_custom_id(name: str) -> str:
    ts = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000_000)
    rnd = random.randint(0, 1 << 32)
    h = abs(hash(name)) % 10000
    return f"custom_{ts}_{rnd}_{h}"


@dataclass
class TtsVoice:
    name: str
    locale: str

    def to_dict(self) -> dict:
        return {"name": self.name, "locale": self.locale}

    @classmethod
    def from_dict(cls, d: dict) -> "TtsVoice":
        return cls(name=str(d["name"]), locale=str(d["locale"]))


@dataclass
class AccessibilitySettings:
    accessibilityType: str = "none"
    screenReaderMode: str = "auto"
    fontSizeMultiplier: float = 1.0
    dialogFontScale: float = 1.0
    dotMatrixZoom: float = 1.0
    resultZoom: float = 1.0
    thousandGroupGap: str = "medium"
    dialogSize: str = "compact"
    useSixteenSegment: bool = False
    usePeriodicNotation: bool = True
    announceExpression: bool = False
    readStatsMemoryValues: bool = True
    autoReadStatsSummary: bool = True
    showStatsNavigationHint: bool = True
    alignInputLeft: bool = True
    overlineThickness: float = 1.0
    overlineHeight: float = 1.0
    speechRate: float = 0.5
    speechVolume: float = 1.0
    ttsEnabled: bool = True
    ttsEngine: Optional[str] = None
    ttsVoice: Optional[TtsVoice] = None
    ttsVoiceName: Optional[str] = None
    inverseFormatPreference: Optional[str] = None  # dms/decimal/null

    @classmethod
    def defaults_standard(cls) -> "AccessibilitySettings":
        return cls()

    @classmethod
    def defaults_blind(cls) -> "AccessibilitySettings":
        return cls(accessibilityType="blind", announceExpression=True)

    @classmethod
    def defaults_low_vision(cls) -> "AccessibilitySettings":
        return cls(
            accessibilityType="visuallyImpaired",
            fontSizeMultiplier=1.75,
            dialogFontScale=1.5,
            dotMatrixZoom=1.25,
            resultZoom=1.25,
            thousandGroupGap="large",
            dialogSize="wide",
            useSixteenSegment=True,
        )

    def to_dict(self) -> dict:
        d: dict = {
            "accessibilityType": self.accessibilityType,
            "screenReaderMode": self.screenReaderMode,
            "fontSizeMultiplier": self.fontSizeMultiplier,
            "dialogFontScale": self.dialogFontScale,
            "dotMatrixZoom": self.dotMatrixZoom,
            "resultZoom": self.resultZoom,
            "thousandGroupGap": self.thousandGroupGap,
            "dialogSize": self.dialogSize,
            "useSixteenSegment": self.useSixteenSegment,
            "usePeriodicNotation": self.usePeriodicNotation,
            "announceExpression": self.announceExpression,
            "readStatsMemoryValues": self.readStatsMemoryValues,
            "autoReadStatsSummary": self.autoReadStatsSummary,
            "showStatsNavigationHint": self.showStatsNavigationHint,
            "alignInputLeft": self.alignInputLeft,
            "overlineThickness": self.overlineThickness,
            "overlineHeight": self.overlineHeight,
            "speechRate": self.speechRate,
            "speechVolume": self.speechVolume,
            "ttsEnabled": self.ttsEnabled,
            "ttsEngine": self.ttsEngine,
            "ttsVoice": self.ttsVoice.to_dict() if self.ttsVoice else None,
            "ttsVoiceName": self.ttsVoiceName,
            "inverseFormatPreference": self.inverseFormatPreference,
        }
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "AccessibilitySettings":
        voice = None
        if d.get("ttsVoice") is not None:
            voice = TtsVoice.from_dict(d["ttsVoice"])
        return cls(
            accessibilityType=str(d.get("accessibilityType", "none")),
            screenReaderMode=str(d.get("screenReaderMode", "auto")),
            fontSizeMultiplier=float(d.get("fontSizeMultiplier", 1.0)),
            dialogFontScale=float(d.get("dialogFontScale", 1.0)),
            dotMatrixZoom=float(d.get("dotMatrixZoom", 1.0)),
            resultZoom=float(d.get("resultZoom", 1.0)),
            thousandGroupGap=str(d.get("thousandGroupGap", "medium")),
            dialogSize=str(d.get("dialogSize", "compact")),
            useSixteenSegment=bool(d.get("useSixteenSegment", False)),
            usePeriodicNotation=bool(d.get("usePeriodicNotation", True)),
            announceExpression=bool(d.get("announceExpression", False)),
            readStatsMemoryValues=bool(d.get("readStatsMemoryValues", True)),
            autoReadStatsSummary=bool(d.get("autoReadStatsSummary", True)),
            showStatsNavigationHint=bool(d.get("showStatsNavigationHint", True)),
            alignInputLeft=bool(d.get("alignInputLeft", True)),
            overlineThickness=float(d.get("overlineThickness", 1.0)),
            overlineHeight=float(d.get("overlineHeight", 1.0)),
            speechRate=float(d.get("speechRate", 0.5)),
            speechVolume=float(d.get("speechVolume", 1.0)),
            ttsEnabled=bool(d.get("ttsEnabled", True)),
            ttsEngine=d.get("ttsEngine"),
            ttsVoice=voice,
            ttsVoiceName=d.get("ttsVoiceName"),
            inverseFormatPreference=d.get("inverseFormatPreference"),
        )


@dataclass
class AccessibilityProfile:
    id: str
    name: str
    isBuiltIn: bool
    settings: AccessibilitySettings

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "isBuiltIn": self.isBuiltIn, "settings": self.settings.to_dict()}

    @classmethod
    def from_dict(cls, d: dict) -> "AccessibilityProfile":
        return cls(
            id=str(d["id"]),
            name=str(d["name"]),
            isBuiltIn=bool(d.get("isBuiltIn", False)),
            settings=AccessibilitySettings.from_dict(d["settings"]),
        )

    def clone(self) -> "AccessibilityProfile":
        return AccessibilityProfile(
            id=self.id, name=self.name, isBuiltIn=self.isBuiltIn, settings=copy.deepcopy(self.settings)
        )


@dataclass
class GlobalSettings:
    themeMode: str = "dark"
    isDegreeMode: bool = True
    defaultMode: str = "scientific"
    statsSummaryOrder: list = field(default_factory=lambda: ["header", "dataValues", "computed"])
    statsComputedOrder: list = field(default_factory=lambda: ["mean", "sum", "variance", "sd", "median", "min", "max", "mode", "cv", "wmean"])
    currencyFrom: str = "CZK"
    currencyTo: str = "EUR"
    devEnabled: bool = False
    devAutoDiagnostic: bool = False
    devDiagnosticDurationMs: int = 700
    devPinCode: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {
            "themeMode": self.themeMode,
            "isDegreeMode": self.isDegreeMode,
            "defaultMode": self.defaultMode,
            "statsSummaryOrder": list(self.statsSummaryOrder),
            "statsComputedOrder": list(self.statsComputedOrder),
            "currency": {"from": self.currencyFrom, "to": self.currencyTo},
            "devMode": {
                "enabled": self.devEnabled,
                "autoDiagnostic": self.devAutoDiagnostic,
                "diagnosticDurationMs": self.devDiagnosticDurationMs,
            },
        }
        if self.devPinCode is not None:
            d["devMode"]["pinCode"] = self.devPinCode
        else:
            # nullable in schema, explicit null for round-trip clarity optional
            pass
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "GlobalSettings":
        cur = d.get("currency", {})
        dev = d.get("devMode", {})
        return cls(
            themeMode=str(d.get("themeMode", "dark")),
            isDegreeMode=bool(d.get("isDegreeMode", True)),
            defaultMode=str(d.get("defaultMode", "scientific")),
            statsSummaryOrder=list(d.get("statsSummaryOrder", ["header", "dataValues", "computed"])),
            statsComputedOrder=list(d.get("statsComputedOrder", ["mean", "sum", "variance", "sd", "median", "min", "max", "mode", "cv", "wmean"])),
            currencyFrom=str(cur.get("from", "CZK")),
            currencyTo=str(cur.get("to", "EUR")),
            devEnabled=bool(dev.get("enabled", False)),
            devAutoDiagnostic=bool(dev.get("autoDiagnostic", False)),
            devDiagnosticDurationMs=int(dev.get("diagnosticDurationMs", 700)),
            devPinCode=dev.get("pinCode"),
        )


@dataclass
class ConfigFile:
    schemaVersion: int = SCHEMA_VERSION
    createdAt: Optional[str] = None
    generator: Optional[str] = None
    minVersion: str = APP_VERSION
    maxVersion: Optional[str] = None
    activeProfileId: str = "standard"
    profiles: list[AccessibilityProfile] = field(default_factory=list)
    globalSettings: GlobalSettings = field(default_factory=GlobalSettings)

    def to_dict(self, include_metadata: bool = True) -> dict:
        d: dict = {
            "schemaVersion": self.schemaVersion,
            "activeProfileId": self.activeProfileId,
            "profiles": [p.to_dict() for p in self.profiles],
            "globalSettings": self.globalSettings.to_dict(),
        }
        if include_metadata:
            if self.createdAt:
                d["createdAt"] = self.createdAt
            else:
                d["createdAt"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            d["generator"] = self.generator or f"Konfigurator_mluvici_kalkulacky/{__import__('konfigurator').__version__}"
            d["calculatorCompatibility"] = {"minVersion": self.minVersion, "maxVersion": self.maxVersion}
        else:
            # for canonicalize comparisons
            pass
        # Ensure calculatorCompatibility always if include_metadata
        if include_metadata and "calculatorCompatibility" not in d:
            d["calculatorCompatibility"] = {"minVersion": self.minVersion, "maxVersion": self.maxVersion}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ConfigFile":
        comp = d.get("calculatorCompatibility", {})
        profiles = [AccessibilityProfile.from_dict(p) for p in d.get("profiles", [])]
        return cls(
            schemaVersion=int(d.get("schemaVersion", 1)),
            createdAt=d.get("createdAt"),
            generator=d.get("generator"),
            minVersion=str(comp.get("minVersion", APP_VERSION)),
            maxVersion=comp.get("maxVersion"),
            activeProfileId=str(d.get("activeProfileId", "standard")),
            profiles=profiles,
            globalSettings=GlobalSettings.from_dict(d.get("globalSettings", {})),
        )

    def canonical(self) -> dict:
        """Semanticky obsah bez dynamickych metadat pro round-trip porovnani."""
        d = self.to_dict(include_metadata=False)
        # Do not include createdAt/generator/calculatorCompatibility.maxVersion
        return d


# --- Statisticke sady (oddělený kontrakt) ---
STATISTICS_SCHEMA_VERSION = 1
STATS_PALETTE_SIZE = 8
STATS_ICON_NAMES = ("dataset", "school", "work", "home", "lab", "chart", "folder", "star")
UNIT_NAMES = ("m","km","cm","mm","mi","yd","ft","in","kg","g","mg","t","lb","oz","m²","km²","ha","cm²","akr","l","ml","m³","gal","pt","Pa","hPa","kPa","bar","atm","psi","s","min","h","d","V","mV","µV","kV","MV","A","mA","µA","kA","Ω","mΩ","kΩ","MΩ","W","mW","kW","MW","GW")


def generate_stats_id() -> str:
    ts = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000_000)
    rnd = random.randint(0, 1 << 32)
    return f"{ts}_{rnd}"


def strip_diacritics(s: str) -> str:
    repl = {"á":"a","č":"c","ď":"d","é":"e","ě":"e","í":"i","ň":"n","ó":"o","ř":"r","š":"s","ť":"t","ú":"u","ů":"u","ý":"y","ž":"z","Á":"A","Č":"C","Ď":"D","É":"E","Ě":"E","Í":"I","Ň":"N","Ó":"O","Ř":"R","Š":"S","Ť":"T","Ú":"U","Ů":"U","Ý":"Y","Ž":"Z"}
    for k,v in repl.items():
        s = s.replace(k, v)
    return s


def normalize_name(s: str) -> str:
    import re
    return strip_diacritics(s.lower().replace(".", "").replace(",", "").strip()).strip()


@dataclass
class StatisticsRecord:
    values: list[float]

    def to_dict(self) -> dict:
        return {"values": list(self.values)}

    @classmethod
    def from_dict(cls, d: dict) -> "StatisticsRecord":
        return cls(values=[float(v) for v in d.get("values", [])])


@dataclass
class StatisticsFolder:
    id: str
    name: str
    colorIndex: int = 0
    iconName: str = "folder"
    sortOrder: int = 0
    createdAt: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict = {"id": self.id, "name": self.name, "colorIndex": self.colorIndex, "iconName": self.iconName, "sortOrder": self.sortOrder}
        if self.createdAt:
            d["createdAt"] = self.createdAt
        else:
            d["createdAt"] = datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StatisticsFolder":
        return cls(
            id=str(d["id"]), name=str(d["name"]),
            colorIndex=int(d.get("colorIndex", 0)), iconName=str(d.get("iconName", "folder")),
            sortOrder=int(d.get("sortOrder", 0)), createdAt=d.get("createdAt")
        )


@dataclass
class StatisticsSet:
    id: str
    name: str
    fieldNames: list[str]
    fieldUnits: list[Optional[str]] = field(default_factory=list)
    records: list[StatisticsRecord] = field(default_factory=list)
    folderId: Optional[str] = None
    colorIndex: int = 0
    iconName: str = "dataset"
    pinned: bool = False
    archived: bool = False
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    lastUsedAt: Optional[str] = None

    def __post_init__(self):
        if not self.fieldUnits:
            self.fieldUnits = [None] * len(self.fieldNames)
        elif len(self.fieldUnits) != len(self.fieldNames):
            # pad/truncate
            self.fieldUnits = (self.fieldUnits + [None]*len(self.fieldNames))[:len(self.fieldNames)]

    def to_dict(self) -> dict:
        now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        return {
            "id": self.id, "name": self.name,
            "fieldNames": list(self.fieldNames),
            "fieldUnits": list(self.fieldUnits),
            "records": [r.to_dict() for r in self.records],
            "folderId": self.folderId,
            "colorIndex": self.colorIndex, "iconName": self.iconName,
            "pinned": self.pinned, "archived": self.archived,
            "createdAt": self.createdAt or now,
            "updatedAt": self.updatedAt or now,
            "lastUsedAt": self.lastUsedAt or now,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "StatisticsSet":
        # legacy 'data' -> single field
        if "data" in d:
            data = [float(v) for v in d.get("data", [])]
            return cls(
                id=str(d.get("id", generate_stats_id())), name=str(d.get("name", "Sada")),
                fieldNames=["Hodnota"], fieldUnits=[None],
                records=[StatisticsRecord(values=[v]) for v in data],
                folderId=d.get("folderId"), colorIndex=int(d.get("colorIndex", 0)), iconName=str(d.get("iconName", "dataset")),
                pinned=bool(d.get("pinned", False)), archived=bool(d.get("archived", False)),
                createdAt=d.get("createdAt"), updatedAt=d.get("updatedAt"), lastUsedAt=d.get("lastUsedAt")
            )
        return cls(
            id=str(d["id"]), name=str(d["name"]),
            fieldNames=list(d["fieldNames"]),
            fieldUnits=list(d.get("fieldUnits", [None]*len(d["fieldNames"]))),
            records=[StatisticsRecord.from_dict(e) for e in d.get("records", [])],
            folderId=d.get("folderId"), colorIndex=int(d.get("colorIndex", 0)), iconName=str(d.get("iconName", "dataset")),
            pinned=bool(d.get("pinned", False)), archived=bool(d.get("archived", False)),
            createdAt=d.get("createdAt"), updatedAt=d.get("updatedAt"), lastUsedAt=d.get("lastUsedAt")
        )


@dataclass
class StatisticsFile:
    schemaVersion: int = STATISTICS_SCHEMA_VERSION
    createdAt: Optional[str] = None
    generator: Optional[str] = None
    minVersion: str = APP_VERSION
    maxVersion: Optional[str] = None
    folders: list[StatisticsFolder] = field(default_factory=list)
    sets: list[StatisticsSet] = field(default_factory=list)
    currentIndex: int = 0

    def to_dict(self, include_metadata: bool = True) -> dict:
        d: dict = {
            "schemaVersion": self.schemaVersion,
            "folders": [f.to_dict() for f in self.folders],
            "sets": [s.to_dict() for s in self.sets],
            "currentIndex": self.currentIndex,
        }
        if include_metadata:
            d["createdAt"] = self.createdAt or datetime.datetime.now(tz=datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            d["generator"] = self.generator or f"Konfigurator_mluvici_kalkulacky/{__import__('konfigurator').__version__}"
            d["statisticsCompatibility"] = {"minVersion": self.minVersion, "maxVersion": self.maxVersion}
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "StatisticsFile":
        comp = d.get("statisticsCompatibility", {})
        return cls(
            schemaVersion=int(d.get("schemaVersion", 1)),
            createdAt=d.get("createdAt"), generator=d.get("generator"),
            minVersion=str(comp.get("minVersion", APP_VERSION)), maxVersion=comp.get("maxVersion"),
            folders=[StatisticsFolder.from_dict(e) for e in d.get("folders", [])],
            sets=[StatisticsSet.from_dict(e) for e in d.get("sets", [])],
            currentIndex=int(d.get("currentIndex", 0)),
        )

    def canonical(self) -> dict:
        return self.to_dict(include_metadata=False)
