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

from ..models import AccessibilityProfile, AccessibilitySettings


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

        # Jmeno (pouze pro custom)
        self.nameEdit = QLineEdit()
        self.nameEdit.setAccessibleName("Nazev profilu")
        self.nameEdit.setAccessibleDescription("Zadejte nazev profilu")
        if self._profile.isBuiltIn:
            self.nameEdit.setEnabled(False)
            self.nameEdit.setToolTip("Vestavene profily nelze prejmenovat zde")
        nameBox = QGroupBox("Identita profilu")
        nameBox.setAccessibleName("Skupina identita profilu")
        fl = QFormLayout(nameBox)
        fl.addRow("Nazev:", self.nameEdit)
        fl.addRow("ID:", QLabel(self._profile.id))
        fl.addRow("Vestaveny:", QLabel("Ano" if self._profile.isBuiltIn else "Ne"))
        layout.addWidget(nameBox)

        # Zobrazeni
        dispBox = QGroupBox("Zobrazeni")
        dispBox.setAccessibleName("Skupina zobrazeni")
        f = QFormLayout(dispBox)
        self.fontSpin = self._make_double_spin(0.7, 2.5, 0.1, "Velikost pisma tlacitek")
        self.dialogFontSpin = self._make_double_spin(0.5, 5.0, 0.1, "Velikost pisma dialogu")
        self.dotSpin = self._make_double_spin(0.5, 5.0, 0.1, "Zoom horni displej")
        self.resultSpin = self._make_double_spin(0.5, 5.0, 0.1, "Zoom spodni displej")
        self.thicknessSpin = self._make_double_spin(0.8, 4.0, 0.2, "Tlouska carky")
        self.heightSpin = self._make_double_spin(0.5, 2.0, 0.1, "Vyska carky")
        self.gapCombo = QComboBox()
        self.gapCombo.setAccessibleName("Mezera tisicu")
        self.gapCombo.addItems(["small", "medium", "large"])
        self.dialogSizeCombo = QComboBox()
        self.dialogSizeCombo.setAccessibleName("Velikost dialogu")
        self.dialogSizeCombo.addItems(["compact", "wide", "fullscreen"])
        self.alignCheck = QCheckBox("Zarovnat vstup vlevo")
        self.alignCheck.setAccessibleName("Zarovnat vstupni radek vlevo")
        self.sixteenCheck = QCheckBox("16-segmentovy displej")
        self.sixteenCheck.setAccessibleName("Pouzit 16-segmentovy displej")
        self.periodicCheck = QCheckBox("Periodicky zapis vysledku")
        self.periodicCheck.setAccessibleName("Periodicky zapis vysledku")
        f.addRow("Pismo tlacitek (0.7-2.5):", self.fontSpin)
        f.addRow("Pismo dialogu (0.5-5.0):", self.dialogFontSpin)
        f.addRow("Zoom horni (0.5-5.0):", self.dotSpin)
        f.addRow("Zoom dolni (0.5-5.0):", self.resultSpin)
        f.addRow("Tlouska carky (0.8-4.0):", self.thicknessSpin)
        f.addRow("Vyska carky (0.5-2.0):", self.heightSpin)
        f.addRow("Mezera tisicu:", self.gapCombo)
        f.addRow("Velikost dialogu:", self.dialogSizeCombo)
        f.addRow(self.alignCheck)
        f.addRow(self.sixteenCheck)
        f.addRow(self.periodicCheck)
        layout.addWidget(dispBox)

        # Oznamovani
        annBox = QGroupBox("Oznamovani a ctecka")
        annBox.setAccessibleName("Skupina oznamovani a ctecka")
        af = QFormLayout(annBox)
        self.announceCheck = QCheckBox("Oznamovat vyraz pred vypoctem")
        self.announceCheck.setAccessibleName("Oznamovat vyraz pred vypoctem")
        self.readStatsCheck = QCheckBox("Cist hodnoty statisticke pameti")
        self.readStatsCheck.setAccessibleName("Cist hodnoty statisticke pameti")
        self.autoReadCheck = QCheckBox("Auto cist statisticky souhrn")
        self.autoReadCheck.setAccessibleName("Automaticky cist statisticky souhrn pri otevreni")
        self.hintCheck = QCheckBox("Napoveda pro pohyb v souhrnu")
        self.hintCheck.setAccessibleName("Zobrazit napovedu pro pohyb v souhrnu")
        self.screenReaderCombo = QComboBox()
        self.screenReaderCombo.setAccessibleName("Rezim ctecky obrazovky")
        self.screenReaderCombo.addItems(["auto", "on", "off"])
        self.accTypeCombo = QComboBox()
        self.accTypeCombo.setAccessibleName("Typ pristupnosti")
        self.accTypeCombo.addItems(["none", "blind", "visuallyImpaired"])
        af.addRow("Typ pristupnosti:", self.accTypeCombo)
        af.addRow("Rezim ctecky:", self.screenReaderCombo)
        af.addRow(self.announceCheck)
        af.addRow(self.readStatsCheck)
        af.addRow(self.autoReadCheck)
        af.addRow(self.hintCheck)
        layout.addWidget(annBox)

        # TTS
        ttsBox = QGroupBox("Hlasovy vystup (TTS)")
        ttsBox.setAccessibleName("Skupina hlasovy vystup")
        tf = QFormLayout(ttsBox)
        self.ttsEnabledCheck = QCheckBox("Hlas povolen")
        self.ttsEnabledCheck.setAccessibleName("Povolit hlasovy vystup")
        self.speechRateSpin = self._make_double_spin(0.1, 1.0, 0.1, "Rychlost reci")
        self.speechVolumeSpin = self._make_double_spin(0.0, 1.0, 0.1, "Hlasitost")
        self.ttsEngineEdit = QLineEdit()
        self.ttsEngineEdit.setAccessibleName("TTS engine")
        self.ttsEngineEdit.setPlaceholderText("Vychozi (prazdne)")
        self.ttsVoiceNameEdit = QLineEdit()
        self.ttsVoiceNameEdit.setAccessibleName("Nazev hlasu")
        self.ttsVoiceNameEdit.setPlaceholderText("Vychozi")
        self.ttsVoiceLocaleCombo = QComboBox()
        self.ttsVoiceLocaleCombo.setAccessibleName("Jazyk hlasu")
        self.ttsVoiceLocaleCombo.addItems(["", "cs-CZ", "en-US"])
        self.ttsVoiceLocaleCombo.setEditable(True)
        self.inverseCombo = QComboBox()
        self.inverseCombo.setAccessibleName("Format uhlu")
        self.inverseCombo.addItems(["", "dms", "decimal"])
        tf.addRow(self.ttsEnabledCheck)
        tf.addRow("Rychlost (0.1-1.0):", self.speechRateSpin)
        tf.addRow("Hlasitost (0.0-1.0):", self.speechVolumeSpin)
        tf.addRow("Engine (prazdne=vychozi):", self.ttsEngineEdit)
        tf.addRow("Hlas - jmeno:", self.ttsVoiceNameEdit)
        tf.addRow("Hlas - locale:", self.ttsVoiceLocaleCombo)
        tf.addRow("Format uhlu (prazdne=vychozi):", self.inverseCombo)
        layout.addWidget(ttsBox)

        outer.addWidget(scroll)
        # Buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setAccessibleName("Ulozit profil")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setAccessibleName("Zrusit upravy profilu")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Ulozit")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Zrusit")
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)
        outer.addWidget(self.buttonBox)
        # Focus na prvni pole
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
        self.gapCombo.setCurrentText(s.thousandGroupGap)
        self.dialogSizeCombo.setCurrentText(s.dialogSize)
        self.alignCheck.setChecked(s.alignInputLeft)
        self.sixteenCheck.setChecked(s.useSixteenSegment)
        self.periodicCheck.setChecked(s.usePeriodicNotation)
        self.announceCheck.setChecked(s.announceExpression)
        self.readStatsCheck.setChecked(s.readStatsMemoryValues)
        self.autoReadCheck.setChecked(s.autoReadStatsSummary)
        self.hintCheck.setChecked(s.showStatsNavigationHint)
        self.screenReaderCombo.setCurrentText(s.screenReaderMode)
        self.accTypeCombo.setCurrentText(s.accessibilityType)
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
        self.inverseCombo.setCurrentText(s.inverseFormatPreference or "")

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
        inv = self.inverseCombo.currentText().strip() or None
        s = AccessibilitySettings(
            accessibilityType=self.accTypeCombo.currentText(),
            screenReaderMode=self.screenReaderCombo.currentText(),
            fontSizeMultiplier=float(self.fontSpin.value()),
            dialogFontScale=float(self.dialogFontSpin.value()),
            dotMatrixZoom=float(self.dotSpin.value()),
            resultZoom=float(self.resultSpin.value()),
            thousandGroupGap=self.gapCombo.currentText(),
            dialogSize=self.dialogSizeCombo.currentText(),
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
            QMessageBox.warning(self, "Chyba", "Nazev profilu nesmi byt prazdny.")
            self.nameEdit.setFocus()
            return
        self.accept()

    def result_profile(self) -> AccessibilityProfile:
        s = self._collect()
        name = self.nameEdit.text().strip() if not self._profile.isBuiltIn else self._profile.name
        return AccessibilityProfile(id=self._profile.id, name=name, isBuiltIn=self._profile.isBuiltIn, settings=s)
