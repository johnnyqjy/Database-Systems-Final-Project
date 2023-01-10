import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QGraphicsScene, QGraphicsView
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mydbutils import do_query, set_data_to_table_cells, adjust_column_widths

class EmployeesDialog(QDialog):
    '''
    The employees dialog
    '''
    
    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()
        
        # Load the dialog components.
        self.ui = uic.loadUi('employees_dialog.ui')

        
        ### PER EMPLOYEE
        # Employees menu and query button event handlers.
        self.ui.employees_cb.currentIndexChanged.connect(self._initialize_table)
        self.ui.query_button.clicked.connect(self._enter_sales_data)

        # Initialize the employees menu and sales table.
        self._initialize_employees_menu()
        self._initialize_table()
        self.ui.monthly_radio.toggled.connect(self._initialize_table)
        self.ui.quarterly_radio.toggled.connect(self._initialize_table)


        ### PER LOCATION
        # Location menu and query button event handlers.
        # When the country is changed, initialize the city menu again
        self.ui.country_cb.currentIndexChanged.connect(self._initialize_city_menu)
        self.ui.query_button_location.clicked.connect(self._enter_sales_data_location)

        # Initialize the location menu and sales table.
        self._initialize_country_menu()
        self._initialize_table_location()
        self.ui.monthly_radio_location.toggled.connect(self._initialize_table_location)
        self.ui.quarterly_radio_location.toggled.connect(self._initialize_table_location)
        self.ui.country_cb.currentIndexChanged.connect(self._initialize_table_location)
        self.ui.city_cb.currentIndexChanged.connect(self._initialize_table_location)
        
    def show_dialog(self):
        """
        Show this dialog.
        """
        self.ui.show()
    
    def _initialize_employees_menu(self):
        """
        Initialize the salesrepemployee menu with names from the database.
        """
        sql = """
            SELECT firstName, lastName FROM pinnacle_wh.salesrepemployee
            ORDER BY firstName, lastName
            """
        rows, _ = do_query(sql)

        # Set the menu items to the employees' names.
        for row in rows:
            name = row[0] + ' ' + row[1]
            self.ui.employees_cb.addItem(name, row)
    
    def _initialize_country_menu(self):
        """
        Initialize the country menu of clients' location from the database.
        """
        sql = """
            SELECT distinct country FROM customers
            ORDER BY country
            """
        rows_country, _ = do_query(sql)

        # Set the menu items to the country
        for row in rows_country:
            c = row[0]
            self.ui.country_cb.addItem(c, row)

    def _initialize_city_menu(self):
        """
        Initialize the city menu of clients' location from the database.
        """
        self.ui.city_cb.clear()
        country = self.ui.country_cb.currentData()
        _country = country[0]
        sql = """
            SELECT distinct city FROM customers
            WHERE country = '""" + _country + """' ORDER BY city
            """ 
        
        rows_city, _ = do_query(sql)

        # Set the menu items to the city by selected country
        self.ui.city_cb.addItem("All", ("All",))
        for row in rows_city:
            c = row[0]
            self.ui.city_cb.addItem(c, row)
        
    def _initialize_table(self):
        """
        Clear the table and set the column headers.
        """
        self.ui.sales_table.clear()

        if self.ui.monthly_radio.isChecked():
            month_quater = ' Month '
        elif self.ui.quarterly_radio.isChecked():
            month_quater = ' Quater '

        col = ['  First Name  ', '  Last Name  ', '  Manager Name  ', month_quater, '  Year End  ', '  Revenue ($000) ']

        self.ui.sales_table.setHorizontalHeaderLabels(col)        
        adjust_column_widths(self.ui.sales_table)

    def _initialize_table_location(self):
        """
        Clear the table and set the column headers.
        """
        self.ui.sales_table_location.clear()

        if self.ui.monthly_radio_location.isChecked():
            month_quater = ' Month '
        elif self.ui.quarterly_radio_location.isChecked():
            month_quater = ' Quater '

        col = [' Country ', ' City ', ' First Name ', ' Last Name ', ' Manager Name ', month_quater, ' Year End ', ' Revenue ($000) ']

        self.ui.sales_table_location.setHorizontalHeaderLabels(col)        
        adjust_column_widths(self.ui.sales_table_location)
        
    def _enter_sales_data(self):    
        """
        Enter monthly/quaterly sales data from the query into 
        the star schema and return quaterly sales per
        each employee, then show the plot.
        """
        name = self.ui.employees_cb.currentData()
        first_name = name[0]
        last_name = name[1]

        if self.ui.monthly_radio.isChecked():
            month_quater = 'month'
        elif self.ui.quarterly_radio.isChecked():
            month_quater = 'qtr'

        sql = ( """
            SELECT sa.firstName, sa.lastName, sa.managerName, ca."""+ month_quater +""", ca.year, sum(sh.quantityOrdered*sh.priceEach)
            FROM shippedorders sh
            JOIN salesrepemployee sa ON sa.employeeNumber = sh.salesRepEmployeeNumber
            JOIN calendar ca ON ca.calendar_key = sh.calendar_key
            WHERE sa.firstName = '""" + first_name + """'
            AND sa.lastName = '""" + last_name + """'
            GROUP BY sa.firstName, sa.lastName, sa.managerName, """+ month_quater +""", ca.year
            ORDER BY sa.firstName, sa.lastName, ca.year, """+ month_quater +"""
            """ 
              )

        # Return data from database
        rows, count = do_query(sql)

        # Plot the sales performance
        df = pd.DataFrame(rows,columns=['First Name', 'Last Name', 'Manager Name', 'M/Q', 'Year', 'Revenue ($000)'])
        df['Time'] = pd.to_datetime(df['Year'].astype(str) + df['M/Q'].astype(str), format='%Y%m').dt.strftime('%m-%Y')

        # print(df)

        X = df['Revenue ($000)']
        Y = df['Time']
        # self.ui.graphicsView.clear()
        scene = QGraphicsScene()
        self.ui.label = QGraphicsView(scene)
        figure = Figure()
        figure.set_size_inches(len(X), 7)
        axes = figure.gca()
        axes.set_title(f"Sales Performance Of {first_name} {last_name}")
        axes.plot(Y, X, "-k", color="red", label="Revenue Made ($000)")
        axes.legend()
        axes.grid(True)
        axes.xaxis.label.set_size(5)

        canvas = FigureCanvas(figure)
        proxy_widget = scene.addWidget(canvas)

        self.ui.label.resize(100*len(X), 700)
        self.ui.label.show()
        
        # Set the sales data into the table cells.
        set_data_to_table_cells(self.ui.sales_table, rows, [5])
                
        adjust_column_widths(self.ui.sales_table)

    def _enter_sales_data_location(self):    
        """
        Enter monthly/quaterly sales data from the query into 
        the star schema and return quaterly sales of employees
        per location of clients.
        """
        country = self.ui.country_cb.currentData()
        _country = country[0]

        city = self.ui.city_cb.currentData()
        _city = city[0]

        if self.ui.monthly_radio_location.isChecked():
            month_quater = 'month'
        elif self.ui.quarterly_radio_location.isChecked():
            month_quater = 'qtr'

        if _city == 'All':
            _city = (f"cu.city")
        else:
            _city = (f"\'{_city}\'")
        
        sql = ( """
            SELECT cu.country, cu.city, sa.firstName, sa.lastName, sa.managerName, ca."""+ month_quater +""", ca.year, sum(sh.quantityOrdered*sh.priceEach)
            FROM shippedorders sh
            JOIN salesrepemployee sa ON sa.employeeNumber = sh.salesRepEmployeeNumber
            JOIN calendar ca ON ca.calendar_key = sh.calendar_key
            JOIN customers cu on cu.customerNumber = sh.customerNumber
            WHERE cu.country = '""" + _country + """'
            AND cu.city = """ + _city + """
            GROUP BY cu.country, cu.city, sa.firstName, sa.lastName, sa.managerName, ca."""+ month_quater +""", ca.year
            ORDER BY cu.country, cu.city, sa.firstName, sa.lastName, ca.year, ca."""+ month_quater +"""
            """ 
            )

        # Return data from database
        rows, count = do_query(sql)
        
        # Set the sales data into the table cells.
        set_data_to_table_cells(self.ui.sales_table_location, rows, [7])
                
        adjust_column_widths(self.ui.sales_table_location)
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = EmployeesDialog()
    form.show_dialog()
    sys.exit(app.exec_())