# load db connection to ISOM3260 server
# Import cx_Oracle package and connect to Oracle Database
import cx_Oracle
import pandas as pd
import itertools

HOST_NAME = "/"
PORT_NUMBER = "/"
SERVICE_NAME = "/"
USERNAME = "/"
PASSWORD = "/"

dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
conn = cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) 

c = conn.cursor()


# clean/empty the server of all data

##################################################################################################################
# UPDATE: KEEP SEPARATE TRY STATEMENTS, TO PREVENT ONE DELETION FROM INTERFERING WITH THE OTHERS
# UPDATE: ADD CASCADE CONSTRAINTS TO REMOVE FOREIGN KEY CONSTRAINTS ON THAT TABLE BEFORE RE-CREATING IT
###################################################################################################################


## create tables
## insert data into each table (print to test; load the data into web pages)

################################# Reset all the tables ######################################################


def ExceptionHandlingFunction(sql_statement):
    try:
        c.execute(sql_statement)
    except:
        print("Failed statement: ", sql_statement)

ExceptionHandlingFunction(
        """
          DROP TABLE customers CASCADE CONSTRAINTS
        """)
ExceptionHandlingFunction(
        """
          DROP TABLE orders CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE employees CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE payment_methods CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE shipments CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE shippers CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE order_items CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE payments CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE invoices CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE shipment_items CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE products CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE product_category CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE suppliers CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE comments CASCADE CONSTRAINTS
        """) 
ExceptionHandlingFunction(
        """
          DROP TABLE transactions CASCADE CONSTRAINTS
        """) 

print("Database cleared")

################################# CREATE ALL TABLES, WITH PK CONSTRAINTS ######################################################
######## WARNING: DO NOT REFERENCE TABLES OR ITEMS THAT HAVE NOT BEEN REFERENCED YET !!!!!!!! -- ORDER MATTERS

c.execute(
    """
    CREATE TABLE customers (
        Customer_ID            VARCHAR2(8 BYTE) NOT NULL,
        Customer_FName         VARCHAR2(20 BYTE) NOT NULL,
        Customer_LName         VARCHAR2(20 BYTE) NOT NULL,
        Customer_Address       VARCHAR2(100 BYTE) NOT NULL,
        Customer_Email         VARCHAR2(50 BYTE) NOT NULL,
        Customer_Username      VARCHAR2(20 BYTE) NOT NULL,
        Customer_Password      VARCHAR2(60 BYTE) NOT NULL,
        Customer_Phone_Number  NUMBER(20) NOT NULL,
    CONSTRAINT customer_PK PRIMARY KEY (Customer_ID)
    )
    """) 

        # Note: because we are hashing the password, thus need extend the byte size of PW
    
c.execute(
    """
    CREATE TABLE orders(
        Orders_ID                           VARCHAR2(20 BYTE) NOT NULL,
        Orders_Price                        NUMBER(10,2),
        Orders_OrderTimeStamp               DATE    DEFAULT SYSDATE,       
        Orders_DeliveryFee                  NUMBER(10,2),
        Orders_RequiredDeliveryTimeStamp    DATE DEFAULT SYSDATE,
        Orders_Status                       VARCHAR2(50 BYTE) NOT NULL,
        Customer_ID_FK                         VARCHAR2(8 BYTE) NOT NULL,
        Employees_ID_FK                         VARCHAR2(8 BYTE) NOT NULL,
    CONSTRAINT orders_PK PRIMARY KEY (Orders_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE employees(
        Employees_ID              VARCHAR2(20 BYTE) NOT NULL,
        Employees_FName           VARCHAR2(20 BYTE) NOT NULL,
        Empolyees_LName           VARCHAR2(20 BYTE) NOT NULL,
        Empolyees_Username        VARCHAR2(20 BYTE) NOT NULL,
        Employees_Password        VARCHAR2(60 BYTE) NOT NULL,
        Employees_Email           VARCHAR2(50 BYTE) NOT NULL,
        Employees_Position        VARCHAR2(20 BYTE) NOT NULL,
        Employees_Phone_Number    NUMBER(20),
    CONSTRAINT employees_PK PRIMARY KEY (Employees_ID)
    )
    """)

