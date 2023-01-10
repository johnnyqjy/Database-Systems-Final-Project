from mysql.connector import MySQLConnection, Error
from configparser import ConfigParser
import sqlite3
from sqlite3 import OperationalError
import csv

def read_config(config_file = 'pinnacle_wh.ini', section = 'mysql'):
    parser = ConfigParser()
    parser.read(config_file)
    
    config = {}
    
    if parser.has_section(section):
        # Parse the configuration file.
        items = parser.items(section)
        
        # Construct the parameter dictionary.
        for item in items:
            config[item[0]] = item[1]
            
    else:
        raise Exception(f'Section [{section}] missing ' + \
                        f'in config file {config_file}')
    
    return config
        
def make_connection(config_file = 'pinnacle_wh.ini', section = 'mysql'):
    try:
        db_config = read_config(config_file, section)
        conn = MySQLConnection(**db_config)

        if conn.is_connected():
            return conn

    except Error as e:
        print('Connection failed.')
        print(e)
        
        return None

def do_query_multi(sql):
    cursor = None
    
    # Connect to the database.
    conn = make_connection()
        
    if conn != None:
        try:
            cursor = conn.cursor()
            results = cursor.execute(sql, multi=True)
            
        except Error as e:
            print('Query failed')
            print(e)
            
            return [(), 0]

    # Return the fetched data as a list of tuples,
    # one tuple per table row.
    if conn != None:
        for result in cursor.execute(sql, multi=True):
            print(result)
        rows = cursor.fetchall()
        count = cursor.rowcount
            
        conn.close()
        return [rows, count]
    else:
        return [(), 0]
    
def do_query(sql):
    cursor = None
    
    # Connect to the database.
    conn = make_connection()
        
    if conn != None:
        try:
            cursor = conn.cursor()
            cursor.execute(sql)
            
        except Error as e:
            print('Query failed')
            print(e)
            
            return [(), 0]

    # Return the fetched data as a list of tuples,
    # one tuple per table row.
    if conn != None:
        rows = cursor.fetchall()
        count = cursor.rowcount
            
        conn.close()
        return [rows, count]
    else:
        return [(), 0]

def do_query_return_all(conn, sql):
    cursor = None

    try:
        cursor = conn.cursor()
        cursor.execute(sql)

        # Return the all fetched data as a list of tuples,
        # one tuple per table row.
        rows = cursor.fetchall()
        count = cursor.rowcount
        
        cursor.close()
        return [rows, count]

    except Error as e:
        print('Query failed')
        print(e)

        cursor.close()
        return [(), 0]

def set_data_to_table_cells(ui_table, rows, money_index):
    """ Function to set data from list of tuples
    to ui_table cells, and change the column index
    in money_index to money value
    """
    from PyQt5.QtWidgets import QTableWidgetItem
    row_index = 0
    for row in rows:
        # print(row)
        column_index = 0
        i = 0
        for data in row:
            string_item = str(data)
            if i in money_index:
                string_item = "${:,.2f}".format(data)
            item = QTableWidgetItem(string_item)
            ui_table.setItem(row_index, column_index, item)
            column_index += 1
            i += 1

        row_index += 1

def adjust_column_widths(ui_table):
    """ Function to resize all the columns
    in the ui_table, the last column will
    be stretched
    """
    from PyQt5.QtWidgets import QHeaderView
    columns_count = ui_table.columnCount()
    header = ui_table.horizontalHeader()
    i = 0
    while i < columns_count:
        if i < columns_count - 1:
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        else:
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        i += 1

def executeScriptsFromFile(filename, config_file='pinnacle_db.ini'):
    """
    filename = "pinnacle_db.sql"
    """
    conn = make_connection(config_file)
    # Open and read the file as a single buffer
    fd = open(filename, 'r')
    sqlFile = fd.read()
    fd.close()
    check = 0

    # all SQL commands (split on ';')
    sqlCommands = sqlFile.split(';')

    # Execute every command from the input file
    if conn != None:
        try:
            cursor = conn.cursor()
            for command in sqlCommands:
                try:
                    cursor.execute(command)
                    check = 1
                except OperationalError:
                    print("Command skipped: ")

            cursor.close()
        except Error as e:
            print('Query failed')
            print(e)
    
    return check

def insert_csv(sql_insert, filename, config_file='pinnacle_db.ini'):
    conn = make_connection(config_file)
    cursor = conn.cursor()
    first = True
    check = 0
    with open(filename, newline='') as csv_file:
        data = csv.reader(csv_file, delimiter=',', quotechar='"')
        for row in data:
            if not first:
                try:
                    cursor.execute(sql_insert, row)
                    check = 1
                except Error:
                    print("ERROR: could be end of file")
            first = False
        conn.commit()
    
    cursor.close()
    return check
