import sys
from PyQt5.QtWidgets import QApplication
from AppWindow import AppWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = AppWindow()
    sys.exit(app.exec_())