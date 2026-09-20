"""Globalni nastaveni — GroupBoxy, ComboBoxy, SpinBoxy."""
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..models import GlobalSettings


class GlobalSettingsWidget(QWidget):
    def __init__(self, gs: GlobalSettings, parent=None):
        super().__init__(parent)
        self._gs = gs
        self.setAccessibleName("Globalni nastaveni")
        self._build_ui()
        self._load()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Tema / rezim
        themeBox = QGroupBox("Vzhled a rezimy")
        themeBox.setAccessibleName("Skupina vzhled a rezimy")
        f = QFormLayout(themeBox)
        self.themeCombo = QComboBox()
        self.themeCombo.setAccessibleName("Tema aplikace")
        self.themeCombo.addItems(["light", "dark"])
        self.degreeCheck = QCheckBox("Stupne (Degree), jinak radiany")
        self.degreeCheck.setAccessibleName("Rezim stupnu")
        self.defaultModeCombo = QComboBox()
        self.defaultModeCombo.setAccessibleName("Vychozi rezim kalkulacky")
        self.defaultModeCombo.addItems(["basic", "scientific", "statistics", "electrician", "unitConversion", "time", "currency"])
        f.addRow("Tema:", self.themeCombo)
        f.addRow(self.degreeCheck)
        f.addRow("Vychozi rezim:", self.defaultModeCombo)
        layout.addWidget(themeBox)

        # Statisticke poradi — zobrazeni jako list s sipkami
        statsBox = QGroupBox("Statistika — poradi")
        statsBox.setAccessibleName("Skupina statistika poradi")
        sl = QVBoxLayout(statsBox)
        sl.addWidget(QLabel("Poradi sekci souhrnu (presun sipkami):"))
        row1 = QHBoxLayout()
        self.summaryList = QListWidget()
        self.summaryList.setAccessibleName("Seznam poradi sekci souhrnu")
        self.summaryUp = QPushButton("Nahoru")
        self.summaryUp.setAccessibleName("Posunout sekci nahoru")
        self.summaryDown = QPushButton("Dolu")
        self.summaryDown.setAccessibleName("Posunout sekci dolu")
        self.summaryUp.clicked.connect(lambda: self._move_up(self.summaryList))
        self.summaryDown.clicked.connect(lambda: self._move_down(self.summaryList))
        row1.addWidget(self.summaryList)
        col = QVBoxLayout()
        col.addWidget(self.summaryUp)
        col.addWidget(self.summaryDown)
        col.addStretch()
        row1.addLayout(col)
        sl.addLayout(row1)

        sl.addWidget(QLabel("Poradi vypoctenych polozek:"))
        row2 = QHBoxLayout()
        self.computedList = QListWidget()
        self.computedList.setAccessibleName("Seznam poradi vypoctenych polozek")
        self.compUp = QPushButton("Nahoru")
        self.compUp.setAccessibleName("Posunout polozku nahoru")
        self.compDown = QPushButton("Dolu")
        self.compDown.setAccessibleName("Posunout polozku dolu")
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

        # Mena
        curBox = QGroupBox("Mena")
        curBox.setAccessibleName("Skupina mena")
        cf = QFormLayout(curBox)
        self.currencyFromCombo = QComboBox()
        self.currencyFromCombo.setAccessibleName("Mena z")
        self.currencyFromCombo.setEditable(True)
        self.currencyFromCombo.addItems(["CZK", "EUR", "USD", "GBP", "PLN", "HUF", "CHF", "JPY"])
        self.currencyToCombo = QComboBox()
        self.currencyToCombo.setAccessibleName("Mena na")
        self.currencyToCombo.setEditable(True)
        self.currencyToCombo.addItems(["CZK", "EUR", "USD", "GBP", "PLN", "HUF", "CHF", "JPY"])
        cf.addRow("Z:", self.currencyFromCombo)
        cf.addRow("Na:", self.currencyToCombo)
        layout.addWidget(curBox)

        # Dev
        devBox = QGroupBox("Vyvojarsky rezim")
        devBox.setAccessibleName("Skupina vyvojarsky rezim")
        df = QFormLayout(devBox)
        self.devEnabledCheck = QCheckBox("Povolit vyvojarsky rezim")
        self.devEnabledCheck.setAccessibleName("Povolit vyvojarsky rezim")
        self.devAutoCheck = QCheckBox("Auto diagnostika")
        self.devAutoCheck.setAccessibleName("Povolit auto diagnostiku")
        self.devDurationSpin = QSpinBox()
        self.devDurationSpin.setAccessibleName("Delka diagnostiky v ms")
        self.devDurationSpin.setRange(200, 3000)
        self.devDurationSpin.setSingleStep(100)
        self.devPinEdit = QLineEdit()
        self.devPinEdit.setAccessibleName("PIN kod (4 cislice, prazdne=zadny)")
        self.devPinEdit.setPlaceholderText("prazdne = bez PIN")
        self.devPinEdit.setMaxLength(4)
        df.addRow(self.devEnabledCheck)
        df.addRow(self.devAutoCheck)
        df.addRow("Delka (200-3000 ms):", self.devDurationSpin)
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
        self.themeCombo.setCurrentText(gs.themeMode)
        self.degreeCheck.setChecked(gs.isDegreeMode)
        self.defaultModeCombo.setCurrentText(gs.defaultMode)
        self.summaryList.clear()
        for s in gs.statsSummaryOrder:
            self.summaryList.addItem(s)
        self.computedList.clear()
        for c in gs.statsComputedOrder:
            self.computedList.addItem(c)
        self.currencyFromCombo.setCurrentText(gs.currencyFrom)
        self.currencyToCombo.setCurrentText(gs.currencyTo)
        self.devEnabledCheck.setChecked(gs.devEnabled)
        self.devAutoCheck.setChecked(gs.devAutoDiagnostic)
        self.devDurationSpin.setValue(gs.devDiagnosticDurationMs)
        self.devPinEdit.setText(gs.devPinCode or "")

    def collect(self) -> GlobalSettings:
        summary = [self.summaryList.item(i).text() for i in range(self.summaryList.count())]
        computed = [self.computedList.item(i).text() for i in range(self.computedList.count())]
        pin = self.devPinEdit.text().strip() or None
        # validate pin 4 digits if present
        if pin is not None and pin != "" and (len(pin) != 4 or not pin.isdigit()):
            pin = None
        return GlobalSettings(
            themeMode=self.themeCombo.currentText(),
            isDegreeMode=self.degreeCheck.isChecked(),
            defaultMode=self.defaultModeCombo.currentText(),
            statsSummaryOrder=summary if summary else ["header", "dataValues", "computed"],
            statsComputedOrder=computed if computed else ["mean", "sum", "variance", "sd", "median", "min", "max", "mode", "cv", "wmean"],
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
