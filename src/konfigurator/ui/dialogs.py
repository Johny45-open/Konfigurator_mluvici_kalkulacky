"""Společné dialogy."""
from PyQt6.QtWidgets import QMessageBox


def show_error(parent, title: str, text: str) -> None:
    m = QMessageBox(parent)
    m.setIcon(QMessageBox.Icon.Critical)
    m.setWindowTitle(title)
    m.setText(text)
    m.setStandardButtons(QMessageBox.StandardButton.Ok)
    # focus na OK
    m.setDefaultButton(QMessageBox.StandardButton.Ok)
    m.exec()


def show_info(parent, title: str, text: str) -> None:
    m = QMessageBox(parent)
    m.setIcon(QMessageBox.Icon.Information)
    m.setWindowTitle(title)
    m.setText(text)
    m.setStandardButtons(QMessageBox.StandardButton.Ok)
    m.setDefaultButton(QMessageBox.StandardButton.Ok)
    m.exec()


def show_warning(parent, title: str, text: str) -> None:
    m = QMessageBox(parent)
    m.setIcon(QMessageBox.Icon.Warning)
    m.setWindowTitle(title)
    m.setText(text)
    m.setStandardButtons(QMessageBox.StandardButton.Ok)
    m.setDefaultButton(QMessageBox.StandardButton.Ok)
    m.exec()
