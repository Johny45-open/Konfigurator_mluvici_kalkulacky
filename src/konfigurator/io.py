"""IO pro konfiguracni soubory — atomicky zapis, nacitani, validace."""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import Any

from . import models
from .validator import ValidationResult, validate_contract


def load_raw(path: str | pathlib.Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Root JSON musi byt objekt.")
    return data


def load_config(path: str | pathlib.Path) -> tuple[models.ConfigFile, ValidationResult]:
    raw = load_raw(path)
    vr = validate_contract(raw)
    if not vr.ok:
        raise ValueError(f"Validace selhala: {[e.message for e in vr.errors]}")
    cfg = models.ConfigFile.from_dict(raw)
    return cfg, vr


def save_config(cfg: models.ConfigFile, path: str | pathlib.Path) -> None:
    raw = cfg.to_dict(include_metadata=True)
    vr = validate_contract(raw)
    if not vr.ok:
        raise ValueError(f"Nelze ulozit nevalidni konfiguraci: {[e.message for e in vr.errors]}")
    # Atomicky zapis: temp file + rename
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(p.parent), prefix=".tmp_config_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, p)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def canonicalize_dict(raw: dict) -> dict:
    """Vrati semanticky obsah bez dynamickych metadat pro porovnani."""
    d = dict(raw)
    d.pop("createdAt", None)
    d.pop("generator", None)
    # calculatorCompatibility.maxVersion je dynamicke, ale minVersion je semanticke
    comp = d.get("calculatorCompatibility")
    if isinstance(comp, dict):
        # keep minVersion, drop maxVersion for canonical compare? Keep both but normalize null
        pass
    return d


def save_raw_atomic(raw: dict, path: str | pathlib.Path) -> None:
    """Ulozi raw dict atomicky (bez validace)."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(p.parent), prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(raw, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, p)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
