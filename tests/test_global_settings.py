import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from konfigurator.models import GlobalSettings, TtsVoice
from konfigurator.ui.global_settings import GlobalSettingsWidget


def test_global_accessibility_settings_round_trip():
    app = QApplication.instance() or QApplication([])
    settings = GlobalSettings(
        themeMode="light",
        screenReaderMode="on",
        ttsEnabled=False,
        speechRate=0.8,
        speechVolume=0.4,
        ttsEngine="example.engine",
        ttsVoice=TtsVoice(name="Hlas", locale="cs-CZ"),
        resultDisplayMode="text",
        announceFractionAvailability=False,
    )

    widget = GlobalSettingsWidget(settings)
    collected = widget.collect()

    assert collected.themeMode == "light"
    assert collected.screenReaderMode == "on"
    assert collected.ttsEnabled is False
    assert collected.speechRate == 0.8
    assert collected.speechVolume == 0.4
    assert collected.ttsEngine == "example.engine"
    assert collected.ttsVoice == TtsVoice(name="Hlas", locale="cs-CZ")
    assert collected.resultDisplayMode == "text"
    assert collected.announceFractionAvailability is False
    widget.close()
    app.processEvents()
