import sys
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, QApplication, QGraphicsScene, QGraphicsView
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from mydbutils import do_query, set_data_to_table_cells, adjust_column_widths

class ProductLinesDialog(QDialog):
    """
    The product lines dialog.
    """
    
    def __init__(self):
        """
        Load the UI and initialize its components.
        """
        super().__init__()
        
        # Load the dialog components.
        self.ui = uic.loadUi('productLines_dialog.ui')

        ### PER PRODUCT LINE
        # Product lines menu and query button event handlers.
        self.ui.product_lines_cb.currentIndexChanged.connect(self._initialize_table)
        self.ui.query_button.clicked.connect(self._enter_product_lines_data)
        
        # Initialize the product lines menu and the sales table.
        self._initialize_product_lines_menu()
        self._initialize_table()
        self.ui.monthly_radio.toggled.connect(self._initialize_table)
        self.ui.quarterly_radio.toggled.connect(self._initialize_table)

        ### PER LOCATION
        # Location menu and query button event handlers.
        # When the country is changed, initialize the city menu again
        self.ui.country_cb.currentIndexChanged.connect(self._initialize_city_menu)
        self.ui.query_button_location.clicked.connect(self._enter_product_lines_data_location)

        # Initialize the location menu and sales table.
        self._initialize_country_menu()
        self._initialize_table_location()
        self.ui.monthly_radio_location.toggled.connect(self._initialize_table_location)
        self.ui.quarterly_radio_location.toggled.connect(self._initialize_table_location)
        self.ui.country_cb.currentIndexChanged.connect(self._initialize_table_location)
        self.ui.city_cb.currentIndexChanged.connect(self._initialize_table_location)

        # Initialize years menu and draw pie chart
        self._initialize_years_menu()
        self.ui.query_button_location_pie.clicked.connect(self._draw_pie_chart)
        
    def show_dialog(self):
        """
        Show this dialog.
        """
        self.ui.show()
    
    def _initialize_years_menu(self):
        """
        Initialize the years of sales menu from the database.
        """
        sql = """
            SELECT distinct year FROM calendar
            """
        rows, _ = do_query(sql)

        # Set the menu items to the teacher names.
        for row in rows:
            year = str(row[0])
            self.ui.year_cb.addItem(year, row)
    
    def _initialize_product_lines_menu(self):
        """
        Initialize the product lines menu with product lines from the database.
        """
        sql = """
            SELECT productLineName FROM productline
            """
        rows, _ = do_query(sql)

        # Set the menu items to the teacher names.
        for row in rows:
            name = row[0]
            self.ui.product_lines_cb.addItem(name, row)
    
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

        col = ['  Product Line  ', month_quater, '  Year End  ', '  Quantity  ',
        '  Average Price Each ($000)  ', '  Total Sales ($000) ']

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

        col = [' Country ', ' City ', ' Product Line ', month_quater, ' Year End ', ' Quantity ',
        'Average Price Each ($000)', 'Total Sales ($000)']

        self.ui.sales_table_location.setHorizontalHeaderLabels(col)        
        adjust_column_widths(self.ui.sales_table_location)
        
    def _enter_product_lines_data(self):    
        """
        Enter monthly/quaterly sales data from the query into 
        the star schema and return quaterly sales per
        each product line and plot the graph.
        """    
        product_lines = self.ui.product_lines_cb.currentData()
        product_line = product_lines[0]

        if self.ui.monthly_radio.isChecked():
            month_quater = 'month'
        elif self.ui.quarterly_radio.isChecked():
            month_quater = 'qtr'
        
        sql = ( """
            SELECT pl.productLineName, ca."""+ month_quater +""", ca.year, sum(sh.quantityOrdered), ROUND(avg(sh.priceEach), 2), sum(sh.quantityOrdered*sh.priceEach)
            FROM pinnacle_wh.shippedorders sh
            JOIN pinnacle_wh.productline pl ON pl.productLineID = sh.productLineID
            JOIN pinnacle_wh.calendar ca ON ca.calendar_key = sh.calendar_key
            WHERE pl.productLineName = '""" + product_line + """' 
            GROUP BY pl.productLineName, ca."""+ month_quater +""", ca.year
            ORDER BY pl.productLineName, ca.year, ca."""+ month_quater +"""
            """ 
              )

        # Return sales data from database         
        rows, _ = do_query(sql)
        
        # Plot the sales performance
        df = pd.DataFrame(rows,columns=['Product Line', 'M/Q', 'Year End', 'Quantity', 'Average Price Each ($000)', 'Total Sales ($000)'])
        df['Time'] = pd.to_datetime(df['Year End'].astype(str) + df['M/Q'].astype(str), format='%Y%m').dt.strftime('%m-%Y')

        X = df['Quantity']
        Y = df['Time']
        # self.ui.graphicsView.clear()
        scene = QGraphicsScene()
        self.ui.label = QGraphicsView(scene)
        figure = Figure()
        figure.set_size_inches(len(X), 7)
        axes = figure.gca()
        axes.set_title(f"Sales Of {product_line}")
        axes.plot(Y, X, "-k", color="red", label="Quantity Sold")
        axes.legend()
        axes.grid(True)

        canvas = FigureCanvas(figure)
        proxy_widget = scene.addWidget(canvas)

        self.ui.label.resize(90*len(X), 700)
        self.ui.label.show()

        # Set the sales data into the table cells.
        # print(rows)
        set_data_to_table_cells(self.ui.sales_table, rows, [4, 5])
                
        adjust_column_widths(self.ui.sales_table)

    def _enter_product_lines_data_location(self):    
        """
        Enter monthly/quaterly sales data from the query into 
        the star schema and return quaterly sales per
        each product line with selected location of clients.
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
            SELECT cu.country, cu.city, pl.productLineName, ca."""+ month_quater +""", ca.year, sum(sh.quantityOrdered), ROUND(avg(sh.priceEach), 2), sum(sh.quantityOrdered*sh.priceEach)
            FROM pinnacle_wh.shippedorders sh
            JOIN pinnacle_wh.productline pl ON pl.productLineID = sh.productLineID
            JOIN pinnacle_wh.calendar ca ON ca.calendar_key = sh.calendar_key
            JOIN customers cu on cu.customerNumber = sh.customerNumber
            WHERE cu.country = '""" + _country + """' 
            AND cu.city = """ + _city + """
            GROUP BY cu.country, cu.city, pl.productLineName, ca."""+ month_quater +""", ca.year
            ORDER BY cu.country, cu.city, pl.productLineName, ca.year, ca."""+ month_quater +"""
            """ 
              )
        
        # Return sales data from database             
        rows, _ = do_query(sql)
        
        # Set the sales data into the table cells.
        # print(rows)
        set_data_to_table_cells(self.ui.sales_table_location, rows, [6, 7])
                
        adjust_column_widths(self.ui.sales_table_location)

    def _draw_pie_chart(self):
        """
        """
        country = self.ui.country_cb.currentData()
        _country = country[0]

        year = self.ui.year_cb.currentData()
        _year = str(year[0])

        sql = ( """
            SELECT cu.country, pl.productLineName, ca.year, sum(sh.quantityOrdered), ROUND(avg(sh.priceEach), 2), sum(sh.quantityOrdered*sh.priceEach)
            FROM pinnacle_wh.shippedorders sh
            JOIN pinnacle_wh.productline pl ON pl.productLineID = sh.productLineID
            JOIN pinnacle_wh.calendar ca ON ca.calendar_key = sh.calendar_key
            JOIN customers cu on cu.customerNumber = sh.customerNumber
            WHERE cu.country = '""" + _country + """'
            AND ca.year = '""" + _year + """'
            GROUP BY cu.country, pl.productLineName, ca.year
            ORDER BY cu.country, pl.productLineName, ca.year
            """ 
              )
        
        # Return sales data from database
        rows, _ = do_query(sql)
              
        # Creating dataset
        df = pd.DataFrame(rows,columns=['Country', 'Product Line', 'Year', 'Quantity', 'Average Price Each ($000)', 'Total Sales ($000)'])
        print(df)
        product_lines = df['Product Line']
        
        revenues = df['Total Sales ($000)']
        scene = QGraphicsScene()
        self.ui.label_year = QGraphicsView(scene)
        # Creating plot
        fig = plt.figure(figsize =(7, 7))
        plt.pie(revenues, labels = product_lines, autopct='%1.0f%%', pctdistance=1.1, labeldistance=1.2)
        plt.title(f"Pie Chart Of {_year} Total Sales ($000) Per Product Line In {_country}")

        canvas = FigureCanvas(fig)
        proxy_widget = scene.addWidget(canvas)

        self.ui.label_year.resize(700, 700)
        self.ui.label_year.show()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = ProductLinesDialog()
    form.show_dialog()
    sys.exit(app.exec_())