# main.py

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.theme import app_font

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setFont(app_font())

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
