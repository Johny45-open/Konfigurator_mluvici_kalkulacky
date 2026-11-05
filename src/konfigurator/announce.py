"""Hlasový výstup pro oznamování provedených akcí.

Používá knihovnu accessible-output2:
- když běží čtečka obrazovky (NVDA, JAWS, Window Eyes, ...),
  text předá jejímu vlastnímu výstupu, takže mluví jediný známý hlas;
- když žádná čtečka neběží, použije se systémový hlas Windows (SAPI5).

Funkce nikdy neshodí výjimku ven — pokud hlasový výstup není
dostupný, ticho se přeskakuje a aplikace dál běží.
"""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)

_auto = None  # líně vytvořená instance Auto(), sdílená pro celou aplikaci


def _get_auto():
    """Vytvoří (a pak vrací) instance Auto(). Lazy import, aby se
    accessible-output2 nenačetlo při importu aplikace."""
    global _auto
    if _auto is None:
        from accessible_output2.outputs.auto import Auto  # odložený import

        _auto = Auto()
    return _auto


def reset() -> None:
    """Zahodí předchozí instanci Auto() (použití: testy)."""
    global _auto
    _auto = None


def announce(text: str, interrupt: bool = True) -> bool:
    """Ozvučit krátké potvrzení provedené akce.

    Args:
        text: Co se má říct (krátká česká věta).
        interrupt: Pokud je `True` (vychození), nejdřív se utlumí
            aktuální promluva, aby potvrzení dorazilo co nejrychleji.

    Returns:
        `True`, pokud bylo volání odesláno aktivnímu výstupu.
        `False`, pokud žádný výstup není dostupný, nebo se něco pokazilo.
    """
    try:
        auto = _get_auto()
        if auto.get_first_available_output() is None:
            return False
        auto.speak(text, interrupt=interrupt)
        return True
    except Exception:
        log.debug("Hlasový výstup není k dispozici.", exc_info=True)
        return False
