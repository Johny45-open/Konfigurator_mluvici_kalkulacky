from PyQt6.QtCore import QThread, pyqtSignal
from .statistics_io import load_raw, parse_csv
from .statistics_validator import validate_statistics
from .models import StatisticsFile

class LoadStatsWorker(QThread):
    finished_ok = pyqtSignal(object, object)
    finished_warn = pyqtSignal(object, object)
    error = pyqtSignal(str)
    def __init__(self, path: str):
        super().__init__(); self.path=path
    def run(self):
        try:
            raw=load_raw(self.path)
            vr=validate_statistics(raw)
            if not vr.ok:
                self.error.emit("; ".join(f"{e.path}: {e.message}" for e in vr.errors)); return
            sf=StatisticsFile.from_dict(raw)
            if vr.warnings: self.finished_warn.emit(sf, vr)
            else: self.finished_ok.emit(sf, vr)
        except Exception as e:
            self.error.emit(str(e))

class SaveStatsWorker(QThread):
    finished_ok = pyqtSignal(str); error=pyqtSignal(str)
    def __init__(self, sf, path: str):
        super().__init__(); self.sf=sf; self.path=path
    def run(self):
        try:
            from .statistics_io import save_statistics
            save_statistics(self.sf, self.path)
            self.finished_ok.emit(self.path)
        except Exception as e:
            self.error.emit(str(e))

class ParseCsvWorker(QThread):
    finished_ok = pyqtSignal(list); error=pyqtSignal(str)
    def __init__(self, text: str, field_count: int, delimiter: str=";"):
        super().__init__(); self.text=text; self.field_count=field_count; self.delimiter=delimiter
    def run(self):
        try:
            from .statistics_io import parse_csv
            recs=parse_csv(self.text, self.field_count, self.delimiter)
            self.finished_ok.emit(recs)
        except Exception as e:
            self.error.emit(str(e))