c.execute(
    """
    CREATE TABLE Payment_methods(
        Payment_Methods_ID      VARCHAR(20 BYTE) NOT NULL,
        Payment_Methods_Type    VARCHAR(30 BYTE) NOT NULL,
        Customer_ID_FK          VARCHAR2(8 BYTE) NOT NULL,
    CONSTRAINT Payment_Methods_PK PRIMARY KEY (Payment_Methods_ID),
    CONSTRAINT Payment_methods_FK1 FOREIGN KEY (Customer_ID_FK) REFERENCES customers(Customer_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE Shipments(
        Shipments_ID    VARCHAR(20 BYTE) NOT NULL,
        Employees_ID_FK VARCHAR2(8 BYTE) NOT NULL,
    CONSTRAINT Shipments_PK PRIMARY KEY (Shipments_ID),
    CONSTRAINT Shipments_FK1 FOREIGN KEY (Employees_ID_FK) REFERENCES employees(Employees_ID)
    )
    """)

c.execute(
    """
    CREATE TABLE Shippers(
        Shippers_ID                  VARCHAR(20 BYTE) NOT NULL,
        Shippers_Name                VARCHAR(50 BYTE) NOT NULL,
        Shippers_Email               VARCHAR(50 BYTE) NOT NULL,
        Shippers_Phone_Number        NUMBER(20) NOT NULL,
        Shippers_Manager             VARCHAR(50 BYTE) NOT NULL,
        Shippers_Transport_Method    VARCHAR(20 BYTE) NOT NULL,
    CONSTRAINT Shippers_PK PRIMARY KEY (Shippers_ID)
    )
    """)

c.execute(
    """
    CREATE TABLE order_items(
        Order_Items_ID                VARCHAR(20 BYTE) NOT NULL,
        Order_Items_Product_Quantity  NUMBER(5),
        Order_Items_Unit_Price        NUMBER(10,2) NOT NULL,
        Order_Items_Discount          NUMBER(10,2) NOT NULL,
        Order_Items_Sales_Tax         NUMBER(10,2) NOT NULL,
        Order_Items_Time_Stamp        DATE   DEFAULT SYSDATE,
        Order_Items_Status            VARCHAR(50 BYTE) NOT NULL,
        Orders_ID_FK                  VARCHAR2(8 BYTE) NOT NULL,
        Products_ID_FK                VARCHAR(20 BYTE) NOT NULL,
    CONSTRAINT order_items_PK PRIMARY KEY (Order_Items_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE invoices(
        Invoices_ID          VARCHAR(20 BYTE) NOT NULL,
        Invoices_Amount      NUMBER(20,2),
        Shipments_ID_FK      VARCHAR(20 BYTE) NOT NULL,
    CONSTRAINT invoices_PK PRIMARY KEY (Invoices_ID),
    CONSTRAINT invoices_FK1 FOREIGN KEY (Shipments_ID_FK) REFERENCES Shipments(Shipments_ID) 
    )
    """)

c.execute(
    """
    CREATE TABLE payments(
        Payments_ID            VARCHAR(20 BYTE) NOT NULL,
        Payments_Date          DATE   DEFAULT SYSDATE,
        Payments_Amount        NUMBER(20,2) NOT NULL,
        Payment_Methods_ID_FK  VARCHAR(20 BYTE) NOT NULL,
        Invoices_ID_FK         VARCHAR(20 BYTE) NOT NULL,
    CONSTRAINT payments_PK PRIMARY KEY (Payments_ID),
    CONSTRAINT payments_FK1 FOREIGN KEY (Payment_Methods_ID_FK) REFERENCES payment_methods(Payment_Methods_ID),
    CONSTRAINT payments_FK2 FOREIGN KEY (Invoices_ID_FK) REFERENCES invoices(Invoices_ID) 
    )
    """)

c.execute(
    """
    CREATE TABLE transactions(
        Transactions_ID            VARCHAR(20 BYTE) NOT NULL,
        Transactions_CreditCardNum        NUMBER(20) NOT NULL,
        Orders_ID_FK         VARCHAR2(20 BYTE) NOT NULL,
    CONSTRAINT transaction_PK PRIMARY KEY (Transactions_ID),
    CONSTRAINT transaction_FK1 FOREIGN KEY (Orders_ID_FK) REFERENCES orders(Orders_ID)
    )
    """)


