"""Testy hlasového výstupu (konfigurator.announce).

Reálné Auto() se nikde nekonstruuje — nahrazujeme ho fákem,
který si pamatuje volání speak(). Díky tomu testy nehlásí
nezávisle na tom, jestli na stroji běží čtečka obrazovky.
"""
import sys

import pytest

from konfigurator import announce


class FakeOutput:
    """Simuluje jeden výstup (NVDA / SAPI5) a zapisuje volání speak()."""

    def __init__(self, active=True, fail_speak=False):
        self._active = active
        self._fail_speak = fail_speak
        self.speak_calls = []

    def is_active(self):
        return self._active

    def speak(self, text, interrupt=False):
        if self._fail_speak:
            raise RuntimeError("Simulovaná chyba výstupu")
        self.speak_calls.append((text, interrupt))


class FakeAuto:
    """Simuluje Auto() z accessible_output2.outputs.auto."""

    def __init__(self, output):
        self.output = output

    def get_first_available_output(self):
        return self.output if self.output.is_active() else None

    def speak(self, *args, **kwargs):
        self.output.speak(*args, **kwargs)


@pytest.fixture
def fake_auto(monkeypatch):
    """Připravené Auto() s aktivním a funkčním výstupem."""
    auto = FakeAuto(FakeOutput())
    monkeypatch.setattr(announce, "_auto", auto)
    return auto


def _set_auto(monkeypatch, output):
    auto = FakeAuto(output)
    monkeypatch.setattr(announce, "_auto", auto)
    return auto


def test_announce_speaks_text(fake_auto):
    """Aktivní výstup dostane text s přerušením běžící promluvy."""
    assert announce.announce("Profil uložen.") is True
    assert fake_auto.output.speak_calls == [("Profil uložen.", True)]


def test_announce_without_active_output(monkeypatch):
    """Bez aktivního výstupu se nic neděje a vrácí se False."""
    auto = _set_auto(monkeypatch, FakeOutput(active=False))
    assert announce.announce("Profil uložen.") is False
    assert auto.output.speak_calls == []


def test_announce_returns_false_when_speak_fails(monkeypatch):
    """Chyba v backendu nesmí proletět do volajícího kódu."""
    _set_auto(monkeypatch, FakeOutput(fail_speak=True))
    assert announce.announce("Profil uložen.") is False


def test_announce_when_library_not_installed(monkeypatch):
    """I bez nainstalované accessible-output2 musí volání mlčenlivě skončit."""
    monkeypatch.setattr(announce, "_auto", None)
    monkeypatch.setitem(sys.modules, "accessible_output2", None)
    assert announce.announce("Profil uložen.") is False
