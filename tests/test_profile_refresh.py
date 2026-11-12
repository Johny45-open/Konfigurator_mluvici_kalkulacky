# -*- coding: utf-8 -*-
"""Tests for profile refresh logic ensuring activeProfileId is preserved.
"""
import os
import sys

# Ensure Qt uses offscreen platform for tests
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
import pytest

# Import the MainWindow class
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.konfigurator.ui.main_window import MainWindow

@pytest.fixture(scope="module")
def app():
    """Create a single QApplication for the test module."""
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app

@pytest.fixture
def window(app):
    """Create a fresh MainWindow instance for each test."""
    w = MainWindow()
    # Ensure UI is fully constructed
    w.show()
    yield w
    w.close()

def set_active_and_refresh(win, profile_id):
    """Helper to set activeProfileId directly and refresh UI."""
    win._config.activeProfileId = profile_id
    win._refresh_profile_list()

def test_active_profile_blind_preserved(window):
    set_active_and_refresh(window, "blind")
    assert window._config.activeProfileId == "blind"
    # QComboBox currentData should match
    assert window.activeCombo.currentData() == "blind"

def test_active_profile_lowvision_preserved(window):
    set_active_and_refresh(window, "lowvision")
    assert window._config.activeProfileId == "lowvision"
    assert window.activeCombo.currentData() == "lowvision"

def test_active_profile_custom_preserved(window):
    # Add a custom profile
    custom = window._config.profiles[0]  # duplicate first for simplicity
    from src.konfigurator import models
    new_id = models.generate_custom_id("Custom")
    custom_profile = models.AccessibilityProfile(
        id=new_id,
        name="Můj profil",
        isBuiltIn=False,
        settings=models.AccessibilitySettings.defaults_standard(),
    )
    window._config.profiles.append(custom_profile)
    set_active_and_refresh(window, new_id)
    assert window._config.activeProfileId == new_id
    assert window.activeCombo.currentData() == new_id

def test_user_changes_active_profile_via_combo(window):
    # Simulate user selecting a different index
    initial_id = window._config.activeProfileId
    # pick a different index
    new_index = (window.activeCombo.currentIndex() + 1) % window.activeCombo.count()
    window.activeCombo.setCurrentIndex(new_index)
    # _on_active_changed should have updated config
    new_id = window.activeCombo.currentData()
    assert window._config.activeProfileId == new_id
    # Refresh and ensure it stays the same
    window._refresh_profile_list()
    assert window._config.activeProfileId == new_id
    assert window.activeCombo.currentData() == new_id

def test_set_active_button(window, monkeypatch):
    # Add a custom profile to select
    from src.konfigurator import models
    new_id = models.generate_custom_id("SetActiveTest")
    prof = models.AccessibilityProfile(
        id=new_id,
        name="SetActiveTest",
        isBuiltIn=False,
        settings=models.AccessibilitySettings.defaults_standard(),
    )
    window._config.profiles.append(prof)
    window._refresh_profile_list()
    # Select the newly added profile in list
    window.profileList.setCurrentRow(len(window._config.profiles) - 1)
    # Trigger the button action
    window.on_set_active()
    assert window._config.activeProfileId == new_id
    # After refresh, activeCombo should still point to that id
    window._refresh_profile_list()
    assert window.activeCombo.currentData() == new_id
