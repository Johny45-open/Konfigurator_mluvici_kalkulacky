"""Validace kontraktu: vrstva A JSON Schema + vrstva B unknown-key warnings."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import jsonschema

from .schema import (
    KNOWN_COMPAT_KEYS,
    KNOWN_CURRENCY_KEYS,
    KNOWN_DEVMODE_KEYS,
    KNOWN_GLOBAL_KEYS,
    KNOWN_PROFILE_KEYS,
    KNOWN_ROOT_KEYS,
    KNOWN_SETTINGS_KEYS,
    load_schema,
)


@dataclass
class ValidationIssue:
    path: str
    message: str
    code: str  # e.g. type, range, required, enum, unknownKey, futureVersion


@dataclass
class ValidationResult:
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def _collect_unknown_keys(data: dict, result: ValidationResult) -> None:
    for k in data.keys():
        if k not in KNOWN_ROOT_KEYS:
            result.warnings.append(ValidationIssue(path=k, message=f"Neznamy klic '{k}' na rootu, ignoruje se.", code="unknownKey"))
    comp = data.get("calculatorCompatibility")
    if isinstance(comp, dict):
        for k in comp.keys():
            if k not in KNOWN_COMPAT_KEYS:
                result.warnings.append(ValidationIssue(path=f"calculatorCompatibility.{k}", message=f"Neznamy klic '{k}' v calculatorCompatibility.", code="unknownKey"))
    profiles = data.get("profiles")
    if isinstance(profiles, list):
        for i, p in enumerate(profiles):
            if not isinstance(p, dict):
                continue
            for k in p.keys():
                if k not in KNOWN_PROFILE_KEYS:
                    result.warnings.append(ValidationIssue(path=f"profiles[{i}].{k}", message=f"Neznamy klic '{k}' v profilu.", code="unknownKey"))
            settings = p.get("settings")
            if isinstance(settings, dict):
                for k in settings.keys():
                    if k not in KNOWN_SETTINGS_KEYS:
                        result.warnings.append(ValidationIssue(path=f"profiles[{i}].settings.{k}", message=f"Neznamy klic '{k}' v settings, ignoruje se.", code="unknownKey"))
                voice = settings.get("ttsVoice")
                if isinstance(voice, dict):
                    for k in voice.keys():
                        if k not in {"name", "locale"}:
                            result.warnings.append(ValidationIssue(path=f"profiles[{i}].settings.ttsVoice.{k}", message=f"Neznamy klic '{k}' v ttsVoice.", code="unknownKey"))
    gs = data.get("globalSettings")
    if isinstance(gs, dict):
        for k in gs.keys():
            if k not in KNOWN_GLOBAL_KEYS:
                result.warnings.append(ValidationIssue(path=f"globalSettings.{k}", message=f"Neznamy klic '{k}' v globalSettings.", code="unknownKey"))
        cur = gs.get("currency")
        if isinstance(cur, dict):
            for k in cur.keys():
                if k not in KNOWN_CURRENCY_KEYS:
                    result.warnings.append(ValidationIssue(path=f"globalSettings.currency.{k}", message=f"Neznamy klic '{k}' v currency.", code="unknownKey"))
        dev = gs.get("devMode")
        if isinstance(dev, dict):
            for k in dev.keys():
                if k not in KNOWN_DEVMODE_KEYS:
                    result.warnings.append(ValidationIssue(path=f"globalSettings.devMode.{k}", message=f"Neznamy klic '{k}' v devMode.", code="unknownKey"))


def validate_contract(data: Any) -> ValidationResult:
    result = ValidationResult()
    if not isinstance(data, dict):
        result.errors.append(ValidationIssue(path="", message="Root musi byt objekt.", code="type"))
        return result

    # --- schemaVersion pred JSON Schema, abychom dali lepsi chybu pro future/old ---
    sv = data.get("schemaVersion")
    if sv is None:
        result.errors.append(ValidationIssue(path="schemaVersion", message="Chybi schemaVersion.", code="required"))
        return result
    if not isinstance(sv, int):
        result.errors.append(ValidationIssue(path="schemaVersion", message="schemaVersion musi byt integer.", code="type"))
        return result
    if sv != 1:
        if sv > 1:
            result.errors.append(ValidationIssue(path="schemaVersion", message=f"Nepodporovana budouci verze schemaVersion={sv} (podporovana je 1). Aktualizujte kalkulacku.", code="futureVersion"))
        else:
            result.errors.append(ValidationIssue(path="schemaVersion", message=f"Nepodporovana stara verze schemaVersion={sv} (podporovana je 1).", code="unsupportedVersion"))
        return result

    # --- vrstva A: JSON Schema ---
    schema = load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) if err.path else ""
        # Map jsonschema keyword to code
        code = err.validator
        result.errors.append(ValidationIssue(path=path, message=err.message, code=code))

    # Pokud uz mame chyby z vrstvy A, stale chceme unknown warnings ale neblokujeme je
    _collect_unknown_keys(data, result)

    # --- dodatecne semanticke kontroly (unikatnost, existence activeProfileId, poradi) ---
    profiles = data.get("profiles")
    if isinstance(profiles, list):
        ids = [p.get("id") for p in profiles if isinstance(p, dict)]
        if len(ids) != len(set(ids)):
            result.errors.append(ValidationIssue(path="profiles", message="ID profilu musi byt unikatni.", code="unique"))
        # builtIn id rezervace: pokud isBuiltIn true ale id neni standard/blind/lowvision -> error
        for i, p in enumerate(profiles):
            if not isinstance(p, dict):
                continue
            is_builtin = p.get("isBuiltIn")
            pid = p.get("id")
            if is_builtin is True and pid not in ("standard", "blind", "lowvision"):
                result.errors.append(ValidationIssue(path=f"profiles[{i}].isBuiltIn", message="isBuiltIn=true povoleno pouze pro standard/blind/lowvision.", code="enum"))
        active = data.get("activeProfileId")
        if isinstance(active, str) and active not in ids:
            result.errors.append(ValidationIssue(path="activeProfileId", message=f"activeProfileId '{active}' neexistuje v profiles.", code="existence"))

        # isBuiltIn custom nesmi mit true pro custom id
    gs = data.get("globalSettings")
    if isinstance(gs, dict):
        # statsSummaryOrder uniqueness + length uz v schema, ale zkontrolujeme unikatnost explicitne
        order = gs.get("statsSummaryOrder")
        if isinstance(order, list) and len(order) != len(set(order)):
            result.errors.append(ValidationIssue(path="globalSettings.statsSummaryOrder", message="statsSummaryOrder musi obsahovat unikatni hodnoty.", code="unique"))
        corder = gs.get("statsComputedOrder")
        if isinstance(corder, list) and len(corder) != len(set(corder)):
            result.errors.append(ValidationIssue(path="globalSettings.statsComputedOrder", message="statsComputedOrder musi obsahovat unikatni hodnoty.", code="unique"))

    # Compatibility minVersion format already in schema, ale zkontrolujeme parsovatelnost
    comp = data.get("calculatorCompatibility")
    if isinstance(comp, dict):
        mv = comp.get("minVersion")
        if isinstance(mv, str):
            try:
                from packaging.version import Version
                Version(mv)
            except Exception:
                result.errors.append(ValidationIssue(path="calculatorCompatibility.minVersion", message=f"Neplatny format verze '{mv}'.", code="format"))

    return result
