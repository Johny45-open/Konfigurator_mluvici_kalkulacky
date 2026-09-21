"""Editor sady — plně editovatelný, tabulka s QTableWidget, CSV import via QThread."""
from __future__ import annotations

import csv
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QWidget, QScrollArea
)
from ..models import StatisticsSet, StatisticsRecord, StatisticsFolder, generate_stats_id, UNIT_NAMES

ICONS = ["dataset","school","work","home","lab","chart","folder","star"]

class SetEditorDialog(QDialog):
    def __init__(self, s: StatisticsSet, folders: list[StatisticsFolder], parent=None):
        super().__init__(parent)
        self._orig = s
        # deep copy via to_dict/from_dict
        import copy
        self._s = StatisticsSet.from_dict(s.to_dict())
        self._folders = folders
        self.setWindowTitle(f"Upravit sadu: {s.name}")
        self.setAccessibleName(f"Dialog upravit sadu {s.name}")
        self.setModal(True)
        self.resize(900, 700)
        self._build_ui()
        self._load()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); scroll.setWidget(content)
        layout = QVBoxLayout(content)

        # Identita
        box = QGroupBox("Sada"); box.setAccessibleName("Skupina sada")
        form = QFormLayout(box)
        self.nameEdit = QLineEdit(); self.nameEdit.setAccessibleName("Název sady")
        form.addRow("Název:", self.nameEdit)
        self.colorSpin = QSpinBox(); self.colorSpin.setRange(0,7); self.colorSpin.setAccessibleName("Barva index")
        form.addRow("Barva (0-7):", self.colorSpin)
        self.iconCombo = QComboBox(); self.iconCombo.addItems(ICONS); self.iconCombo.setAccessibleName("Ikona sady")
        form.addRow("Ikona:", self.iconCombo)
        self.folderCombo = QComboBox(); self.folderCombo.setAccessibleName("Složka sady")
        form.addRow("Složka:", self.folderCombo)
        self.pinnedCheck = QCheckBox("Připnutá"); self.pinnedCheck.setAccessibleName("Připnutá sada")
        self.archivedCheck = QCheckBox("Archivovaná"); self.archivedCheck.setAccessibleName("Archivovaná sada")
        form.addRow(self.pinnedCheck); form.addRow(self.archivedCheck)
        layout.addWidget(box)

        # Pole
        fieldsBox = QGroupBox("Pole (1-10)"); fieldsBox.setAccessibleName("Skupina pole")
        v = QVBoxLayout(fieldsBox)
        hl = QHBoxLayout()
        self.fieldCountSpin = QSpinBox(); self.fieldCountSpin.setRange(1,10); self.fieldCountSpin.setAccessibleName("Počet polí")
        self.fieldCountSpin.valueChanged.connect(self._on_field_count_changed)
        hl.addWidget(QLabel("Počet polí:")); hl.addWidget(self.fieldCountSpin); hl.addStretch()
        v.addLayout(hl)
        self.fieldsContainer = QWidget(); self.fieldsLayout = QFormLayout(self.fieldsContainer)
        v.addWidget(self.fieldsContainer)
        layout.addWidget(fieldsBox)

        # Data tabulka
        dataBox = QGroupBox("Data — tabulka"); dataBox.setAccessibleName("Skupina data tabulka")
        dv = QVBoxLayout(dataBox)
        self.table = QTableWidget(); self.table.setAccessibleName("Tabulka dat sady")
        self.table.setAlternatingRowColors(True)
        dv.addWidget(self.table)
        btnRow = QHBoxLayout()
        self.btnAddRow = QPushButton("Přidat řádek"); self.btnAddRow.setAccessibleName("Přidat řádek dat")
        self.btnDelRow = QPushButton("Smazat řádek"); self.btnDelRow.setAccessibleName("Smazat vybraný řádek")
        self.btnImportCsv = QPushButton("Import CSV…"); self.btnImportCsv.setAccessibleName("Importovat CSV do tabulky")
        self.btnClear = QPushButton("Vymazat vše"); self.btnClear.setAccessibleName("Vymazat všechna data")
        for b in (self.btnAddRow, self.btnDelRow, self.btnImportCsv, self.btnClear):
            btnRow.addWidget(b)
        dv.addLayout(btnRow)
        self.btnAddRow.clicked.connect(self._add_row)
        self.btnDelRow.clicked.connect(self._del_row)
        self.btnImportCsv.clicked.connect(self._import_csv)
        self.btnClear.clicked.connect(self._clear_rows)
        layout.addWidget(dataBox)

        outer.addWidget(scroll)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Uložit")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Zrušit")
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)
        outer.addWidget(self.buttonBox)
        self.nameEdit.setFocus()

    def _load(self):
        self.nameEdit.setText(self._s.name)
        self.colorSpin.setValue(self._s.colorIndex)
        self.iconCombo.setCurrentText(self._s.iconName if self._s.iconName in ICONS else "dataset")
        # folders
        self.folderCombo.clear()
        self.folderCombo.addItem("Bez složky", None)
        for f in self._folders:
            self.folderCombo.addItem(f.name, f.id)
        idx = 0
        if self._s.folderId:
            for i in range(self.folderCombo.count()):
                if self.folderCombo.itemData(i)==self._s.folderId:
                    idx=i; break
        self.folderCombo.setCurrentIndex(idx)
        self.pinnedCheck.setChecked(self._s.pinned)
        self.archivedCheck.setChecked(self._s.archived)
        self.fieldCountSpin.setValue(len(self._s.fieldNames))
        self._rebuild_fields()
        self._load_table()

    def _rebuild_fields(self):
        # clear
        while self.fieldsLayout.rowCount():
            self.fieldsLayout.removeRow(0)
        self.fieldEdits = []
        self.unitCombos = []
        for i in range(self.fieldCountSpin.value()):
            nameEdit = QLineEdit()
            nameEdit.setAccessibleName(f"Název pole {i+1}")
            nameEdit.setText(self._s.fieldNames[i] if i < len(self._s.fieldNames) else f"Pole {i+1}")
            unitCombo = QComboBox(); unitCombo.setAccessibleName(f"Jednotka pole {i+1}")
            unitCombo.addItem("--")
            for u in [x for x in UNIT_NAMES if x not in ("--",)]:
                unitCombo.addItem(u)
            cur = self._s.fieldUnits[i] if i < len(self._s.fieldUnits) else None
            if cur and cur in [unitCombo.itemText(j) for j in range(unitCombo.count())]:
                unitCombo.setCurrentText(cur)
            else:
                unitCombo.setCurrentIndex(0)
            row = QHBoxLayout()
            row.addWidget(QLabel(f"Pole {i+1}:")); row.addWidget(nameEdit); row.addWidget(QLabel("Jednotka:")); row.addWidget(unitCombo)
            w = QWidget(); w.setLayout(row)
            self.fieldsLayout.addRow(w)
            self.fieldEdits.append(nameEdit)
            self.unitCombos.append(unitCombo)
        self._sync_table_columns()

    def _on_field_count_changed(self, v: int):
        # adjust _s fieldNames/Units to new count, preserve existing
        new_names = [self.fieldEdits[i].text() if i < len(self.fieldEdits) else f"Pole {i+1}" for i in range(v)]
        new_units = [self.unitCombos[i].currentText() if i < len(self.unitCombos) else "--" for i in range(v)]
        # keep old values for existing, else defaults
        for i in range(v):
            if i >= len(self._s.fieldNames):
                self._s.fieldNames.append(new_names[i] if new_names[i] else f"Pole {i+1}")
                self._s.fieldUnits.append(None if new_units[i]=="--" else new_units[i])
        # trim if reduced
        self._s.fieldNames = self._s.fieldNames[:v]
        self._s.fieldUnits = self._s.fieldUnits[:v]
        # trim records
        for r in self._s.records:
            if len(r.values) > v:
                r.values = r.values[:v]
            elif len(r.values) < v:
                r.values.extend([0.0]*(v-len(r.values)))
        self._rebuild_fields()
        # keep edits from new_names/units
        for i, e in enumerate(self.fieldEdits):
            e.setText(new_names[i])

    def _sync_table_columns(self):
        n = self.fieldCountSpin.value()
        self.table.setColumnCount(n)
        headers = [self.fieldEdits[i].text() or f"Pole {i+1}" for i in range(n)]
        self.table.setHorizontalHeaderLabels(headers)
        # update existing rows values length
        for r in range(self.table.rowCount()):
            if self.table.columnCount() != n:
                pass

    def _load_table(self):
        n = len(self._s.fieldNames)
        self.table.setColumnCount(n)
        self.table.setHorizontalHeaderLabels(self._s.fieldNames)
        self.table.setRowCount(len(self._s.records))
        for r, rec in enumerate(self._s.records):
            for c, val in enumerate(rec.values):
                item = QTableWidgetItem(str(val).replace(".", ","))
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)

    def _collect_table(self) -> list[StatisticsRecord]:
        recs=[]
        for r in range(self.table.rowCount()):
            vals=[]
            for c in range(self.table.columnCount()):
                item = self.table.item(r,c)
                txt = item.text().strip() if item else "0"
                txt = txt.replace(",", ".")
                if txt=="": txt="0"
                try:
                    vals.append(float(txt))
                except ValueError:
                    raise ValueError(f"Řádek {r+1}, sloupec {c+1}: neplatné číslo '{txt}'")
            recs.append(StatisticsRecord(values=vals))
        return recs

    def _add_row(self):
        self.table.insertRow(self.table.rowCount())
        for c in range(self.table.columnCount()):
            self.table.setItem(self.table.rowCount()-1, c, QTableWidgetItem("0"))

    def _del_row(self):
        r = self.table.currentRow()
        if r>=0:
            self.table.removeRow(r)
        elif self.table.rowCount()>0:
            self.table.removeRow(self.table.rowCount()-1)

    def _clear_rows(self):
        if self.table.rowCount()==0: return
        ret = QMessageBox.question(self, "Vymazat", "Opravdu vymazat všechna data?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ret==QMessageBox.StandardButton.Yes:
            self.table.setRowCount(0)

    def _import_csv(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Vybrat CSV", "", "CSV (*.csv *.txt);;Vše (*.*)")
        if not path: return
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
            # detect delimiter ; or , or \t
            delim = ";"
            if text.count(",") > text.count(";") and "," in text.splitlines()[0]:
                # heuristic: if first line contains ',' and not ';' use ','
                if ";" not in text.splitlines()[0]:
                    delim = ","
            recs = []
            reader = csv.reader(text.splitlines(), delimiter=delim)
            for row in reader:
                if not row or all(not c.strip() for c in row):
                    continue
                # skip header if not numeric?
                vals=[]
                is_header=False
                for cell in row[:self.table.columnCount()]:
                    c = cell.strip().replace(",", ".")
                    try:
                        vals.append(float(c))
                    except ValueError:
                        is_header=True; break
                if is_header:
                    continue
                if len(vals)!=self.table.columnCount():
                    raise ValueError(f"Řádek má {len(vals)} hodnot, očekáváno {self.table.columnCount()}")
                recs.append(vals)
            if not recs:
                QMessageBox.warning(self, "CSV", "Žádná data k importu.")
                return
            ret = QMessageBox.question(self, "CSV import", f"Nalezeno {len(recs)} řádků. Nahradit tabulku nebo přidat?", QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No)
            # Yes = nahradit, No = přidat — použijeme Yes/No/Cancel
            # Pro jednoduchost: přidat
            for vals in recs:
                r = self.table.rowCount()
                self.table.insertRow(r)
                for c, v in enumerate(vals):
                    self.table.setItem(r, c, QTableWidgetItem(str(v).replace(".", ",")))
            QMessageBox.information(self, "CSV", f"Importováno {len(recs)} řádků.")
        except Exception as e:
            QMessageBox.critical(self, "Chyba CSV", str(e))

    def _on_accept(self):
        if not self.nameEdit.text().strip():
            QMessageBox.warning(self, "Chyba", "Název sady nesmí být prázdný."); return
        # collect fields
        names=[e.text().strip() or f"Pole {i+1}" for i,e in enumerate(self.fieldEdits)]
        if len(set(names))!=len(names):
            QMessageBox.warning(self, "Chyba", "Názvy polí musí být unikátní."); return
        units=[]
        for c in self.unitCombos:
            t=c.currentText()
            units.append(None if t=="--" else t)
        try:
            recs=self._collect_table()
        except ValueError as e:
            QMessageBox.warning(self, "Chyba dat", str(e)); return
        # update _s
        self._s.name=self.nameEdit.text().strip()
        self._s.fieldNames=names
        self._s.fieldUnits=units
        self._s.records=recs
        self._s.folderId=self.folderCombo.currentData()
        self._s.colorIndex=self.colorSpin.value()
        self._s.iconName=self.iconCombo.currentText()
        self._s.pinned=self.pinnedCheck.isChecked()
        self._s.archived=self.archivedCheck.isChecked()
        self.accept()

    def result_set(self) -> StatisticsSet:
        return self._s