c.execute(
    """
    CREATE TABLE products(
        Products_ID                   VARCHAR(20 BYTE) NOT NULL,
        Products_Name                 VARCHAR(400 BYTE) NOT NULL,
        Products_Selling_Price        NUMBER(10,2),
        Products_Discounted_Price     NUMBER(10,2),
        Products_Discount             NUMBER(3,2),
        Products_Cost_Price           NUMBER(10,2),
        Products_Inventory_Quantity   NUMBER(20),
        Products_PromotionOrNot       VARCHAR(20 BYTE) NOT NULL,
        Products_PromotionStartDate   DATE   DEFAULT SYSDATE,
        Products_PromotionEndDate     DATE   DEFAULT SYSDATE,
        Products_Description          VARCHAR(4000 BYTE) NOT NULL,
        Products_URL                  VARCHAR(800 BYTE) NOT NULL,
    CONSTRAINT products_PK PRIMARY KEY (Products_ID)
    )
    """)
# We retain the selling price column and a separate discount price column in case we wish to revert back from the discount and need a reference price
# EVERY TIME we use a discount, we need to recalculate the discount price !!!

    
c.execute(
    """
    CREATE TABLE product_category(
        Product_Categories_ID            VARCHAR(20 BYTE) NOT NULL,
        Product_Categories_Name          VARCHAR(50 BYTE) NOT NULL,
        Product_Categories_Description   VARCHAR(800 BYTE) NOT NULL,
    CONSTRAINT Product_Category_PK PRIMARY KEY (Product_Categories_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE suppliers(
        Suppliers_ID               VARCHAR(20 BYTE) NOT NULL,
        Suppliers_Brand_Name       VARCHAR(100 BYTE) NOT NULL,
        Suppliers_Telephone        NUMBER(20),
        Suppliers_Email            VARCHAR(50 BYTE) NOT NULL,
        Suppliers_Manager_Name     VARCHAR(50 BYTE) NOT NULL,
    CONSTRAINT suppliers_PK PRIMARY KEY (Suppliers_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE shipment_items(
        Shipment_Items_ID         VARCHAR(20 BYTE) NOT NULL,
        Shipment_Items_Date       DATE   DEFAULT SYSDATE,
        Shipment_Items_Method     VARCHAR(30 BYTE) NOT NULL,
        Shipment_Items_Status     VARCHAR(20 BYTE) NOT NULL,
        Shipments_ID_FK           VARCHAR(20 BYTE) NOT NULL,
        Products_ID_FK            VARCHAR(20 BYTE) NOT NULL,
    CONSTRAINT Shipment_Items_PK PRIMARY KEY (Shipment_Items_ID),
    CONSTRAINT Shipment_Items_FK1 FOREIGN KEY (Shipments_ID_FK) REFERENCES Shipments(Shipments_ID),
    CONSTRAINT Shipment_Items_FK2 FOREIGN KEY (Products_ID_FK) REFERENCES products(Products_ID)
    )
    """)
    
c.execute(
    """
    CREATE TABLE comments(
        Comments_ID         VARCHAR(20 BYTE) NOT NULL,
        Comments_Date       DATE   DEFAULT SYSDATE,
        Comments_Text             VARCHAR(800 BYTE) NOT NULL,
        Ratings_Value             NUMBER(2),
        Customer_ID_FK           VARCHAR(20 BYTE) NOT NULL,
        Products_ID_FK            VARCHAR(20 BYTE) NOT NULL,
        Comments_ShowOrHide       VARCHAR(8 BYTE) NOT NULL,
    CONSTRAINT Comments_PK PRIMARY KEY (Comments_ID),
    CONSTRAINT Comments_FK1 FOREIGN KEY (Customer_ID_FK) REFERENCES customers(Customer_ID),
    CONSTRAINT Comments_FK2 FOREIGN KEY (Products_ID_FK) REFERENCES products(Products_ID)
    )
    """)

print("Tables created")

# Redundant tables (e.g. shipping, invoices) are included for future scalability

################################# ALTER TO ADD FK ######################################################

c.execute(
    """
    ALTER TABLE orders
    ADD CONSTRAINT Orders_FK1
        FOREIGN KEY (Customer_ID_FK)
        REFERENCES customers(customer_ID)
    """)

c.execute(
    """
    ALTER TABLE orders
    ADD CONSTRAINT Orders_FK2
        FOREIGN KEY (Employees_ID_FK)
        REFERENCES employees(Employees_ID)
    """)

c.execute(
    """
    ALTER TABLE order_items
    ADD CONSTRAINT order_items_FK1
        FOREIGN KEY (Orders_ID_FK)
        REFERENCES orders(Orders_ID)
    """)
    
