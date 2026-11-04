"""Editor jednoho profilu — GroupBoxy, SpinBoxy, ComboBoxy, CheckBoxy."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..models import (
    ACCESSIBILITY_TYPE_LABELS,
    AccessibilityProfile,
    AccessibilitySettings,
    DIALOG_SIZE_LABELS,
    INVERSE_PREF_LABELS,
    SCREEN_READER_LABELS,
    THOUSAND_GAP_LABELS,
)


def _set_combo_by_data(combo, value) -> None:
    """Nastavi rozbočník na položku, jejíž skryta hodnota se rovná value."""
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return
    combo.setCurrentIndex(0)


class ProfileEditorDialog(QDialog):
    def __init__(self, profile: AccessibilityProfile, parent=None):
        super().__init__(parent)
        self._profile = profile
        self._settings = profile.settings
        # deep copy pro editaci
        import copy

        self._edited = copy.deepcopy(self._settings)
        self._name = profile.name
        self.setWindowTitle(f"Upravit profil: {self._name}")
        self.setAccessibleName(f"Dialog upravit profil {self._name}")
        self.setModal(True)
        self.resize(720, 800)
        self._build_ui()
        self._load_to_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        # Scroll area aby nebyl obrovsky formular
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAccessibleName("Obsah editoru profilu")
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        # Jméno (pouze pro custom)
        self.nameEdit = QLineEdit()
        self.nameEdit.setAccessibleName("Název profilu")
        self.nameEdit.setAccessibleDescription("Zadejte název profilu")
        if self._profile.isBuiltIn:
            self.nameEdit.setEnabled(False)
            self.nameEdit.setToolTip("Vestavěné profily nelze přejmenovat zde")
        nameBox = QGroupBox("Identita profilu")
        nameBox.setAccessibleName("Skupina identita profilu")
        fl = QFormLayout(nameBox)
        fl.addRow("Název:", self.nameEdit)
        fl.addRow("ID:", QLabel(self._profile.id))
        fl.addRow("Vestavěný:", QLabel("Ano" if self._profile.isBuiltIn else "Ne"))
        layout.addWidget(nameBox)

        # Zobrazení
        dispBox = QGroupBox("Zobrazení")
        dispBox.setAccessibleName("Skupina zobrazení")
        f = QFormLayout(dispBox)
        self.fontSpin = self._make_double_spin(0.7, 2.5, 0.1, "Velikost písma tlačítek")
        self.dialogFontSpin = self._make_double_spin(0.5, 5.0, 0.1, "Velikost písma dialogů")
        self.dotSpin = self._make_double_spin(0.5, 5.0, 0.1, "Zoom horní displej")
        self.resultSpin = self._make_double_spin(0.5, 5.0, 0.1, "Zoom spodní displej")
        self.thicknessSpin = self._make_double_spin(0.8, 4.0, 0.2, "Tloušťka čárky")
        self.heightSpin = self._make_double_spin(0.5, 2.0, 0.1, "Výška čárky")
        self.gapCombo = QComboBox()
        self.gapCombo.setAccessibleName("Mezera tisíců")
        for v in ("small", "medium", "large"):
            self.gapCombo.addItem(THOUSAND_GAP_LABELS[v], v)
        self.dialogSizeCombo = QComboBox()
        self.dialogSizeCombo.setAccessibleName("Velikost dialogu")
        for v in ("compact", "wide", "fullscreen"):
            self.dialogSizeCombo.addItem(DIALOG_SIZE_LABELS[v], v)
        self.alignCheck = QCheckBox("Zarovnát vstup vlevo")
        self.alignCheck.setAccessibleName("Zarovnat vstupní řádek vlevo")
        self.sixteenCheck = QCheckBox("16-segmentový displej")
        self.sixteenCheck.setAccessibleName("Použít 16-segmentový displej")
        self.periodicCheck = QCheckBox("Periodický zápis výsledků")
        self.periodicCheck.setAccessibleName("Periodický zápis výsledků")
        f.addRow("Písmo tlačítek (0.7-2.5):", self.fontSpin)
        f.addRow("Písmo dialogů (0.5-5.0):", self.dialogFontSpin)
        f.addRow("Zoom horní (0.5-5.0):", self.dotSpin)
        f.addRow("Zoom dolní (0.5-5.0):", self.resultSpin)
        f.addRow("Tloušťka čárky (0.8-4.0):", self.thicknessSpin)
        f.addRow("Výška čárky (0.5-2.0):", self.heightSpin)
        f.addRow("Mezera tisíců:", self.gapCombo)
        f.addRow("Velikost dialogu:", self.dialogSizeCombo)
        f.addRow(self.alignCheck)
        f.addRow(self.sixteenCheck)
        f.addRow(self.periodicCheck)
        layout.addWidget(dispBox)

        # Oznamování
        annBox = QGroupBox("Oznamování a čtečka")
        annBox.setAccessibleName("Skupina oznamování a čtečka")
        af = QFormLayout(annBox)
        self.announceCheck = QCheckBox("Oznamovat výraz před výpočtem")
        self.announceCheck.setAccessibleName("Oznamovat výraz před výpočtem")
        self.readStatsCheck = QCheckBox("Číst hodnoty statistické paměti")
        self.readStatsCheck.setAccessibleName("Číst hodnoty statistické paměti")
        self.autoReadCheck = QCheckBox("Auto číst statistický souhrn")
        self.autoReadCheck.setAccessibleName("Automaticky číst statistický souhrn při otevření")
        self.hintCheck = QCheckBox("Nápověda pro pohyb v souhrnu")
        self.hintCheck.setAccessibleName("Zobrazit nápovědu pro pohyb v souhrnu")
        self.screenReaderCombo = QComboBox()
        self.screenReaderCombo.setAccessibleName("Režim čtečky obrazovky")
        for v in ("auto", "on", "off"):
            self.screenReaderCombo.addItem(SCREEN_READER_LABELS[v], v)
        self.accTypeCombo = QComboBox()
        self.accTypeCombo.setAccessibleName("Typ přístupnosti")
        for v in ("none", "blind", "visuallyImpaired"):
            self.accTypeCombo.addItem(ACCESSIBILITY_TYPE_LABELS[v], v)
        af.addRow("Typ přístupnosti:", self.accTypeCombo)
        af.addRow("Režim čtečky:", self.screenReaderCombo)
        af.addRow(self.announceCheck)
        af.addRow(self.readStatsCheck)
        af.addRow(self.autoReadCheck)
        af.addRow(self.hintCheck)
        layout.addWidget(annBox)

        # TTS
        ttsBox = QGroupBox("Hlasový výstup (TTS)")
        ttsBox.setAccessibleName("Skupina hlasový výstup")
        tf = QFormLayout(ttsBox)
        self.ttsEnabledCheck = QCheckBox("Hlas povolen")
        self.ttsEnabledCheck.setAccessibleName("Povolit hlasový výstup")
        self.speechRateSpin = self._make_double_spin(0.1, 1.0, 0.1, "Rychlost řeči")
        self.speechVolumeSpin = self._make_double_spin(0.0, 1.0, 0.1, "Hlasitost")
        self.ttsEngineEdit = QLineEdit()
        self.ttsEngineEdit.setAccessibleName("TTS engine")
        self.ttsEngineEdit.setPlaceholderText("Výchozí (prázdné)")
        self.ttsVoiceNameEdit = QLineEdit()
        self.ttsVoiceNameEdit.setAccessibleName("Název hlasu")
        self.ttsVoiceNameEdit.setPlaceholderText("Výchozí")
        self.ttsVoiceLocaleCombo = QComboBox()
        self.ttsVoiceLocaleCombo.setAccessibleName("Jazyk hlasu")
        self.ttsVoiceLocaleCombo.addItems(["", "cs-CZ", "en-US"])
        self.ttsVoiceLocaleCombo.setEditable(True)
        self.inverseCombo = QComboBox()
        self.inverseCombo.setAccessibleName("Formát úhlů")
        self.inverseCombo.addItem("Výchozí", "")
        for v in ("dms", "decimal"):
            self.inverseCombo.addItem(INVERSE_PREF_LABELS[v], v)
        tf.addRow(self.ttsEnabledCheck)
        tf.addRow("Rychlost (0.1-1.0):", self.speechRateSpin)
        tf.addRow("Hlasitost (0.0-1.0):", self.speechVolumeSpin)
        tf.addRow("Engine (prázdné=výchozí):", self.ttsEngineEdit)
        tf.addRow("Hlas - jméno:", self.ttsVoiceNameEdit)
        tf.addRow("Hlas - locale:", self.ttsVoiceLocaleCombo)
        tf.addRow("Formát úhlů:", self.inverseCombo)
        layout.addWidget(ttsBox)

        outer.addWidget(scroll)
        # Buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setAccessibleName("Uložit profil")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setAccessibleName("Zrušit úpravy profilu")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Uložit")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Zrušit")
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)
        outer.addWidget(self.buttonBox)
        # Focus na první pole
        self.nameEdit.setFocus()

    def _make_double_spin(self, mn: float, mx: float, step: float, acc_name: str) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(mn, mx)
        s.setSingleStep(step)
        s.setDecimals(2)
        s.setAccessibleName(acc_name)
        s.setKeyboardTracking(False)
        return s

    def _load_to_ui(self) -> None:
        s = self._edited
        self.nameEdit.setText(self._name)
        self.fontSpin.setValue(s.fontSizeMultiplier)
        self.dialogFontSpin.setValue(s.dialogFontScale)
        self.dotSpin.setValue(s.dotMatrixZoom)
        self.resultSpin.setValue(s.resultZoom)
        self.thicknessSpin.setValue(s.overlineThickness)
        self.heightSpin.setValue(s.overlineHeight)
        _set_combo_by_data(self.gapCombo, s.thousandGroupGap)
        _set_combo_by_data(self.dialogSizeCombo, s.dialogSize)
        self.alignCheck.setChecked(s.alignInputLeft)
        self.sixteenCheck.setChecked(s.useSixteenSegment)
        self.periodicCheck.setChecked(s.usePeriodicNotation)
        self.announceCheck.setChecked(s.announceExpression)
        self.readStatsCheck.setChecked(s.readStatsMemoryValues)
        self.autoReadCheck.setChecked(s.autoReadStatsSummary)
        self.hintCheck.setChecked(s.showStatsNavigationHint)
        _set_combo_by_data(self.screenReaderCombo, s.screenReaderMode)
        _set_combo_by_data(self.accTypeCombo, s.accessibilityType)
        self.ttsEnabledCheck.setChecked(s.ttsEnabled)
        self.speechRateSpin.setValue(s.speechRate)
        self.speechVolumeSpin.setValue(s.speechVolume)
        self.ttsEngineEdit.setText(s.ttsEngine or "")
        if s.ttsVoice:
            self.ttsVoiceNameEdit.setText(s.ttsVoice.name)
            self.ttsVoiceLocaleCombo.setCurrentText(s.ttsVoice.locale)
        else:
            self.ttsVoiceNameEdit.setText(s.ttsVoiceName or "")
            self.ttsVoiceLocaleCombo.setCurrentText("")
        _set_combo_by_data(self.inverseCombo, s.inverseFormatPreference or "")

    def _collect(self) -> AccessibilitySettings:
        from ..models import TtsVoice

        voice = None
        vname = self.ttsVoiceNameEdit.text().strip()
        vlocale = self.ttsVoiceLocaleCombo.currentText().strip()
        # If locale set, create voice; vname may be empty then use vlocale as name placeholder?
        if vlocale:
            # If name empty but locale present, use locale as fallback name is not valid; require name
            if vname:
                voice = TtsVoice(name=vname, locale=vlocale)
            else:
                # No voice if name missing — clear
                voice = None
        engine = self.ttsEngineEdit.text().strip() or None
        inv = self.inverseCombo.currentData() or None
        s = AccessibilitySettings(
            accessibilityType=self.accTypeCombo.currentData(),
            screenReaderMode=self.screenReaderCombo.currentData(),
            fontSizeMultiplier=float(self.fontSpin.value()),
            dialogFontScale=float(self.dialogFontSpin.value()),
            dotMatrixZoom=float(self.dotSpin.value()),
            resultZoom=float(self.resultSpin.value()),
            thousandGroupGap=self.gapCombo.currentData(),
            dialogSize=self.dialogSizeCombo.currentData(),
            useSixteenSegment=self.sixteenCheck.isChecked(),
            usePeriodicNotation=self.periodicCheck.isChecked(),
            announceExpression=self.announceCheck.isChecked(),
            readStatsMemoryValues=self.readStatsCheck.isChecked(),
            autoReadStatsSummary=self.autoReadCheck.isChecked(),
            showStatsNavigationHint=self.hintCheck.isChecked(),
            alignInputLeft=self.alignCheck.isChecked(),
            overlineThickness=float(self.thicknessSpin.value()),
            overlineHeight=float(self.heightSpin.value()),
            speechRate=float(self.speechRateSpin.value()),
            speechVolume=float(self.speechVolumeSpin.value()),
            ttsEnabled=self.ttsEnabledCheck.isChecked(),
            ttsEngine=engine,
            ttsVoice=voice,
            ttsVoiceName=vname or None,
            inverseFormatPreference=inv,
        )
        return s

    def _on_accept(self) -> None:
        if not self.nameEdit.text().strip():
            QMessageBox.warning(self, "Chyba", "Název profilu nesmí být prázdný.")
            self.nameEdit.setFocus()
            return
        self.accept()

    def result_profile(self) -> AccessibilityProfile:
        s = self._collect()
        name = self.nameEdit.text().strip() if not self._profile.isBuiltIn else self._profile.name
        return AccessibilityProfile(id=self._profile.id, name=name, isBuiltIn=self._profile.isBuiltIn, settings=s)
