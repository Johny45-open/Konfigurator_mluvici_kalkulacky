"""Validator pro statistics_schema_v1.json — vrstva A + B (unknown warning)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import jsonschema

KNOWN_ROOT_KEYS = {"schemaVersion","createdAt","generator","statisticsCompatibility","folders","sets","currentIndex"}
KNOWN_COMPAT_KEYS = {"minVersion","maxVersion"}
KNOWN_FOLDER_KEYS = {"id","name","colorIndex","iconName","sortOrder","createdAt"}
KNOWN_SET_KEYS = {"id","name","fieldNames","fieldUnits","records","folderId","colorIndex","iconName","pinned","archived","createdAt","updatedAt","lastUsedAt","data"}
ICON_NAMES = {"dataset","school","work","home","lab","chart","folder","star"}
UNIT_NAMES = {"m","km","cm","mm","mi","yd","ft","in","kg","g","mg","t","lb","oz","m²","km²","ha","cm²","akr","l","ml","m³","gal","pt","Pa","hPa","kPa","bar","atm","psi","s","min","h","d","V","mV","µV","kV","MV","A","mA","µA","kA","Ω","mΩ","kΩ","MΩ","W","mW","kW","MW","GW","--", None}

import pathlib
_SCHEMA_PATH = pathlib.Path(__file__).parent / "assets" / "statistics_schema_v1.json"
_cached = None
def load_schema() -> dict:
    global _cached
    if _cached is not None:
        return _cached
    with open(_SCHEMA_PATH, encoding="utf-8") as f:
        _cached = json.load(f)
    return _cached

@dataclass
class ValidationIssue:
    path: str
    message: str
    code: str

@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    @property
    def ok(self) -> bool:
        return len(self.errors)==0

def _collect_unknown(data: dict, result: ValidationResult) -> None:
    for k in data.keys():
        if k not in KNOWN_ROOT_KEYS:
            result.warnings.append(ValidationIssue(k, f"Neznamy klic '{k}' na rootu.", "unknownKey"))
    comp = data.get("statisticsCompatibility")
    if isinstance(comp, dict):
        for k in comp.keys():
            if k not in KNOWN_COMPAT_KEYS:
                result.warnings.append(ValidationIssue(f"statisticsCompatibility.{k}", f"Neznamy klic '{k}'.", "unknownKey"))
    for i, f in enumerate(data.get("folders", [])):
        if not isinstance(f, dict): continue
        for k in f.keys():
            if k not in KNOWN_FOLDER_KEYS:
                result.warnings.append(ValidationIssue(f"folders[{i}].{k}", f"Neznamy klic '{k}'.", "unknownKey"))
    for i, s in enumerate(data.get("sets", [])):
        if not isinstance(s, dict): continue
        for k in s.keys():
            if k not in KNOWN_SET_KEYS:
                result.warnings.append(ValidationIssue(f"sets[{i}].{k}", f"Neznamy klic '{k}'.", "unknownKey"))

def validate_statistics(data) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(data, dict):
        result.errors.append(ValidationIssue("", "Root musi byt objekt.", "type"))
        return result
    sv = data.get("schemaVersion")
    if sv is None:
        result.errors.append(ValidationIssue("schemaVersion","Chybi schemaVersion.","required")); return result
    if not isinstance(sv, int):
        result.errors.append(ValidationIssue("schemaVersion","schemaVersion musi byt int.","type")); return result
    if sv != 1:
        if sv > 1:
            result.errors.append(ValidationIssue("schemaVersion", f"Nepodporovana budouci verze {sv}.","futureVersion"))
        else:
            result.errors.append(ValidationIssue("schemaVersion", f"Nepodporovana stara verze {sv}.","unsupportedVersion"))
        return result
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path)
        result.errors.append(ValidationIssue(path, err.message, err.validator))
    _collect_unknown(data, result)
    # semantic: ids unique, fieldUnits length, records values length, folderId existence, currentIndex clamp
    folders = data.get("folders", [])
    folder_ids = {f.get("id") for f in folders if isinstance(f, dict) and isinstance(f.get("id"), str)}
    sets = data.get("sets", [])
    set_ids = []
    set_norm_names = set()
    from .models import normalize_name
    for i, s in enumerate(sets):
        if not isinstance(s, dict): continue
        sid = s.get("id")
        if isinstance(sid, str):
            set_ids.append(sid)
        fn = s.get("fieldNames")
        fu = s.get("fieldUnits")
        if isinstance(fn, list) and isinstance(fu, list) and len(fn)!=len(fu):
            result.errors.append(ValidationIssue(f"sets[{i}].fieldUnits","fieldUnits delka musi odpovidat fieldNames.","length"))
        # units enum already in schema but check values
        if isinstance(fu, list):
            for u in fu:
                if u is not None and u != "--" and u not in UNIT_NAMES:
                    result.errors.append(ValidationIssue(f"sets[{i}].fieldUnits","Neplatna jednotka "+str(u),"enum"))
        # records length check
        if isinstance(fn, list):
            expected = len(fn)
            for ri, r in enumerate(s.get("records",[])):
                if not isinstance(r, dict): continue
                vals = r.get("values",[])
                if isinstance(vals, list) and len(vals)!=expected:
                    result.errors.append(ValidationIssue(f"sets[{i}].records[{ri}].values",f"Delka {len(vals)} != fieldNames {expected}.","length"))
                for v in vals:
                    if not isinstance(v, (int,float)):
                        result.errors.append(ValidationIssue(f"sets[{i}].records[{ri}].values","Hodnota musi byt cislo.","type"))
                    elif v!=v or v==float('inf') or v==float('-inf'):
                        result.errors.append(ValidationIssue(f"sets[{i}].records[{ri}].values","Hodnota nesmi byt NaN/Inf.","range"))
        # folderId existence
        fid = s.get("folderId")
        if fid is not None and fid not in folder_ids:
            result.errors.append(ValidationIssue(f"sets[{i}].folderId",f"folderId '{fid}' neexistuje.","existence"))
    if len(set_ids)!=len(set(set_ids)):
        result.errors.append(ValidationIssue("sets","ID sad musi byt unikatni.","unique"))
    folder_ids_list = [f.get("id") for f in folders if isinstance(f, dict)]
    if len(folder_ids_list)!=len(set(folder_ids_list)):
        result.errors.append(ValidationIssue("folders","ID slozek musi byt unikatni.","unique"))
    ci = data.get("currentIndex")
    if isinstance(ci, int) and isinstance(sets, list) and sets:
        if ci <0 or ci >= len(sets):
            result.errors.append(ValidationIssue("currentIndex", f"currentIndex {ci} mimo rozsah 0..{len(sets)-1}.","range"))
    # compatibility minVersion format
    comp = data.get("statisticsCompatibility")
    if isinstance(comp, dict):
        mv = comp.get("minVersion")
        if isinstance(mv, str):
            try:
                from packaging.version import Version; Version(mv)
            except Exception:
                result.errors.append(ValidationIssue("statisticsCompatibility.minVersion", f"Neplatny format '{mv}'.","format"))
    return result