c.execute(
    """
    ALTER TABLE order_items
    ADD CONSTRAINT order_items_FK2
        FOREIGN KEY (Products_ID_FK)
        REFERENCES products(Products_ID)
    """)    

print("Foreign keys created")

################################# INSERT INTO TABLES ######################################################

#This insert is just a trial
# Guest user // Default user // Blank user to reference
c.execute(
    """
    INSERT INTO customers VALUES ('1', '1', '1', '1', '1', '1', '1', '123456')
    """)
    # Pt 1. You need to add all columns for a row, not just customer_id becaue we set them that they cannot be NULL
    # Pt 2. Use single quotes ' for individual items, not double quotes "


def clean_string(string):
    try:
        desc = str(string.encode('utf-8'))
    except:
        desc = str(string)
    for _ in range(10):
        try:
            desc = desc.replace("'", "")
        except:
            print()
        try:
            desc = desc.replace("  ", " ")
        except:
            print()
    return desc

import random

id_num = 0 # id number must be unique

# insert masks
mask_prods = pd.read_csv("data/mask_data.csv")
for index, row in mask_prods.iterrows():
    id = str(id_num)
    id_num+=1
    name = clean_string(row['name'])
    discount = 0.1
    selling_price_flt = random.uniform(1,100)
    selling_price_str = str(selling_price_flt)
    discount_price_flt = selling_price_flt*(1-discount)
    discount_price_str = str(discount_price_flt)
    cost_price_flt = selling_price_flt*0.65
    cost_price_str = str(cost_price_flt)
    invQ = str(random.uniform(0,1000))
    desc = clean_string(row['description'])
    url = row['imgurl']
    string = (
        f"INSERT INTO products VALUES ('{id}', '"
        + name[1:]
        + "', '"
        + selling_price_str
        + "', '"
        + discount_price_str
        + "', '"
        + str(discount)
        + "', '"
        + cost_price_str
        + "', '"
        + invQ
        + "', '"
        + "N"
        + "', "
        + "sysdate"
        + ", "
        + "sysdate"
        + ", '"
        + desc.replace("\t", "")
        + "', '"
        + url
        + "')"
    )
    c.execute(string)
    c.execute("commit")

# insert hand sanitzers
hand_prods = pd.read_csv("data/handsant_data.csv")
discount = 0.1
for index, row in hand_prods.iterrows():
    id = str(id_num)
    id_num+=1
    name = clean_string(row['name'])
    selling_price_flt = random.uniform(1,100)
    selling_price_str = str(selling_price_flt)
    discount_price_flt = selling_price_flt*(1-discount)
    discount_price_str = str(discount_price_flt)
    cost_price_flt = selling_price_flt*0.65
    cost_price_str = str(cost_price_flt)
    invQ = str(random.uniform(0,1000))
    desc = clean_string(row['description'])
    url = row['imgurl']
    string = (
        f"INSERT INTO products VALUES ('{id}', '"
        + name[1:]
        + "', '"
        + selling_price_str
        + "', '"
        + discount_price_str
        + "', '"
        + str(discount)
        + "', '"
        + cost_price_str
        + "', '"
        + invQ
        + "', '"
        + "N"
        + "', "
        + "sysdate"
        + ", "
        + "sysdate"
        + ", '"
        + desc.replace("\t", "")
        + "', '"
        + url
        + "')"
    )
    c.execute(string)
    c.execute("commit")


# inserting test comments into database
c.execute('SELECT Products_ID FROM products')
index=0
row = c.fetchone()
insert_commands=[]
while row is not None:
    product_id = int(row[0])
    insert_commands.append(
        f"""INSERT INTO comments VALUES ('{str(index)}', sysdate, 'Add a comment with the + icon', '5', '1', '{product_id}', 'show')"""
    )
    # SPECIAL NOTE: THERE SHOULD BE NO QUOTATION MARKS AROUND SYSDATE
    index+=1
    row = c.fetchone()
for insert in insert_commands:
    c.execute(insert)
    c.execute("commit") 
    # WARNING: EXECUTING A COMMAND WITHOUT COMMIT TO DB IS POINTLESS - WITHOUT COMMIT IS GOOD FOR DEBUGGING, BUT NOT FOR PRODUCTION

print("Tables filled")


