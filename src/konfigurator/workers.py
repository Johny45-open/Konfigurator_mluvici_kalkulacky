"""QThread workers pro neblokujici IO/validaci."""
from __future__ import annotations

import pathlib

from PyQt6.QtCore import QThread, pyqtSignal

from . import models
from .io import load_raw, save_config
from .validator import ValidationResult, validate_contract


class LoadWorker(QThread):
    finished_ok = pyqtSignal(object, object)  # ConfigFile, ValidationResult
    finished_warn = pyqtSignal(object, object)  # same but with warnings
    error = pyqtSignal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    def run(self) -> None:
        try:
            raw = load_raw(self.path)
            vr = validate_contract(raw)
            if not vr.ok:
                self.error.emit("; ".join(f"{e.path}: {e.message}" for e in vr.errors))
                return
            cfg = models.ConfigFile.from_dict(raw)
            if vr.warnings:
                self.finished_warn.emit(cfg, vr)
            else:
                self.finished_ok.emit(cfg, vr)
        except Exception as e:
            self.error.emit(str(e))


class SaveWorker(QThread):
    finished_ok = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, cfg: models.ConfigFile, path: str):
        super().__init__()
        self.cfg = cfg
        self.path = path

    def run(self) -> None:
        try:
            save_config(self.cfg, self.path)
            self.finished_ok.emit(self.path)
        except Exception as e:
            self.error.emit(str(e))


class ValidateWorker(QThread):
    finished = pyqtSignal(object)  # ValidationResult

    def __init__(self, raw: dict):
        super().__init__()
        self.raw = raw

    def run(self) -> None:
        vr = validate_contract(self.raw)
        self.finished.emit(vr)
