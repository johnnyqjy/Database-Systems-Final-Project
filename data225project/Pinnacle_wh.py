from mydbutils import make_connection, do_query_return_all, do_query
from pandas import DataFrame
import mysql.connector
import pandas as pd

def perform_ETL_warehouse():
    conn_warehouse = make_connection(config_file = 'pinnacle_wh.ini')
    cursor_warehouse = conn_warehouse.cursor()
    conn = make_connection(config_file = 'pinnacle_db.ini')
    cursor = conn.cursor()

    def make_table(table, sql):
        cursor_warehouse.execute(f"DROP TABLE IF EXISTS {table}")
        cursor_warehouse.execute(sql)

    # Calendar dimension
    sql =   ("""
            CREATE TABLE calendar
            (
                calendar_key INT NOT NULL AUTO_INCREMENT,
                full_date DATE,
                day_of_week VARCHAR(9),
                day_of_month INT,
                month INT,
                qtr INT,
                year INT,
                PRIMARY KEY (calendar_key)
            )
            """
            )

    make_table('calendar', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.calendar(full_date, day_of_week, 
                                                day_of_month, month, 
                                                qtr, year)
                SELECT DISTINCT requiredDate, dayname(requiredDate), 
                                day(requiredDate), month(requiredDate), 
                                quarter(requiredDate), year(requiredDate)
                FROM pinnacle_db.orders
                WHERE status = 'Shipped'
            """
        )

    cursor_warehouse.execute(sql)
    conn_warehouse.commit()

    # Sales Rep Emplpoyee dimension
    sql = ( """
            CREATE TABLE salesrepemployee
            (
                employeeNumber INT NOT NULL,
                lastName VARCHAR(50),
                firstName VARCHAR(50),
                email VARCHAR(100),
                managerName VARCHAR(100),
                managerEmail VARCHAR(100),
                PRIMARY KEY(employeeNumber)
            )
            """
        )
    make_table('salesrepemployee', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.salesrepemployee(employeeNumber, 
                                                    lastName,
                                                    firstName,
                                                    email,
                                                    managerName,
                                                    managerEmail)
                SELECT em1.employeeNumber, em1.lastName, em1.firstName, em1.email, concat(em2.firstName, ' ', em2.lastName) as managerName, em2.email as managerEmail
                FROM pinnacle_db.employees em1
                LEFT JOIN pinnacle_db.employees em2 ON em1.reportsTo = em2.employeeNumber
                WHERE em1.jobTitle = 'Sales Rep'
            """
            )

    cursor.execute(sql)
    conn.commit()

    # Product Line Dimension

    sql = ( """
            CREATE TABLE productline
            (
                productLineID INT NOT NULL AUTO_INCREMENT,
                productLineName VARCHAR(100),
                PRIMARY KEY(productLineID)
            )
            """
        )
    make_table('productline', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.productline(productLineName)
                SELECT distinct productLine FROM pinnacle_db.products
            """
        )

    cursor.execute(sql)
    conn.commit()

    # Product Dimension

    sql = ( """
            CREATE TABLE products
            (
                productCode varchar(15) NOT NULL,
                productName VARCHAR(100),
                buyPrice decimal(10,2) NOT NULL,
                PRIMARY KEY(productCode)
            )
            """
        )
    make_table('products', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.products(productCode,
                                                productName,
                                                buyPrice)
                SELECT productCode, productName, buyPrice 
                FROM pinnacle_db.products
                WHERE productCode in (Select productCode from pinnacle_db.orderdetails)
            """
        )

    cursor.execute(sql)
    conn.commit()

    # Customer Dimension

    sql = ( """
            CREATE TABLE customers
            (
                customerNumber INT NOT NULL,
                customerName VARCHAR(100),
                contactLastName VARCHAR(100),
                contactFirstName VARCHAR(100),
                phone VARCHAR(50),
                city VARCHAR(50),
                country VARCHAR(50),
                PRIMARY KEY(customerNumber)
            )
            """
        )
    make_table('customers', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.customers(customerNumber,
                                                customerName,
                                                contactLastName,
                                                contactFirstName,
                                                phone,
                                                city,
                                                country)
                SELECT customerNumber, customerName, contactLastName, contactFirstName, phone, city, country
                FROM pinnacle_db.customers
                WHERE salesRepEmployeeNumber is not NULL
            """
        )

    cursor.execute(sql)
    conn.commit()

    # Sales Fact Table

    sql = ( """
            CREATE TABLE shippedorders
            (
                orderNumber INT NOT NULL,
                calendar_key INT NOT NULL,
                customerNumber INT NOT NULL,
                salesRepEmployeeNumber INT NOT NULL,
                productCode varchar(15) NOT NULL,
                productLineID INT NOT NULL,
                quantityOrdered INT NOT NULL,
                priceEach decimal(10,2) NOT NULL,
                PRIMARY KEY(orderNumber, calendar_key, customerNumber, salesRepEmployeeNumber, productCode, productLineID)
            )
            """
        )

    make_table('shippedorders', sql)

    sql = ( """
            INSERT INTO pinnacle_wh.shippedorders(orderNumber,
                                                    calendar_key,
                                                    customerNumber,
                                                    salesRepEmployeeNumber,
                                                    productCode,
                                                    productLineID,
                                                    quantityOrdered,
                                                    priceEach)
                SELECT o.orderNumber, ca.calendar_key, cus.customerNumber, cus.salesRepEmployeeNumber, 
                    od.productCode, pl.productLineID, od.quantityOrdered, od.priceEach FROM pinnacle_db.orders o
                    JOIN pinnacle_db.orderdetails od on od.orderNumber = o.orderNumber
                    JOIN pinnacle_db.products pro on pro.productCode = od.productCode
                    JOIN pinnacle_wh.productline pl on pl.productLineName = pro.productLine
                    JOIN pinnacle_db.customers cus on cus.customerNumber = o.customerNumber
                    JOIN pinnacle_wh.calendar ca on ca.full_date = o.requiredDate
                    WHERE o.status = 'Shipped'
            """
        )

    cursor.execute(sql)
    conn.commit()

    cursor_warehouse.close()
    conn_warehouse.close()
    cursor.close()
    conn.close()