# Note on fetchone vs fetchall
# Using a while loop
#cursor.execute("SELECT * FROM employees")
#row = cursor.fetchone()
#while row is not None:
#  print(row)
#  row = cursor.fetchone()

## Using the cursor as iterator
#cursor.execute("SELECT * FROM employees")
#for row in cursor:
#  print(row)


#* In products table, add promotion_yes/no, promotion_startdate, promotion_edddate
#* For new products, auto set promotion_yes/no to Yes (users can also manually set promotion to Yes for random products)
#* We assume promotions can last at most 2 weeks only, so the startdate is autoset to sysdate, and enddate is just sysdate+2wks

#/* test first: For UI, we need a scrolling bar at top of page to show all products+imgs of those items in promotion [https://www.w3schools.com/w3css/w3css_slideshow.asp]


c.execute(
        """
        insert into employees values ('1', 'siddu', 'datta', 'sidudatta', 'ilovesid', 'siddu@sid.com', 'ceo', 12345678)
    """)

c.execute(
        """
    insert into employees values ('2', 'sidddu', 'ddatta', 'siduddatta', 'ilovesidd', 'sidddu@sid.com', 'cio', 12452678)    
    """)

c.execute(
        """
    insert into employees values ('3', 'siddduu', 'ddattta', 'siduuddatta', 'ilooovesidd', 'siddduuu@sid.com', 'coo', 13452678)    
    """)



# fake orders data -- FOR DEBUGGING PURPOSES ONLY -- WARNING: initializing shopping cart upon database creation means customer has orders before even adding to cart
#c.execute(
#        """
#    insert into orders values ('1', 1.2, sysdate, 1, sysdate, 'unpaid', '1', '1')    
#    """)

#c.execute(
#        """
#        insert into orders values ('2', 1.4, sysdate, 9, sysdate, 'completed', '1', '2')            
#    """)

#c.execute(
#        """
#    insert into orders values ('3', 1.7, sysdate, 9, sysdate, 'completed', '1', '3')    
#    """)

#c.execute(
#        """
#    insert into orders values ('4', 1.2, sysdate-1, 1, sysdate-1, 'completed', '1', '1')    
#    """)

#c.execute(
#        """
#        insert into orders values ('5', 1.4, sysdate-1, 9, sysdate-1, 'completed', '1', '2')            
#    """)

#c.execute(
#        """
#    insert into orders values ('6', 1.7, sysdate-1, 9, sysdate-1, 'completed', '1', '3')    
#    """)

#c.execute(
#        """
#    insert into orders values ('7', 1.2, sysdate-31, 1, sysdate-31, 'completed', '1', '1')    
#    """)

#c.execute(
#        """
#        insert into orders values ('8', 1.4, sysdate-31, 9, sysdate-31, 'completed', '1', '2')            
#    """)

#c.execute(
#        """
#    insert into orders values ('9', 1.7, sysdate-31, 9, sysdate-31, 'completed', '1', '3')    
#    """)

#c.execute(
#        """
#    insert into orders values ('10', 1.2, sysdate-365, 1, sysdate-365, 'completed', '1', '1')    
#    """)

#c.execute(
#        """
#        insert into orders values ('11', 1.4, sysdate-365, 9, sysdate-365, 'delivery', '1', '2')            
#    """)

#c.execute(
#        """
#    insert into orders values ('12', 1.7, sysdate-365, 9, sysdate-365, 'delivery', '1', '3')    
#    """)

#c.execute(
#        """
#    insert into orders values ('13', 1.2, sysdate-365, 1, sysdate-365, 'delivery', '1', '1')    
#    """)

#c.execute(
#        """
#        insert into orders values ('14', 1.4, sysdate-1000, 9, sysdate-1000, 'delivery', '1', '2')            
#    """)

#c.execute(
#        """
#    insert into orders values ('15', 1.7, sysdate-1000, 9, sysdate-1000, 'delivery', '1', '3')    
#    """)


## fake order items

#c.execute(
#    """
#    INSERT into order_items values ('1', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
#    """)
#c.execute(
#    """
#    INSERT into order_items values ('2', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
#    """)
#c.execute(
#    """
#    INSERT into order_items values ('3', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
#    """)
#c.execute(
#    """
#    INSERT into order_items values ('4', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
#    """)
#c.execute(
#    """
#    INSERT into order_items values ('5', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
#    """)

c.execute("commit")

print("Fake data initialized")