"""Entry point."""
import sys

from PyQt6.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Konfigurator mluvici kalkulacky")
    app.setOrganizationName("MluviciKalkulacka")
    # Pro NVDA: umoznit pristupnost
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
