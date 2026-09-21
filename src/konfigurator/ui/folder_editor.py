from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QComboBox, QSpinBox, QGroupBox, QVBoxLayout
from ..models import StatisticsFolder, generate_stats_id

ICONS = ["dataset","school","work","home","lab","chart","folder","star"]

class FolderEditorDialog(QDialog):
    def __init__(self, folder: StatisticsFolder | None, parent=None):
        super().__init__(parent)
        self._folder = folder
        self.setWindowTitle("Složka" if folder else "Nová složka")
        self.setAccessibleName("Dialog složka")
        self.setModal(True)
        self.resize(400, 250)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.nameEdit = QLineEdit(folder.name if folder else "")
        self.nameEdit.setAccessibleName("Název složky")
        self.nameEdit.setPlaceholderText("Název")
        form.addRow("Název:", self.nameEdit)
        self.colorSpin = QSpinBox()
        self.colorSpin.setAccessibleName("Barva index 0-7")
        self.colorSpin.setRange(0,7)
        self.colorSpin.setValue(folder.colorIndex if folder else 0)
        form.addRow("Barva (0-7):", self.colorSpin)
        self.iconCombo = QComboBox()
        self.iconCombo.setAccessibleName("Ikona složky")
        self.iconCombo.addItems(ICONS)
        if folder and folder.iconName in ICONS:
            self.iconCombo.setCurrentText(folder.iconName)
        form.addRow("Ikona:", self.iconCombo)
        layout.addLayout(form)
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Uložit")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText("Zrušit")
        layout.addWidget(self.buttonBox)
        self.nameEdit.setFocus()

    def _on_accept(self):
        if not self.nameEdit.text().strip():
            self.nameEdit.setFocus(); return
        self.accept()

    def result_folder(self) -> StatisticsFolder:
        name = self.nameEdit.text().strip()
        if self._folder:
            self._folder.name=name
            self._folder.colorIndex=self.colorSpin.value()
            self._folder.iconName=self.iconCombo.currentText()
            return self._folder
        return StatisticsFolder(id=generate_stats_id(), name=name, colorIndex=self.colorSpin.value(), iconName=self.iconCombo.currentText())
