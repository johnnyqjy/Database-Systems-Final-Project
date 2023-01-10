from PyQt5 import uic
from PyQt5.QtGui import QWindow
from TitanicDialog import TitanicDialog


class AppWindow(QWindow):
    """
    The main application window.
    """

    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()

        # Titanic dialog.
        self._titanic_dialog = TitanicDialog()
        self._titanic_dialog.show_dialog()

