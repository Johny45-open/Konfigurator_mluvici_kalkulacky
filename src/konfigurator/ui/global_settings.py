"""Globální nastavení — GroupBoxy, ComboBoxy, SpinBoxy."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..models import (
    CALCULATOR_MODES,
    CALCULATOR_MODE_LABELS,
    COMPUTED_ITEM_LABELS,
    GlobalSettings,
    STATS_COMPUTED_ITEMS,
    STATS_SUMMARY_SECTIONS,
    SUMMARY_SECTION_LABELS,
    THEMES,
    THEME_LABELS,
)


def _set_combo_by_data(combo, value) -> None:
    """Nastavi rozbočník na položku, jejíž skryta hodnota se rovná value."""
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return
    combo.setCurrentIndex(0)


class GlobalSettingsWidget(QWidget):
    def __init__(self, gs: GlobalSettings, parent=None):
        super().__init__(parent)
        self._gs = gs
        self.setAccessibleName("Globální nastavení")
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Téma / režim
        themeBox = QGroupBox("Vzhled a režimy")
        themeBox.setAccessibleName("Skupina vzhled a režimy")
        f = QFormLayout(themeBox)
        self.themeCombo = QComboBox()
        self.themeCombo.setAccessibleName("Téma aplikace")
        for v in THEMES:
            self.themeCombo.addItem(THEME_LABELS[v], v)
        self.degreeCheck = QCheckBox("Stupně (Degree), jinak radiány")
        self.degreeCheck.setAccessibleName("Režim stupňů")
        self.defaultModeCombo = QComboBox()
        self.defaultModeCombo.setAccessibleName("Výchozí režim kalkulačky")
        for v in CALCULATOR_MODES:
            self.defaultModeCombo.addItem(CALCULATOR_MODE_LABELS[v], v)
        f.addRow("Téma:", self.themeCombo)
        f.addRow(self.degreeCheck)
        f.addRow("Výchozí režim:", self.defaultModeCombo)
        layout.addWidget(themeBox)

        # Statistické pořadí — zobrazení jako list s šipkami
        statsBox = QGroupBox("Statistika — pořadí")
        statsBox.setAccessibleName("Skupina statistika pořadí")
        sl = QVBoxLayout(statsBox)
        sl.addWidget(QLabel("Pořadí sekcí souhrnu (přesun šipkami):"))
        row1 = QHBoxLayout()
        self.summaryList = QListWidget()
        self.summaryList.setAccessibleName("Seznam pořadí sekcí souhrnu")
        self.summaryUp = QPushButton("Nahoru")
        self.summaryUp.setAccessibleName("Posunout sekci nahoru")
        self.summaryDown = QPushButton("Dolů")
        self.summaryDown.setAccessibleName("Posunout sekci dolů")
        self.summaryUp.clicked.connect(lambda: self._move_up(self.summaryList))
        self.summaryDown.clicked.connect(lambda: self._move_down(self.summaryList))
        row1.addWidget(self.summaryList)
        col = QVBoxLayout()
        col.addWidget(self.summaryUp)
        col.addWidget(self.summaryDown)
        col.addStretch()
        row1.addLayout(col)
        sl.addLayout(row1)

        sl.addWidget(QLabel("Pořadí vypočtených položek:"))
        row2 = QHBoxLayout()
        self.computedList = QListWidget()
        self.computedList.setAccessibleName("Seznam pořadí vypočtených položek")
        self.compUp = QPushButton("Nahoru")
        self.compUp.setAccessibleName("Posunout položku nahoru")
        self.compDown = QPushButton("Dolů")
        self.compDown.setAccessibleName("Posunout položku dolů")
        self.compUp.clicked.connect(lambda: self._move_up(self.computedList))
        self.compDown.clicked.connect(lambda: self._move_down(self.computedList))
        row2.addWidget(self.computedList)
        col2 = QVBoxLayout()
        col2.addWidget(self.compUp)
        col2.addWidget(self.compDown)
        col2.addStretch()
        row2.addLayout(col2)
        sl.addLayout(row2)
        layout.addWidget(statsBox)

        # Měna
        curBox = QGroupBox("Měna")
        curBox.setAccessibleName("Skupina měna")
        cf = QFormLayout(curBox)
        self.currencyFromCombo = QComboBox()
        self.currencyFromCombo.setAccessibleName("Měna z")
        self.currencyFromCombo.setEditable(True)
        self.currencyFromCombo.addItems(["CZK", "EUR", "USD", "GBP", "PLN", "HUF", "CHF", "JPY"])
        self.currencyToCombo = QComboBox()
        self.currencyToCombo.setAccessibleName("Měna na")
        self.currencyToCombo.setEditable(True)
        self.currencyToCombo.addItems(["CZK", "EUR", "USD", "GBP", "PLN", "HUF", "CHF", "JPY"])
        cf.addRow("Z:", self.currencyFromCombo)
        cf.addRow("Na:", self.currencyToCombo)
        layout.addWidget(curBox)

        # Dev
        devBox = QGroupBox("Vývojářský režim")
        devBox.setAccessibleName("Skupina vývojářský režim")
        df = QFormLayout(devBox)
        self.devEnabledCheck = QCheckBox("Povolit vývojářský režim")
        self.devEnabledCheck.setAccessibleName("Povolit vývojářský režim")
        self.devAutoCheck = QCheckBox("Auto diagnostika")
        self.devAutoCheck.setAccessibleName("Povolit auto diagnostiku")
        self.devDurationSpin = QSpinBox()
        self.devDurationSpin.setAccessibleName("Délka diagnostiky v ms")
        self.devDurationSpin.setRange(200, 3000)
        self.devDurationSpin.setSingleStep(100)
        self.devPinEdit = QLineEdit()
        self.devPinEdit.setAccessibleName("PIN kód (4 číslice, prázdné=žádný)")
        self.devPinEdit.setPlaceholderText("prázdné = bez PIN")
        self.devPinEdit.setMaxLength(4)
        df.addRow(self.devEnabledCheck)
        df.addRow(self.devAutoCheck)
        df.addRow("Délka (200-3000 ms):", self.devDurationSpin)
        df.addRow("PIN:", self.devPinEdit)
        layout.addWidget(devBox)
        layout.addStretch()

    def _move_up(self, lst: QListWidget) -> None:
        r = lst.currentRow()
        if r > 0:
            item = lst.takeItem(r)
            lst.insertItem(r - 1, item)
            lst.setCurrentRow(r - 1)

    def _move_down(self, lst: QListWidget) -> None:
        r = lst.currentRow()
        if 0 <= r < lst.count() - 1:
            item = lst.takeItem(r)
            lst.insertItem(r + 1, item)
            lst.setCurrentRow(r + 1)

    def _load(self) -> None:
        gs = self._gs
        _set_combo_by_data(self.themeCombo, gs.themeMode)
        self.degreeCheck.setChecked(gs.isDegreeMode)
        _set_combo_by_data(self.defaultModeCombo, gs.defaultMode)
        self.summaryList.clear()
        for s in gs.statsSummaryOrder:
            it = QListWidgetItem(SUMMARY_SECTION_LABELS.get(s, s))
            it.setData(Qt.ItemDataRole.UserRole, s)
            self.summaryList.addItem(it)
        self.computedList.clear()
        for c in gs.statsComputedOrder:
            it = QListWidgetItem(COMPUTED_ITEM_LABELS.get(c, c))
            it.setData(Qt.ItemDataRole.UserRole, c)
            self.computedList.addItem(it)
        self.currencyFromCombo.setCurrentText(gs.currencyFrom)
        self.currencyToCombo.setCurrentText(gs.currencyTo)
        self.devEnabledCheck.setChecked(gs.devEnabled)
        self.devAutoCheck.setChecked(gs.devAutoDiagnostic)
        self.devDurationSpin.setValue(gs.devDiagnosticDurationMs)
        self.devPinEdit.setText(gs.devPinCode or "")

    def collect(self) -> GlobalSettings:
        summary = [self.summaryList.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.summaryList.count())]
        computed = [self.computedList.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.computedList.count())]
        pin = self.devPinEdit.text().strip() or None
        # validate pin 4 digits if present
        if pin is not None and pin != "" and (len(pin) != 4 or not pin.isdigit()):
            pin = None
        return GlobalSettings(
            themeMode=self.themeCombo.currentData(),
            isDegreeMode=self.degreeCheck.isChecked(),
            defaultMode=self.defaultModeCombo.currentData(),
            statsSummaryOrder=summary if summary else list(STATS_SUMMARY_SECTIONS),
            statsComputedOrder=computed if computed else list(STATS_COMPUTED_ITEMS),
            currencyFrom=self.currencyFromCombo.currentText().strip() or "CZK",
            currencyTo=self.currencyToCombo.currentText().strip() or "EUR",
            devEnabled=self.devEnabledCheck.isChecked(),
            devAutoDiagnostic=self.devAutoCheck.isChecked(),
            devDiagnosticDurationMs=int(self.devDurationSpin.value()),
            devPinCode=pin,
        )

    def set_global(self, gs: GlobalSettings) -> None:
        self._gs = gs
        self._load()
