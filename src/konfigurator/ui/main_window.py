"""Hlavni okno konfiguratoru — pristupne, Tab order, skupina profilu + global + import/export."""
from __future__ import annotations

import copy
import pathlib

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import models
from ..announce import announce
from ..io import save_config
from ..models import AccessibilityProfile, ConfigFile, GlobalSettings, StatisticsFile
from ..workers import LoadWorker, SaveWorker
from .dialogs import show_error, show_info, show_warning
from .global_settings import GlobalSettingsWidget
from .profile_editor import ProfileEditorDialog
from .sets_tab import SetsTabWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Konfigurátor mluvící kalkulačky")
        self.setAccessibleName("Hlavní okno konfigurátoru mluvící kalkulačky")
        self.resize(1000, 700)
        self._config = self._default_config()
        self._stats = StatisticsFile()
        self._current_file: str | None = None
        self._workers: list = []
        self._build_ui()
        self._refresh_profile_list()
        self._update_status()

    def _default_config(self) -> ConfigFile:
        profiles = [
            AccessibilityProfile(id="standard", name="Standardní", isBuiltIn=True, settings=models.AccessibilitySettings.defaults_standard()),
            AccessibilityProfile(id="blind", name="Nevidomý", isBuiltIn=True, settings=models.AccessibilitySettings.defaults_blind()),
            AccessibilityProfile(id="lowvision", name="Slabozraký", isBuiltIn=True, settings=models.AccessibilitySettings.defaults_low_vision()),
        ]
        return ConfigFile(activeProfileId="standard", profiles=profiles, globalSettings=GlobalSettings())

    def _build_ui(self) -> None:
        central = QWidget()
        central.setAccessibleName("Hlavní obsah")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Top bar: Nový / Otevřít / Uložit / Uložit jako
        top = QHBoxLayout()
        self.btnNew = QPushButton("Nový")
        self.btnNew.setAccessibleName("Vytvořit novou konfiguraci")
        self.btnOpen = QPushButton("Otevřít…")
        self.btnOpen.setAccessibleName("Otevřít konfigurační soubor")
        self.btnSave = QPushButton("Uložit")
        self.btnSave.setAccessibleName("Uložit konfiguraci")
        self.btnSaveAs = QPushButton("Uložit jako…")
        self.btnSaveAs.setAccessibleName("Uložit konfiguraci jako")
        self.btnValidate = QPushButton("Zkontrolovat")
        self.btnValidate.setAccessibleName("Zkontrolovat konfiguraci")
        for b in (self.btnNew, self.btnOpen, self.btnSave, self.btnSaveAs, self.btnValidate):
            top.addWidget(b)
        top.addStretch()
        root.addLayout(top)
        self.btnNew.clicked.connect(self.on_new)
        self.btnOpen.clicked.connect(self.on_open)
        self.btnSave.clicked.connect(self.on_save)
        self.btnSaveAs.clicked.connect(self.on_save_as)
        self.btnValidate.clicked.connect(self.on_validate)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("Záložky konfigurace")
        root.addWidget(self.tabs)

        # Tab Profily
        self.tabProfiles = QWidget()
        self.tabProfiles.setAccessibleName("Záložka profily")
        self.tabs.addTab(self.tabProfiles, "Profily")
        self._build_profiles_tab()

        # Tab Global
        self.globalWidget = GlobalSettingsWidget(self._config.globalSettings)
        self.globalWidget.setAccessibleName("Záložka globální nastavení")
        self.tabs.addTab(self.globalWidget, "Globální")

        # Tab Sady
        self.setsTab = SetsTabWidget(self._stats)
        self.tabs.addTab(self.setsTab, "Sady")

        # Tab Info
        self.tabInfo = QWidget()
        self.tabInfo.setAccessibleName("Záložka informace")
        self.tabs.addTab(self.tabInfo, "Info")
        self._build_info_tab()

        # Status
        self.statusLabel = QLabel("")
        self.statusLabel.setAccessibleName("Stavová zpráva")
        root.addWidget(self.statusLabel)

        # Tab order
        self.setTabOrder(self.btnNew, self.btnOpen)
        self.setTabOrder(self.btnOpen, self.btnSave)
        self.setTabOrder(self.btnSave, self.btnSaveAs)
        self.setTabOrder(self.btnSaveAs, self.btnValidate)
        self.setTabOrder(self.btnValidate, self.tabs)

    def _build_profiles_tab(self) -> None:
        layout = QHBoxLayout(self.tabProfiles)
        # Left: list
        left = QVBoxLayout()
        self.profileList = QListWidget()
        self.profileList.setAccessibleName("Seznam profilů")
        self.profileList.setAccessibleDescription("Vyberte profil pro úpravu. Použijte šipky a Tab.")
        self.profileList.currentRowChanged.connect(self._on_profile_selected)
        left.addWidget(QLabel("Profily:"))
        left.addWidget(self.profileList)
        # Active combo
        self.activeCombo = QComboBox()
        self.activeCombo.setAccessibleName("Aktivní profil")
        self.activeCombo.setAccessibleDescription("Vyberte který profil bude aktivní po importu")
        left.addWidget(QLabel("Aktivní profil:"))
        left.addWidget(self.activeCombo)
        self.activeCombo.currentIndexChanged.connect(self._on_active_changed)
        layout.addLayout(left, 2)
        # Right: buttons
        right = QVBoxLayout()
        self.btnEdit = QPushButton("Upravit…")
        self.btnEdit.setAccessibleName("Upravit vybraný profil")
        self.btnDuplicate = QPushButton("Duplikovat")
        self.btnDuplicate.setAccessibleName("Duplikovat vybraný profil")
        self.btnCreate = QPushButton("Vytvořit nový")
        self.btnCreate.setAccessibleName("Vytvořit nový profil")
        self.btnRename = QPushButton("Přejmenovat…")
        self.btnRename.setAccessibleName("Přejmenovat vybraný profil")
        self.btnDelete = QPushButton("Smazat")
        self.btnDelete.setAccessibleName("Smazat vybraný profil")
        self.btnSetActive = QPushButton("Nastavit jako aktivní")
        self.btnSetActive.setAccessibleName("Nastavit vybraný profil jako aktivní")
        for b in (self.btnEdit, self.btnDuplicate, self.btnCreate, self.btnRename, self.btnDelete, self.btnSetActive):
            right.addWidget(b)
        right.addStretch()
        layout.addLayout(right, 1)
        # Connections
        self.btnEdit.clicked.connect(self.on_edit)
        self.btnDuplicate.clicked.connect(self.on_duplicate)
        self.btnCreate.clicked.connect(self.on_create)
        self.btnRename.clicked.connect(self.on_rename)
        self.btnDelete.clicked.connect(self.on_delete)
        self.btnSetActive.clicked.connect(self.on_set_active)
        self.profileList.itemDoubleClicked.connect(lambda _: self.on_edit())

    def _build_info_tab(self) -> None:
        layout = QVBoxLayout(self.tabInfo)
        info = QLabel(
            "Konfigurátor vytváří přenositelný JSON soubor s konfigurací mluvící kalkulačky.\n"
            "Soubor uložte a přeneste do telefonu (USB, e-mail, cloud) a importujte v kalkulačce: Nastavení → Zálohování → Import kontraktu.\n"
            "Schéma verze 1, kompatibilita minVersion 11.5.0.\n"
            "Vestavěné profily standard/blind/lowvision nelze smazat, lze je resetovat na výchozí.\n"
            "Změna jednoho profilu neovlivní jiný profil (izolace).\n"
            "Všechny ovládací prvky jsou ovladatelné klávesnicí: Tab, Shift+Tab, Enter, Space, Esc, šipky."
        )
        info.setWordWrap(True)
        info.setAccessibleName("Informace o konfigurátoru")
        info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        layout.addWidget(info)
        self.compatLabel = QLabel("")
        self.compatLabel.setAccessibleName("Kompatibilita")
        layout.addWidget(self.compatLabel)
        layout.addStretch()

    def _refresh_profile_list(self) -> None:
        self.profileList.clear()
        self.activeCombo.clear()
        for p in self._config.profiles:
            item = QListWidgetItem(f"{p.name}  ({p.id}){' [vestaveny]' if p.isBuiltIn else ''}")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.profileList.addItem(item)
            self.activeCombo.addItem(f"{p.name} ({p.id})", p.id)
        # select active
        for i, p in enumerate(self._config.profiles):
            if p.id == self._config.activeProfileId:
                self.profileList.setCurrentRow(i)
                self.activeCombo.setCurrentIndex(i)
                break
        self._update_buttons()

    def _on_profile_selected(self, row: int) -> None:
        self._update_buttons()

    def _update_buttons(self) -> None:
        row = self.profileList.currentRow()
        has_sel = 0 <= row < len(self._config.profiles)
        is_builtin = has_sel and self._config.profiles[row].isBuiltIn
        self.btnEdit.setEnabled(has_sel)
        self.btnDuplicate.setEnabled(has_sel)
        self.btnRename.setEnabled(has_sel and not is_builtin)
        self.btnDelete.setEnabled(has_sel and not is_builtin)
        self.btnSetActive.setEnabled(has_sel)

    def _on_active_changed(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._config.profiles):
            return
        # avoid recursion when refreshing
        pid = self.activeCombo.currentData()
        if pid and pid != self._config.activeProfileId:
            self._config.activeProfileId = pid
            self._update_status()

    def on_edit(self) -> None:
        row = self.profileList.currentRow()
        if row < 0:
            return
        prof = self._config.profiles[row]
        dlg = ProfileEditorDialog(prof, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            new_prof = dlg.result_profile()
            self._config.profiles[row] = new_prof
            self._refresh_profile_list()
            self.profileList.setCurrentRow(row)
            self._update_status()
            announce(f"Profil {new_prof.name} uložen.")

    def on_duplicate(self) -> None:
        row = self.profileList.currentRow()
        if row < 0:
            return
        src = self._config.profiles[row]
        new_id = models.generate_custom_id(src.name + "_kopie")
        dup = AccessibilityProfile(id=new_id, name=src.name + " (kopie)", isBuiltIn=False, settings=copy.deepcopy(src.settings))
        self._config.profiles.append(dup)
        self._refresh_profile_list()
        self.profileList.setCurrentRow(len(self._config.profiles) - 1)
        self._update_status()
        announce(f"Vytvořena kopie profilu {src.name}.")

    def on_create(self) -> None:
        # create from standard
        new_id = models.generate_custom_id("Novy profil")
        prof = AccessibilityProfile(id=new_id, name="Novy profil", isBuiltIn=False, settings=models.AccessibilitySettings.defaults_standard())
        dlg = ProfileEditorDialog(prof, self)
        dlg.setWindowTitle("Vytvorřit nový profil")
        if dlg.exec() == dlg.DialogCode.Accepted:
            new_prof = dlg.result_profile()
            # ensure id is still unique
            new_prof.id = new_id
            self._config.profiles.append(new_prof)
            self._refresh_profile_list()
            self.profileList.setCurrentRow(len(self._config.profiles) - 1)
            self._update_status()
            announce(f"Vytvořen profil {new_prof.name}.")

    def on_rename(self) -> None:
        row = self.profileList.currentRow()
        if row < 0:
            return
        prof = self._config.profiles[row]
        if prof.isBuiltIn:
            show_warning(self, "Nelze přejmenovat", "Vestavěné profily nelze přejmenovat.")
            return
        from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "Přejmenovat profil", "Nový název:", text=prof.name)
        if ok:
            name = text.strip()
            if not name:
                show_error(self, "Chyba", "Název nesmí být prázdný.")
                return
            if any(p.name.lower() == name.lower() for p in self._config.profiles if p.id != prof.id):
                show_error(self, "Chyba", "Profil s tímto názvem již existuje.")
                return
            prof.name = name
            self._refresh_profile_list()
            self.profileList.setCurrentRow(row)
            announce(f"Profil přejmenován na {name}.")

    def on_delete(self) -> None:
        row = self.profileList.currentRow()
        if row < 0:
            return
        prof = self._config.profiles[row]
        if prof.isBuiltIn:
            show_warning(self, "Nelze smazat", "Vestavěné profily nelze smazat. Můžete je resetovat na výchozí v kalkulačce.")
            return
        ret = QMessageBox.question(self, "Smazat profil", f"Opravdu smazat profil '{prof.name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return
        was_active = self._config.activeProfileId == prof.id
        del self._config.profiles[row]
        if was_active:
            self._config.activeProfileId = self._config.profiles[0].id if self._config.profiles else "standard"
        self._refresh_profile_list()
        self._update_status()
        announce(f"Profil {prof.name} smazán.")

    def on_set_active(self) -> None:
        row = self.profileList.currentRow()
        if row < 0:
            return
        pid = self._config.profiles[row].id
        self._config.activeProfileId = pid
        self._refresh_profile_list()
        self._update_status()
        announce(f"Aktivní profil {self._config.profiles[row].name}.")

    def _collect_global(self) -> None:
        self._config.globalSettings = self.globalWidget.collect()
        # sets tab drzi referenci na self._stats přímo, není třeba collect

    def _sync_sets(self) -> None:
        self._stats = self.setsTab.stats

    def _update_status(self) -> None:
        name = next((p.name for p in self._config.profiles if p.id == self._config.activeProfileId), self._config.activeProfileId)
        self.statusLabel.setText(f"Aktivní profil: {name}  |  Profilů: {len(self._config.profiles)}  |  Soubor: {self._current_file or 'neuloženo'}")
        self.compatLabel.setText(f"Kompatibilita: minVersion {self._config.minVersion}, schéma {self._config.schemaVersion}")

    # --- File ops with workers ---
    def on_new(self) -> None:
        ret = QMessageBox.question(self, "Nový", "Zahodit aktuální konfiguraci a vytvořit novou výchozí?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret != QMessageBox.StandardButton.Yes:
            return
        self._config = self._default_config()
        self.globalWidget.set_global(self._config.globalSettings)
        self._current_file = None
        self._refresh_profile_list()
        self._update_status()
        announce("Vytvořena nová konfigurace.")

    def on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Otevřít konfiguraci", "", "JSON (*.json);;Všechny (*.*)")
        if not path:
            return
        worker = LoadWorker(path)
        worker.finished_ok.connect(self._on_load_ok)
        worker.finished_warn.connect(self._on_load_warn)
        worker.error.connect(lambda msg: show_error(self, "Chyba při načítání", msg))
        worker.finished_ok.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        worker.finished_warn.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        worker.error.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        self._workers.append(worker)
        worker.start()

    def _on_load_ok(self, cfg: ConfigFile, vr) -> None:
        self._config = cfg
        self.globalWidget.set_global(cfg.globalSettings)
        self._current_file = None  # will be set on save; keep path? not to auto-overwrite
        # remember path for Save? store but require explicit Save As? keep for Save
        # we store _current_file as opened path for Save
        # find path from worker? Use last opened path stored?
        # Simplify: ask user to Save As
        self._refresh_profile_list()
        self._update_status()
        show_info(self, "Načteno", f"Konfigurace načtena ({len(cfg.profiles)} profilů). Zkontrolujte aktivní profil.")

    def _on_load_warn(self, cfg: ConfigFile, vr) -> None:
        self._on_load_ok(cfg, vr)
        warns = "\n".join(f"{w.path}: {w.message}" for w in vr.warnings)
        show_warning(self, "Varování", f"Konfigurace načtena s varováními (neznámá pole ignorována):\n{warns}")

    def on_save(self) -> None:
        if self._current_file:
            self._do_save(self._current_file)
        else:
            self.on_save_as()

    def on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Uložit konfiguraci", "mluvici_kalkulacka_config_v1.json", "JSON (*.json)")
        if not path:
            return
        self._do_save(path)

    def _do_save(self, path: str) -> None:
        self._collect_global()
        # Validate before save
        from ..validator import validate_contract

        raw = self._config.to_dict(include_metadata=True)
        vr = validate_contract(raw)
        if not vr.ok:
            msgs = "\n".join(f"{e.path}: {e.message}" for e in vr.errors)
            show_error(self, "Validace selhala", msgs)
            return
        if vr.warnings:
            warns = "\n".join(f"{w.path}: {w.message}" for w in vr.warnings)
            show_warning(self, "Varování", warns)
        worker = SaveWorker(self._config, path)
        worker.finished_ok.connect(lambda p: self._on_save_ok(p))
        worker.error.connect(lambda msg: show_error(self, "Chyba při ukládání", msg))
        worker.finished_ok.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        worker.error.connect(lambda *_: self._workers.remove(worker) if worker in self._workers else None)
        self._workers.append(worker)
        worker.start()

    def _on_save_ok(self, path: str) -> None:
        self._current_file = path
        self._update_status()
        show_info(self, "Uloženo", f"Konfigurace uložena:\n{path}\n\nPřeneste soubor do telefonu a importujte v kalkulačce: Nastavení → Import kontraktu.")

    def on_validate(self) -> None:
        self._collect_global()
        from ..validator import validate_contract

        raw = self._config.to_dict(include_metadata=True)
        vr = validate_contract(raw)
        if vr.ok and not vr.warnings:
            show_info(self, "Validace", "Konfigurace je validní.")
        elif vr.ok and vr.warnings:
            warns = "\n".join(f"{w.path}: {w.message}" for w in vr.warnings)
            show_warning(self, "Validace s varováním", f"Validní, ale s varováními:\n{warns}")
        else:
            msgs = "\n".join(f"{e.path}: {e.message}" for e in vr.errors)
            show_error(self, "Nevalidní", msgs)
