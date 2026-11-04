"""Entry point."""
import sys

from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Konfigurátor mluvící kalkulačky")
    app.setOrganizationName("MluviciKalkulacka")
    # Pro NVDA:umožnit přístupnost
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
