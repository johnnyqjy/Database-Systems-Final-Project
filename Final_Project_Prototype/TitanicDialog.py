import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QTableWidgetItem, QHeaderView, QSlider, QLabel
from mydbutils import do_query,make_connection


class TitanicDialog(QDialog):
    """
    The titanic dialog.
    """

    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()

        # Titanic dialog.
        self.ui = uic.loadUi('titanic_dialog.ui')

        self.ui.minimum_age.valueChanged.connect(self.update_min)
        self.ui.maximum_age.valueChanged.connect(self.update_max)
        
        # Query button event handlers and Analysis Selection
        # TODO hide initial last name when analysis 1 is selected
        self.ui.query_button.clicked.connect(self._load_data)

        # Initialize table
        self._initialize_table()
        self.ui.analysis_1.toggled.connect(self._initialize_table)
        self.ui.analysis_2.toggled.connect(self._initialize_table)
        
    def update_min(self):
            new_value = str(self.ui.minimum_age.value())
            self.ui.min_value.setText(new_value)
    
    def update_max(self):
            new_value = str(self.ui.maximum_age.value())
            self.ui.max_value.setText(new_value)
    
    def show_dialog(self):
        """
        Show this dialog.
        """
        self.ui.show()

    def _initialize_table(self):
        """
        Clear the table and set the column headers.
        """
        self.ui.query_table.clear()

        col1 = ['  last_name  ', '  set_size  ', '  class_count  ', '  avg(age)  ']
        col2 = ['  last_name  ', '  class  ', '  subset_size  ', '  avg(age)  ']

        if self.ui.analysis_1.isChecked():
            self.ui.line_edit.hide()
            self.ui.query_table.setHorizontalHeaderLabels(col1)
        elif self.ui.analysis_2.isChecked():
            self.ui.line_edit.show()
            self.ui.query_table.setHorizontalHeaderLabels(col2)

        self._adjust_column_widths()

    def _adjust_column_widths(self):
        """
        Adjust the column widths of the class table to fit the contents.
        """
        header = self.ui.query_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

    def _load_data(self):
        """
        Enter data from Inputs to query_table to return data.
        """
        conn = make_connection()
        cursor = conn.cursor()
        if self.ui.analysis_1.isChecked():
            min_age = self.ui.minimum_age.value()
            max_age = self.ui.maximum_age.value()
            min_set = self.ui.minimum_set_subset.value()
            cursor.callproc('analysis_1', [min_set,min_age,max_age])
            for result in cursor.stored_results():
                count = 0
                for row in result.fetchall():
                    self.ui.query_table.setItem(count, 0, QTableWidgetItem(str(row[0])))
                    self.ui.query_table.setItem(count, 1, QTableWidgetItem(str(row[1])))
                    self.ui.query_table.setItem(count, 2, QTableWidgetItem(str(row[2])))
                    self.ui.query_table.setItem(count, 3, QTableWidgetItem(str(row[3])))
                    count += 1

        elif self.ui.analysis_2.isChecked():
            min_age = self.ui.minimum_age.value()
            max_age = self.ui.maximum_age.value()
            min_set = self.ui.minimum_set_subset.value()
            initial = self.ui.line_edit.text()
            cursor.callproc('analysis_2', [min_set,initial,min_age,max_age])
            for result in cursor.stored_results():
                count = 0
                for row in result.fetchall():
                    self.ui.query_table.setItem(count, 0, QTableWidgetItem(row[0]))
                    self.ui.query_table.setItem(count, 1, QTableWidgetItem(row[1]))
                    self.ui.query_table.setItem(count, 2, QTableWidgetItem(str(row[2])))
                    self.ui.query_table.setItem(count, 3, QTableWidgetItem(str(row[3])))
                    count += 1

        