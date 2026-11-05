"""Tab Sady — list sad + složek, preview tabulka, merge logika."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QGroupBox, QSplitter, QInputDialog, QFileDialog
)
from ..announce import announce
from ..models import StatisticsFile, StatisticsSet, StatisticsFolder, generate_stats_id
from ..statistics_io import merge_statistics
from .folder_editor import FolderEditorDialog
from .set_editor import SetEditorDialog

class SetsTabWidget(QWidget):
    def __init__(self, stats: StatisticsFile, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.setAccessibleName("Záložka sady")
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        # Top row: folders + sets
        splitter = QSplitter(Qt.Orientation.Horizontal)
        # Folders box
        fBox = QGroupBox("Složky"); fBox.setAccessibleName("Skupina složek")
        fl = QVBoxLayout(fBox)
        self.folderList = QListWidget(); self.folderList.setAccessibleName("Seznam složek")
        self.folderList.currentRowChanged.connect(self._on_folder_selected)
        fl.addWidget(QLabel("Složky (výběr filtruje sady):"))
        fl.addWidget(self.folderList)
        row = QHBoxLayout()
        self.btnAddFolder = QPushButton("Nová složka"); self.btnAddFolder.setAccessibleName("Vytvořit novou složku")
        self.btnEditFolder = QPushButton("Upravit složku"); self.btnEditFolder.setAccessibleName("Upravit vybranou složku")
        self.btnDelFolder = QPushButton("Smazat složku"); self.btnDelFolder.setAccessibleName("Smazat vybranou složku")
        for b in (self.btnAddFolder, self.btnEditFolder, self.btnDelFolder):
            row.addWidget(b)
        fl.addLayout(row)
        self.btnAddFolder.clicked.connect(self._add_folder)
        self.btnEditFolder.clicked.connect(self._edit_folder)
        self.btnDelFolder.clicked.connect(self._del_folder)
        splitter.addWidget(fBox)

        # Sets box
        sBox = QGroupBox("Sady"); sBox.setAccessibleName("Skupina sad")
        sl = QVBoxLayout(sBox)
        self.setList = QListWidget(); self.setList.setAccessibleName("Seznam sad")
        self.setList.currentRowChanged.connect(self._on_set_selected)
        self.setList.itemDoubleClicked.connect(lambda _: self._edit_set())
        sl.addWidget(QLabel("Sady:"))
        sl.addWidget(self.setList)
        btnRow = QHBoxLayout()
        self.btnAddSet = QPushButton("Vytvořit sadu"); self.btnAddSet.setAccessibleName("Vytvořit novou sadu")
        self.btnEditSet = QPushButton("Upravit"); self.btnEditSet.setAccessibleName("Upravit vybranou sadu")
        self.btnDupSet = QPushButton("Duplikovat"); self.btnDupSet.setAccessibleName("Duplikovat sadu")
        self.btnDelSet = QPushButton("Smazat"); self.btnDelSet.setAccessibleName("Smazat sadu")
        for b in (self.btnAddSet, self.btnEditSet, self.btnDupSet, self.btnDelSet):
            btnRow.addWidget(b)
        sl.addLayout(btnRow)
        splitter.addWidget(sBox)
        splitter.setSizes([300, 400])
        layout.addWidget(splitter, 2)

        # Preview table
        previewBox = QGroupBox("Náhled dat (prvních 20 řádků)"); previewBox.setAccessibleName("Skupina náhled dat")
        pv = QVBoxLayout(previewBox)
        self.previewTable = QTableWidget(); self.previewTable.setAccessibleName("Náhled tabulky dat")
        self.previewTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        pv.addWidget(self.previewTable)
        layout.addWidget(previewBox, 2)

        # Bottom: import/export statistics file
        bottom = QHBoxLayout()
        self.btnOpenStats = QPushButton("Otevřít sady…"); self.btnOpenStats.setAccessibleName("Otevřít soubor sad")
        self.btnSaveStats = QPushButton("Uložit sady…"); self.btnSaveStats.setAccessibleName("Uložit soubor sad")
        self.btnMergeStats = QPushButton("Sloučit sady ze souboru…"); self.btnMergeStats.setAccessibleName("Sloučit sady ze souboru merge")
        for b in (self.btnOpenStats, self.btnSaveStats, self.btnMergeStats):
            bottom.addWidget(b)
        bottom.addStretch()
        layout.addLayout(bottom)

        # connections
        self.btnAddSet.clicked.connect(self._add_set)
        self.btnEditSet.clicked.connect(self._edit_set)
        self.btnDupSet.clicked.connect(self._dup_set)
        self.btnDelSet.clicked.connect(self._del_set)
        self.btnOpenStats.clicked.connect(self._open_stats_file)
        self.btnSaveStats.clicked.connect(self._save_stats_file)
        self.btnMergeStats.clicked.connect(self._merge_stats_file)

    def refresh(self):
        # folders
        self.folderList.clear()
        itemAll = QListWidgetItem("Vše"); itemAll.setData(Qt.ItemDataRole.UserRole, None)
        self.folderList.addItem(itemAll)
        itemNone = QListWidgetItem("Bez složky"); itemNone.setData(Qt.ItemDataRole.UserRole, "none")
        self.folderList.addItem(itemNone)
        for f in self.stats.folders:
            it = QListWidgetItem(f"{f.name} ({f.iconName} {f.colorIndex})")
            it.setData(Qt.ItemDataRole.UserRole, f.id)
            self.folderList.addItem(it)
        if self.folderList.count()>0 and self.folderList.currentRow()<0:
            self.folderList.setCurrentRow(0)
        self._refresh_sets()
        self._update_buttons()

    def _current_folder_filter(self):
        row = self.folderList.currentRow()
        if row<=0:
            return None if row==0 else "none"
        it = self.folderList.item(row)
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def _refresh_sets(self):
        filt = self._current_folder_filter()
        self.setList.clear()
        for s in self.stats.sets:
            if filt is None:
                pass
            elif filt=="none":
                if s.folderId is not None: continue
            else:
                if s.folderId != filt: continue
            label = f"{s.name}  [{', '.join(s.fieldNames)}]  ({len(s.records)} řádků){' 📌' if s.pinned else ''}{' 📦' if s.archived else ''}  id:{s.id[:8]}"
            it = QListWidgetItem(label); it.setData(Qt.ItemDataRole.UserRole, s.id)
            self.setList.addItem(it)
        if self.setList.count()>0 and self.setList.currentRow()<0:
            self.setList.setCurrentRow(0)
        self._refresh_preview()

    def _on_folder_selected(self, _):
        self._refresh_sets(); self._update_buttons()

    def _on_set_selected(self, _):
        self._refresh_preview(); self._update_buttons()

    def _update_buttons(self):
        has_set = self.setList.currentRow()>=0
        has_folder = self.folderList.currentRow()>=2
        self.btnEditSet.setEnabled(has_set)
        self.btnDupSet.setEnabled(has_set)
        self.btnDelSet.setEnabled(has_set)
        self.btnEditFolder.setEnabled(has_folder)
        self.btnDelFolder.setEnabled(has_folder)

    def _refresh_preview(self):
        s = self._selected_set()
        self.previewTable.clear()
        if not s:
            self.previewTable.setRowCount(0); self.previewTable.setColumnCount(0); return
        self.previewTable.setColumnCount(len(s.fieldNames))
        self.previewTable.setHorizontalHeaderLabels(s.fieldNames)
        rows = min(20, len(s.records))
        self.previewTable.setRowCount(rows)
        for r in range(rows):
            rec = s.records[r]
            for c, val in enumerate(rec.values):
                self.previewTable.setItem(r, c, QTableWidgetItem(str(val).replace(".", ",")))

    def _selected_set(self) -> StatisticsSet | None:
        row = self.setList.currentRow()
        if row<0: return None
        it = self.setList.item(row)
        if not it: return None
        sid = it.data(Qt.ItemDataRole.UserRole)
        for s in self.stats.sets:
            if s.id==sid: return s
        return None

    def _selected_folder(self) -> StatisticsFolder | None:
        row=self.folderList.currentRow()
        if row<2: return None
        it=self.folderList.item(row)
        fid=it.data(Qt.ItemDataRole.UserRole)
        for f in self.stats.folders:
            if f.id==fid: return f
        return None

    # --- folder ops ---
    def _add_folder(self):
        dlg=FolderEditorDialog(None, self)
        if dlg.exec()==dlg.DialogCode.Accepted:
            f=dlg.result_folder()
            self.stats.folders.append(f); self.refresh()
            announce(f"Přidána složka {f.name}.")

    def _edit_folder(self):
        f=self._selected_folder()
        if not f: return
        dlg=FolderEditorDialog(f, self)
        if dlg.exec()==dlg.DialogCode.Accepted:
            self.refresh()
            announce(f"Složka {f.name} uložena.")

    def _del_folder(self):
        f=self._selected_folder()
        if not f: return
        ret=QMessageBox.question(self, "Smazat složku", f"Smazat složku '{f.name}'? Sady v ní zůstanou (bez složky).", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ret!=QMessageBox.StandardButton.Yes: return
        self.stats.folders = [x for x in self.stats.folders if x.id!=f.id]
        for s in self.stats.sets:
            if s.folderId==f.id: s.folderId=None
        self.refresh()
        announce(f"Složka {f.name} smazána.")

    # --- set ops ---
    def _add_set(self):
        s=StatisticsSet(id=generate_stats_id(), name="Nová sada", fieldNames=["Hodnota"], fieldUnits=[None], records=[])
        dlg=SetEditorDialog(s, self.stats.folders, self)
        if dlg.exec()==dlg.DialogCode.Accepted:
            ns=dlg.result_set()
            self.stats.sets.append(ns); self.stats.currentIndex=len(self.stats.sets)-1
            self.refresh()
            announce(f"Přidána sada {ns.name}.")

    def _edit_set(self):
        s=self._selected_set()
        if not s: return
        dlg=SetEditorDialog(s, self.stats.folders, self)
        if dlg.exec()==dlg.DialogCode.Accepted:
            self.refresh()
            announce(f"Sada {s.name} uložena.")

    def _dup_set(self):
        s=self._selected_set()
        if not s: return
        import copy
        dup=StatisticsSet.from_dict(copy.deepcopy(s.to_dict()))
        dup.id=generate_stats_id()
        dup.name=s.name+" (kopie)"
        self.stats.sets.append(dup); self.refresh()
        announce(f"Vytvořena kopie sady {s.name}.")

    def _del_set(self):
        s=self._selected_set()
        if not s: return
        ret=QMessageBox.question(self, "Smazat sadu", f"Smazat sadu '{s.name}' ({len(s.records)} řádků)?", QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
        if ret!=QMessageBox.StandardButton.Yes: return
        self.stats.sets = [x for x in self.stats.sets if x.id!=s.id]
        if self.stats.currentIndex>=len(self.stats.sets):
            self.stats.currentIndex=max(0, len(self.stats.sets)-1)
        self.refresh()
        announce(f"Sada {s.name} smazána.")

    # --- file ops ---
    def _open_stats_file(self):
        path,_=QFileDialog.getOpenFileName(self, "Otevřít sady", "", "JSON (*.json)")
        if not path: return
        from ..statistics_io import load_statistics
        try:
            sf, vr = load_statistics(path)
            if vr.warnings:
                QMessageBox.warning(self, "Varování", "\n".join(f"{w.path}: {w.message}" for w in vr.warnings))
            self.stats=sf; self.refresh()
            QMessageBox.information(self, "Načteno", f"Načteno {len(sf.sets)} sad, {len(sf.folders)} složek.")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))

    def _save_stats_file(self):
        path,_=QFileDialog.getSaveFileName(self, "Uložit sady", "mluvici_kalkulacka_statistics_v1.json", "JSON (*.json)")
        if not path: return
        from ..statistics_io import save_statistics
        from ..statistics_validator import validate_statistics
        raw=self.stats.to_dict(include_metadata=True)
        vr=validate_statistics(raw)
        if not vr.ok:
            QMessageBox.critical(self, "Validace", "\n".join(f"{e.path}: {e.message}" for e in vr.errors)); return
        try:
            save_statistics(self.stats, path)
            QMessageBox.information(self, "Uloženo", f"Uloženo {path}\nPřeneste do telefonu a importujte: Více možností → Importovat sady (statistics, merge).")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))

    def _merge_stats_file(self):
        path,_=QFileDialog.getOpenFileName(self, "Vybrat soubor ke sloučení", "", "JSON (*.json)")
        if not path: return
        # ask conflict strategy
        choice, ok = QInputDialog.getItem(self, "Strategie duplicit", "Duplicitní název sady:", ["Přeskočit","Přejmenovat","Přepsat"], 1, False)
        if not ok: return
        mapping={"Přeskočit":"skip","Přejmenovat":"rename","Přepsat":"overwrite"}
        strategy=mapping.get(choice,"rename")
        from ..statistics_io import load_statistics, merge_statistics
        try:
            incoming,_=load_statistics(path)
            merged, log = merge_statistics(self.stats, incoming, on_conflict=strategy)
            self.stats=merged; self.refresh()
            QMessageBox.information(self, "Sloučeno", "\n".join(log) if log else "Žádné změny.")
        except Exception as e:
            QMessageBox.critical(self, "Chyba", str(e))
