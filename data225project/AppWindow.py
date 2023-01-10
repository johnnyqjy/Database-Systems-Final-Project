from PyQt5 import uic
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QMessageBox
from Employees import EmployeesDialog
from ProductLines import ProductLinesDialog
from Pinnacle_wh import perform_ETL_warehouse
from mydbutils import executeScriptsFromFile, insert_csv

class AppWindow(QWindow):
    """
    The main application window.
    """
    
    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()
        
        self.ui = uic.loadUi('demo_app.ui')
        self.ui.show()

        # ETL for operational schema.
        self.ui.etl_db_button.clicked.connect(self._perform_ETL_DB)

        # ETL for warehouse schema.
        self.ui.etl_wh_button.clicked.connect(self._perform_ETL_WH)
        
        # Employees dialog.
        self._employees_dialog = EmployeesDialog()
        self.ui.employees_button.clicked.connect(self._show_employees_dialog)
        
        # Product Lines dialog.
        self._productLines_dialog = ProductLinesDialog()
        self.ui.productLines_button.clicked.connect(self._show_productLines_dialog)

    def _show_employees_dialog(self):
        """
        Show the eployees dialog.
        """
        self._employees_dialog.show_dialog()

    def _show_productLines_dialog(self):
        """
        Show the product lines dialog.
        """
        self._productLines_dialog.show_dialog()

    def _perform_ETL_WH(self):
        """
        Show message if the ETL is successfull or not.
        """
        msg = QMessageBox()
        msg.setWindowTitle("Perform ETL For Warehouse:")

        try:
            perform_ETL_warehouse()
            msg.setText("Successfully!")
        except:
            msg.setText("Unsuccessfully, please check pinnacle_wh schema or if the schema has been created!")

        x = msg.exec_()

    def _perform_ETL_DB(self):
        """
        Show message if the ETL is successfull or not.
        """
        msg = QMessageBox()
        msg.setWindowTitle("Perform ETL For Operational Schema:")

        # Create tables and insert data for operational database
        check1 = executeScriptsFromFile("pinnacle_db.sql")

        # Isert data for orderdetails from csv file
        check2 = insert_csv("INSERT INTO orderdetails VALUES (%s, %s, %s, %s)",
        "orderdetails.csv")

        if check1 == 1 and check2 == 1:
            msg.setText("Successfully!")
        else:
            msg.setText("Unsuccessfully, please check pinnacle_db schema or if the schema has been created!")

        x = msg.exec_()