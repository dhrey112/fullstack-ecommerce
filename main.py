################################################# IMPORTS ##################################################################
from flask import *
import sqlite3, hashlib, os
from werkzeug.utils import secure_filename
import requests
import random
import cx_Oracle
from flask import jsonify
from flask import request
import json
import pandas as pd
import datetime
import string

current_page=0 # global variable

HOST_NAME = "/"
PORT_NUMBER = "/"
SERVICE_NAME = "/"
USERNAME = "/"
PASSWORD = "/"

dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
conn = cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) 

c = conn.cursor()


app = Flask(__name__)
app.secret_key = 'random string' # NEEDED


################################################ ECOMMERCE ############################################################
#Home page
@app.route("/")
@app.route("/home", methods=["GET", "POST"])
def root():
    global current_page # Note: need to place "global" to reference the global variable each time you wish to call its value in a function

    try:
        loggedIn, loggedIn_employee, email, position = getLoginDetails()
        dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
        with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
            
            searchQuery = request.args.get('searchQuery')
            cur = conn.cursor()

            # auto-check on promotions: if sysdate is past the promotion_enddate, then set promotion_yesno to N
            ## For testing, set the condition as sysdate+15
            cur.execute("SELECT Products_ID, Products_Name, Products_Selling_Price, Products_Discounted_Price, Products_Discount, Products_Cost_Price, Products_Inventory_Quantity, Products_PromotionOrNot, Products_PromotionStartDate, Products_PromotionEndDate, Products_Description, Products_URL FROM products WHERE Products_PromotionOrNot LIKE 'Y'")
            cur.execute("""
            UPDATE products
            SET Products_PromotionOrNot =  CASE
                                                WHEN SYSDATE > Products_PromotionEndDate THEN
                                                  'N'
                                                ELSE
                                                  'Y'
                                             END
            """)
            conn.commit() # not necessary to commit, because in thise connection session we already modified DB before pulling data; after conn closes, updates are rolled back
            # works when set condition to SYSDATE+15

            ### Search Functionality ####
            if filter_NoneCheck(searchQuery) == True:
                cur.execute('SELECT Products_ID, Products_Name, Products_Selling_Price, Products_Discounted_Price, Products_Discount, Products_Cost_Price, Products_Inventory_Quantity, Products_Description, Products_URL FROM products ORDER BY Products_ID ASC')
            else:
                cur.execute(
                    f"SELECT Products_ID, Products_Name, Products_Selling_Price, Products_Discounted_Price, Products_Discount, Products_Cost_Price, Products_Inventory_Quantity, Products_Description, Products_URL FROM products WHERE lower(Products_Name) LIKE '%{str(searchQuery.lower())}%' ORDER BY Products_ID ASC "
                )
            itemData = cur.fetchall()


            ## Issues with search at the moment: 
            # 1. No combobox options
            ## Resolved issues
            # 2. Case sensitive search, i.e. "Mask" != "mask" -- FIXED
            ############################

            cur.execute("SELECT Products_ID, Products_Name, Products_Selling_Price, Products_Discounted_Price, Products_Discount, Products_Cost_Price, Products_Inventory_Quantity, Products_PromotionOrNot, Products_PromotionStartDate, Products_PromotionEndDate, Products_Description, Products_URL FROM products WHERE Products_PromotionOrNot LIKE 'Y'")
            # bug with promotion: for some reason, it still shows items that are labelled "N"
            promoData = cur.fetchall()

        itemData = parse(itemData)
        promoData = parse(promoData)

        # categories test
        categories = ['Mask', 'Hand Sanitizer']

        # pagination - criteria: no. of rows per page
        number_of_items_per_page = 3 # number of rows
        paginate_counter=0
        tmp=[]
        itemData_paginated_reflattened=[];
        for item in itemData:
            if paginate_counter < number_of_items_per_page:
                tmp.append(item)
                paginate_counter+=1
            if paginate_counter == number_of_items_per_page:
                itemData_paginated_reflattened.append(tmp)
                paginate_counter=0
                tmp=[]

        # display all products at once
        #return render_template('home.html', itemData=itemData, itemData_paginated_Count=list(range(len(itemData_paginated))), loggedIn=loggedIn, firstName=email, noOfItems=noOfItems, categories=categories)

        # display page by page
        if current_page > len(itemData_paginated_reflattened):
            current_page=-1

        # Warning: New products have no image url -- users can leave it blank? what if need render an image, home page breaks?


        try:
            return render_template('home.html', itemData=itemData_paginated_reflattened[current_page], itemData_paginated_Count=list(range(len(itemData_paginated_reflattened))), loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, categories=categories, promoData=promoData)

        except:
                # Bug
                # 1. Search is not perfect, cannot search for every type of search term in a product name
                # 2. New products added do not show up for some reason ***
                # -- not an image problem, even when leave valid URL it doesnt work
                # -- turns out the issue is LIKE function does not work as well as we want it to, specific terms do not pop up 
                # -- but when we print out, seems LIKE does capture the right items, just not being displayed though 
                # -- consider deleting the except handling to see the exact error 
                # -- soln: apparently it was an issue with the pagination

            return render_template('home.html', itemData=itemData, itemData_paginated_Count=list(range(len(itemData_paginated_reflattened))), loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, categories=categories, promoData=promoData)

    except: # General 404 Exception Handling, in case users search outside of available indices, or click Next to end of list
        # returns a blank page with no items to indicate to user that no products are available further
        return redirect("/")

@app.route("/productDescription")
def productDescription():
    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    productId = request.args.get('productId')
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        cur.execute(
            f'SELECT Products_ID, Products_Name, Products_Selling_Price, Products_Discounted_Price, Products_Discount, Products_Cost_Price, Products_Inventory_Quantity, Products_Description, Products_URL FROM products WHERE Products_ID = {str(productId)}'
        )
        productData = cur.fetchone()

    try:
        quantity_added= request.args.get('order')

        with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    f"SELECT Comments_ID, Comments_Date, Comments_Text, Ratings_Value, Customer_ID_FK, Products_ID_FK FROM comments WHERE Comments_ShowOrHide <> 'hide' AND Products_ID_FK = {str(productId)}"
                )
                commentsData = cur.fetchall()
                commentsData = parse(commentsData)
            except:
                flash("There was a problem posting your comment. Try making it shorter, for example.")
        try:
            avg_rating = [item[3] for item in commentsData[0]]
            avg_rating=pd.Series(avg_rating).mean()
        except: # in case we hide the one reserve comment
            avg_rating=0
        system_date = datetime.datetime.now().strftime('%d/%m/%Y')
        #print(quantity_added)
        if filter_NoneCheck(quantity_added) == False:
            if min(float(productData[6]), max(0,float(quantity_added))) != float(quantity_added):
                flash("The quantity you set has been adjusted.")
            if float((1-productData[4])*productData[2])*float(min(float(productData[6]), max(0,float(quantity_added))))> 99999999:
                flash("Sorry, we cannot handle orders worth more than HK$ 99,999,999.")
            AddToShoppingCart(email, productId, min(float(productData[6]), max(0,float(quantity_added))))
        return render_template("productDescription.html", data=productData, commentsData=commentsData, system_date=system_date, loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, avg_rating=avg_rating)
    except:
        flash("An error occurred. Please try again.")
        return render_template("productDescription.html", data=productData, commentsData=commentsData, system_date=system_date, loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, avg_rating=avg_rating)
        #return redirect("/")



def AddToShoppingCart(email, productId, quantity_added):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT Customer_ID from customers WHERE Customer_Email = '{str(email)}'"
        )
        find_CusID=cur.fetchall()[0][0]

    # Unit Test 1: Existing Order
    # find_CusID
    # Unit Tesr 2: No Existing Order
    #find_CusID = -1

    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
                      # Existing order
            Old_Orders_ID = cur.execute(
                f"SELECT Orders_ID from orders Where Orders_Status= 'unpaid' AND Customer_ID_FK = '{str(find_CusID)}'"
            ).fetchall()[0][0]
        except:
                      # Non-existing order
            Old_Orders_ID = cur.execute(
                f"SELECT Orders_ID from orders Where Orders_Status= 'unpaid' AND Customer_ID_FK = '{str(find_CusID)}'"
            ).fetchall()
                      

    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()

        Order_Items_Unit_Price = cur.execute(
            f"SELECT Products_Selling_Price from products where Products_ID = '{str(productId)}' "
        ).fetchall()[0][0]

        Order_Items_Discount = cur.execute(
            f"SELECT Products_Discount from products where Products_ID = '{str(productId)}' "
        ).fetchall()[0][0]

        Order_Items_Time_Stamp= cur.execute("SELECT Sysdate AS System_date FROM Dual").fetchall()[0][0]

        Order_Items_ID=CreateNewOrders_ID(20, "ABCDEFHIJK1234567890")

        # Ordering data for the purpose of displaying on the Shopping Cart; requires reconfirmation at Shopping Cart page
        # Orders_Price factors in (1) Discount, (2) product quantity; does not factor in (1) Sales tax
        if Old_Orders_ID == []:
            New_OrderID = CreateNewOrders_ID(8, "ABCDEF135790") #generate new Orders_id
            cur.execute(
                f"INSERT INTO orders VALUES( '{str(New_OrderID)}', '0', sysdate, '100', sysdate+15, 'unpaid', '{str(find_CusID)}', '1')"
            )
            command = f"INSERT INTO order_items VALUES('{str(Order_Items_ID)}', {str(quantity_added)}, {str(Order_Items_Unit_Price)},{str(Order_Items_Discount)}, 0.16, TO_DATE('{str(Order_Items_Time_Stamp)}', 'YYYY-MM-DD HH24:MI:SS'), 'added to cart', '{str(New_OrderID)}', '{str(productId)}')"
            cur.execute(command)
            cur.execute(
                f"UPDATE orders SET Orders_Price = Orders_Price + {str(float(quantity_added) * float(Order_Items_Unit_Price) * (1 - float(Order_Items_Discount)))} WHERE Orders_ID = '{str(New_OrderID)}'"
            )
        else:
            command = f"INSERT INTO order_items VALUES('{str(Order_Items_ID)}', {str(quantity_added)}, {str(Order_Items_Unit_Price)}, {str(Order_Items_Discount)}, 0.16, TO_DATE('{str(Order_Items_Time_Stamp)}', 'YYYY-MM-DD HH24:MI:SS'), 'added to cart', '{str(Old_Orders_ID)}', '{str(productId)}')"
            cur.execute(command)
            cur.execute(
                f"UPDATE orders SET Orders_Price = Orders_Price + {str(float(quantity_added) * float(Order_Items_Unit_Price) * (1 - float(Order_Items_Discount)))} WHERE Orders_ID = '{str(Old_Orders_ID)}'"
            )
        cur.execute("commit")

        # allow customers to enter 0 quantity too, in case they wish to have placeholder items in cart?

#######################################################################################################################


################################################# LOGIN ################################################################
#Fetch user details if logged in
def getLoginDetails():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            try:
                loggedIn = True
                loggedIn_employee = False
                cur.execute("SELECT Customer_ID, Customer_Email FROM customers WHERE Customer_Email = '" + session['email'] + "'")
                userId, email = cur.fetchone()
                position=0
            except:
                loggedIn_employee = True
                loggedIn = True
                cur.execute("SELECT Employees_ID, Employees_Email, Employees_Position FROM employees WHERE Employees_Email = '" + session['email'] + "'")
                userId, email, position = cur.fetchone()
        except:
            loggedIn = False
            loggedIn_employee = False
            email = 'Guest'
            position=0
    return (loggedIn, loggedIn_employee, email, position)

@app.route("/loginForm")
def loginForm():
    return render_template('login.html', error='')

@app.route("/employeeLoginForm")
def employeeLoginForm():
    return render_template('employeeLogin.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/employeeLogin", methods = ['POST', 'GET'])
def employeeLogin():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid_employee(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('employeeLogin.html', error=error)

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    conn = cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns)
    cur = conn.cursor()
    cur.execute('SELECT Customer_Password, Customer_Email FROM customers')
    data = cur.fetchall()
    return any(
        row[1] == email
        and row[0] == hashlib.md5(password.encode()).hexdigest()
        for row in data
    )

def is_valid_employee(email, password):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    conn = cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns)
    cur = conn.cursor()
    cur.execute('SELECT Employees_Password, Employees_Email FROM employees')
    data = cur.fetchall()
    return any(
        row[1] == email
        and row[0] == hashlib.md5(password.encode()).hexdigest()
        for row in data
    )

@app.route("/register", methods = ['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            #Parse form data    
            password = request.form['password']
            email = request.form['email']
            fname = request.form['fname']
            lname = request.form['lname']
            address = request.form['address']
            usrname = request.form['usrname']
            phoneNum = request.form['phoneNum']

            # Check if any row in customers table with the same email value

            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT Customer_Email FROM customers WHERE Customer_Email = '{str(email)}'"
                )
                uservalidation = cur.fetchall()
            uservalidation= parse(uservalidation)
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                if uservalidation ==[] or uservalidation is None or uservalidation=="":
                    cur.execute(
                        f"INSERT INTO customers (Customer_ID, Customer_FName, Customer_LName, Customer_Address, Customer_Email, Customer_Username, Customer_Password, Customer_Phone_Number) VALUES ('{int(random.uniform(1, 1000000))}', '{str(fname)}', '{str(lname)}', '{str(address)}', '{str(email)}', '{str(usrname)}', '{hashlib.md5(password.encode()).hexdigest()}', '{str(phoneNum)}')"
                    )
                    conn.commit()
                    msg = "Registered Successfully"
                else:
                    msg = "email already in use"
            return render_template("login.html", error=msg)
    except:
        msg = "Data validation failed"
        return render_template("register.html", error=msg)

@app.route("/employeeRegister", methods = ['GET', 'POST'])
def employeeRegister():
    try:
        if request.method == 'POST':
            #Parse form data    
            password = request.form['password']
            email = request.form['email']
            fname = request.form['fname']
            lname = request.form['lname']
            position = request.form['position']
            usrname = request.form['usrname']
            phoneNum = request.form['phoneNum']

            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
            #Check if email is in database
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                cur.execute(
                    f"SELECT Employees_Email FROM employees WHERE Employees_Email = '{str(email)}'"
                )
                uservalidation = cur.fetchall()
            uservalidation= parse(uservalidation)

            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                if uservalidation ==[] or uservalidation is None or uservalidation=="":
                    cur.execute(
                        f"INSERT INTO employees (Employees_ID, Employees_FName, Empolyees_LName, Empolyees_Username, Employees_Password, Employees_Email, Employees_Position, Employees_Phone_Number) VALUES ('{int(random.uniform(1, 1000000))}', '{str(fname)}', '{str(lname)}', '{str(usrname)}', '{hashlib.md5(password.encode()).hexdigest()}', '{str(email)}', '{str(position)}', '{str(phoneNum)}')"
                    )
                    conn.commit()
                    msg = "Registered Successfully"
                else:
                    msg = "email already in use"

            return render_template("employeeLogin.html", error=msg)
    except:
        msg = "Data validation failed"
        return render_template("employeeRegister.html", error=msg)

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

@app.route("/employeeregisterationForm")
def employeeregisterationForm():
    return render_template("employeeRegister.html")

@app.route("/changePassword", methods=["GET", "POST"])
def changePassword():
    if request.method != "POST":
        return render_template("changePassword.html")
    # assume no emal verification needed
    email = request.form['email']
    # ask user for new password
    newPassword = request.form['newpassword']
    newPassword = hashlib.md5(newPassword.encode()).hexdigest()

    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
        #Check if email is in database
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT Customer_Email FROM customers WHERE Customer_Email = '{str(email)}'"
        )
        uservalidation = cur.fetchall()
    uservalidation= parse(uservalidation)

    # update db with new password, search by email
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            if uservalidation !=[] and newPassword != "":
                print(
                    f"UPDATE customers SET Customer_Password = '{newPassword}' WHERE Customer_Email = '"
                    + email
                    + "'"
                )
                cur.execute(
                    f"UPDATE customers SET Customer_Password = '{newPassword}' WHERE Customer_Email = '"
                    + email
                    + "'"
                )
                #cur.execute("UPDATE customers SET Customer_Password = ? WHERE Customer_Email = ?", (newPassword, email))
                conn.commit()
                msg="Changed successfully (auto-verified)"
            else:
                conn.rollback()
                msg = "Failed, either email does not exist or password was empty"
        except:
            conn.rollback()
            msg = "Failed, either email does not exist or password was empty"
        return render_template("changePassword.html", msg=msg)



##################### Update Customer Profile ######################################
@app.route("/profile")
def profile():

    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    with cx_Oracle.connect (user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM customers where Customer_Email = '{str(email)}'"
        )
        CustomerData = cursor.fetchall()
    CustomerData = parse(CustomerData)
    return render_template("updateCustomerInfo.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, customerData=CustomerData)



#######################################################################################################################

########################################### SHOPPING CART ####################################################################


@app.route("/cart")
def ShoppingCart():

    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    CCNum = request.args.get("CCNum")
    try:
        confirmation_page=False
        if confirmation_page==False:
            show_payment=False

        OrderidData, CartData = cartItems()
        
        orderitemsID_divsList=[]
        for row in CartData:
            orderitemsID_divsList.append(row[3])
        
        # adjsuted Quantity value
        Q_updatedList=[]
        for id in orderitemsID_divsList:
            Q = request.args.get(str(id))
            Q_updatedList.append(Q)
        

        # When ConfirmOrder button is pressed
        try:
            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                # update quantity
                for i in range(len(Q_updatedList)):
                    # max btn-add possible
                    cur.execute("SELECT Products_Inventory_Quantity FROM products, order_items WHERE Order_Items_ID = '" + str(orderitemsID_divsList[i]) + "' AND products.Products_ID = order_items.Products_ID_FK ")
                    maxQ_Prod = cur.fetchone()
                    print(maxQ_Prod)
                    string = "UPDATE order_items SET Order_Items_Product_Quantity = '" + str(min(float(maxQ_Prod[0]), float(max(0,float(Q_updatedList[i]))))) + "' WHERE Order_Items_ID = '" + str(orderitemsID_divsList[i]) + "'"
                    cur.execute(string)
                    conn.commit()
                    show_payment=True
                    # When ConfirmPayment button is pressed
                    if 'Enter your Credit Card number here' not in CCNum:
                        string = "INSERT INTO TRANSACTIONS VALUES ( '" + str(CreateNewOrders_ID(8, "ABCDEF135790")) + "', " + str(CCNum) + ", '" + str(OrderidData) + "')"
                        cur.execute(string)
                        conn.commit()
                        confirmation_page=True
                    OrderidData, CartData = cartItems()
        except:
            print()

        
        if confirmation_page == False:
            OrderidData, CartData = cartItems()
            try:
                # prepare total price -- non-dynamic
                Q_updatedList=[]
                for id in orderitemsID_divsList:
                    Q = request.args.get(str(id))
                    Q_updatedList.append(Q)
                totalP=0
                orderitemPrices=[]
                for row in CartData:
                    orderitemPrices.append(row[1])
                for i in range(len(orderitemPrices)):
                    totalP+=float(orderitemPrices[i])*float(min(float(maxQ_Prod[0]), float(max(0,float(Q_updatedList[i])))))
            except:
                    totalP=0

            return render_template("cart.html", CartData=CartData, loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, show_payment=show_payment, totalP=totalP)

        if confirmation_page == True:
            OrderidData, CartData = cartItems() # This the the absolute latest values obtained from the user's cart
            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                # Update quantities on the database
                Q_updatedList=[]
                for id in orderitemsID_divsList:
                    Q = request.args.get(str(id))
                    Q_updatedList.append(Q)
                for i in range(len(Q_updatedList)):
                    # max btn-add possible
                    #print("fail")
                    cur.execute("SELECT Products_Inventory_Quantity FROM products, order_items WHERE Order_Items_ID = '" + str(orderitemsID_divsList[i]) + "' AND products.Products_ID = order_items.Products_ID_FK ")
                    maxQ_Prod = cur.fetchone()
                    #print(maxQ_Prod)
                    string = "UPDATE order_items SET Order_Items_Product_Quantity = '" + str(min(float(maxQ_Prod[0]), float(max(0,float(Q_updatedList[i]))))) + "' WHERE Order_Items_ID = '" + str(orderitemsID_divsList[i]) + "'"
                    cur.execute(string)
                    conn.commit()
                # Update stock quantity in products table
                orderitemProducts=[]
                for row in CartData:
                    orderitemProducts.append(row[4])
                for i in range(len(orderitemProducts)):
                    string = "UPDATE products SET Products_Inventory_Quantity = (CASE WHEN Products_Inventory_Quantity - " + str(Q_updatedList[i]) + " < 0 THEN 0 ELSE Products_Inventory_Quantity - " + str(Q_updatedList[i]) + "  END) WHERE Products_ID = '" + str(orderitemProducts[i]) + "'"
                    cur.execute(string)
                    conn.commit()
                # Update Price & Status in Orders
                totalP=0
                orderitemPrices=[]
                for row in CartData:
                    orderitemPrices.append(row[1])
                for i in range(len(orderitemPrices)):
                    totalP+=float(orderitemPrices[i])*float(min(float(maxQ_Prod[0]), float(max(0,float(Q_updatedList[i])))))
                string = "UPDATE orders SET Orders_Status = 'preparation',  Orders_Price = " + str(totalP) + " WHERE Orders_ID = '" + str(OrderidData) + "'"
                cur.execute(string)
                conn.commit()

            return render_template("confirmation.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email)
    except:
        # in case of empty shopping cart, or guest login
        flash('Shopping cart is empty. Perhaps you could try logging in as a customer and adding to cart!')
        return render_template("cart.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email)

def cartItems():
    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        cur.execute("SELECT Orders_ID FROM orders, customers where orders.Customer_ID_FK = customers.Customer_ID AND Orders_Status = 'unpaid' AND customers.Customer_Email = '"+str(email)+"'")
        OrderidData = cur.fetchall()
        print(OrderidData)
    OrderidData = parse(OrderidData)[0][0][0]
    print(OrderidData)
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        cur.execute("SELECT Order_Items_Product_Quantity, Order_Items_Unit_Price*(1-Order_Items_Discount), Products_Name, Order_Items_ID, Products_ID FROM order_items, products WHERE order_items.Orders_ID_FK = '" + str(OrderidData) + "' AND products.Products_ID = order_items.Products_ID_FK")
        CartData = cur.fetchall()
    CartData = parse(CartData)[0]
    return OrderidData, CartData


@app.route("/order")
def ordersCustomer():

    loggedIn, loggedIn_employee, email, position = getLoginDetails()

    # combobox -- obtain a list of all unique values in the STATUS column for filterbox
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        combobox_list = cur.execute("SELECT DISTINCT Orders_Status FROM orders, customers where orders.Customer_ID_FK = customers.Customer_ID AND customers.Customer_Email = '"+str(email)+"'")
        combobox_list = [i[0] for i in list(cur.fetchall())]

    filter_status = request.args.get('status')
    
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            if filter_NoneCheck(filter_status)  == True:
                cur.execute("SELECT * FROM orders, customers where orders.Customer_ID_FK = customers.Customer_ID AND customers.Customer_Email = '"+str(email)+"' ORDER BY Orders_OrderTimeStamp DESC")
                orderData = cur.fetchall()
            else:
                cur.execute("SELECT * FROM orders, customers WHERE Orders_Status = '"+str(filter_status)+"' AND orders.Customer_ID_FK = customers.Customer_ID AND customers.Customer_Email = '"+str(email)+"'  ORDER BY Orders_OrderTimeStamp DESC")
                orderData = cur.fetchall()
        except:
            cur.execute("SELECT * FROM orders, customers where orders.Customer_ID_FK = customers.Customer_ID AND customers.Customer_Email = '"+str(email)+"'  ORDER BY Orders_OrderTimeStamp DESC")
            orderData = cur.fetchall()
    orderData = parse(orderData)

    return render_template("customerOrders.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, combobox_list=combobox_list, orderData=orderData)





########################################### ORDER MGMT ####################################################################

##################### Employee's Order Mgmt System ######################################
@app.route("/orders")
def ordersEmployee():

    # We have 2 filters
    filter_order = request.args.get('filter_order')
    filter_customer = request.args.get('filter_customer')

#######
#Assumptions#
# 1) all orders are shipped together so all items in one order has the same status
########
    
    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    if loggedIn_employee == False:
        return redirect("/")

    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    
    # combobox -- obtain a list of all unique values in the STATUS column for filterbox
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        combobox_list = cur.execute("SELECT DISTINCT Orders_ID FROM orders")
        combobox_list = [i[0] for i in list(cur.fetchall())]

    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:

            if filter_NoneCheck(filter_order) == True:
                if filter_NoneCheck(filter_customer) == True:
                    cur.execute('SELECT * FROM orders ORDER BY Orders_ID ASC')        
            if  filter_NoneCheck(filter_order) == False:
                if filter_NoneCheck(filter_customer) == True:
                    cur.execute("SELECT * FROM orders WHERE Orders_ID = '" + str(filter_order) + "' ORDER BY Orders_ID ASC")
            if filter_NoneCheck(filter_customer) == False:
                if filter_NoneCheck(filter_order) == True: 
                    cur.execute("SELECT * FROM orders WHERE Customer_ID_FK = '" + str(filter_customer) + "' ORDER BY Orders_ID ASC")
            if filter_NoneCheck(filter_order) == False:
                if filter_NoneCheck(filter_customer) == False:  
                    cur.execute("SELECT * FROM orders WHERE Customer_ID_FK = '" + str(filter_customer) + "' and ORDERS_ID = '" + str(filter_order) + "' ORDER BY Orders_ID ASC")
            orderData = cur.fetchall()
        except:
            cur.execute('SELECT * FROM orders ORDER BY Orders_ID ASC')
            orderData = cur.fetchall()
    orderData = parse(orderData)
    
    # This code is needed to filter out the table
    # However, this is only a use case with ONE filter; in our current use case, we have 3 filters
    # How do we manage the 3 filters to show 3 results, e.g. if a user leaves one of the filters blank?

    # In case a user makes an error, or wishes to display all results, then this query should be shown
    # The query shown here should be the same as the one for filter_order=='' and filter_customer=='' and filter_product==''

    
    # order items filterable by combobox
    filter_status = request.args.get('status')
    
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            if filter_NoneCheck(filter_status)  == True:
                cur.execute("SELECT * FROM order_items ORDER BY Order_Items_Time_Stamp DESC")
                orderItemsData = cur.fetchall()
            else:
                cur.execute("SELECT * FROM order_items where Orders_ID_FK = '"+str(filter_status)+"'")
                orderItemsData = cur.fetchall()
        except:
            cur.execute("SELECT * FROM order_items ORDER BY Order_Items_Time_Stamp DESC")
            orderItemsData = cur.fetchall()
    orderItemsData = parse(orderItemsData)

    return render_template("orderManagement.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, orderData=orderData, combobox_list=combobox_list, orderItemsData=orderItemsData)

#############################################################################################

########################################### PROFILE MGMT ####################################################################

@app.route("/inventory")
def inventoryManagement():
    loggedIn, loggedIn_employee, email, position = getLoginDetails()
    if loggedIn_employee == False:
        return redirect("/")
    filter = request.args.get('filter')
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            if filter == "":
                cur.execute('SELECT * FROM products ORDER BY Products_ID ASC')
            if filter != "":
                cur.execute("SELECT * FROM products WHERE lower(Products_Name) LIKE '%" + str(filter.lower()) + "%'  ORDER BY Products_ID ASC")
        except:
            cur.execute('SELECT * FROM products ORDER BY Products_ID ASC')
        itemData = cur.fetchall()
    itemData = parse(itemData)
    return render_template("inventory.html", itemData=itemData, loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email)

#def updateInventorySQL():
    # when /placeholder page is updated, Cases listed below:
    # Case 1. Insert new product
    # Case 2. Delete a product -- set quantity=0
    # Case 3: Update a product information
    # Expected user flow: 
    # (i) user filters for an item and adds a row or modifies etc
    # or (ii) user directly adds to a new row or deletes smthg 

    # implementation:
    # 1. retrieve information from /placeholder
    # 2. parse it for the values
    # 3. craft & execute DELETE statements on SQL db
    # 4. craft & execute INSERT statements on SQL db

########################################### SEARCH QUERYING ####################################################################
########################################### .............. ####################################################################

#######################################################################################################################

########################################### MANAGER DASHBOARD ####################################################################
########################################### .............. ####################################################################

@app.route("/managerdashboard")
def managerdashboard():
    loggedIn, loggedIn_employee, email, position = getLoginDetails()

    # authorization check
    if loggedIn_employee == False:
        return redirect("/")
    if "manager" not in position.lower():
        return redirect("/")

    #daily
    filter_dailysales = request.args.get('filter_dailysales')
    dailysales = dailySales(filter_dailysales)
    #monthly
    filter_monthlysales = request.args.get('filter_monthlysales')
    monthlysales = monthlySales(filter_monthlysales)    
    
    todayorders = todayOrders()
    todayorderitems = todayOrderItems()
    
    fiveproducts = fiveProducts()
    restockinventory = restockInventory()
    fivemembers = fiveMembers()
    orderstatus = orderStatus()
    discountview = discountView()
    comments = commentHide()

    filter_product = request.args.get('filter_product')
    productinfor = productInfor(filter_product)
    
    return render_template("managerdashboard.html", loggedIn=loggedIn, loggedIn_employee=loggedIn_employee, firstName=email, dailysales=dailysales, monthlysales=monthlysales, todayorders=todayorders, fiveproducts=fiveproducts, fivemembers=fivemembers, restockinventory=restockinventory, orderstatus=orderstatus, discountview=discountview, comments=comments, productinfor=productinfor, todayorderitems=todayorderitems)
    

#we should show day, total amount of sales, group by data 
def dailySales(filter_dailysales):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            # NOTE: UPDATE THE CONDITIONS WITH FUNCTION CHECK
            if filter_NoneCheck(filter_dailysales) == False:
                cur.execute("SELECT TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM-DD'), SUM(Orders_Price) FROM Orders WHERE TO_CHAR(Orders_OrderTimeStamp,'YYYY-MM-DD') = TO_CHAR('"+str(filter_dailysales)+"') AND Orders_Status <> 'unpaid' GROUP BY TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM-DD')") 
            if filter_NoneCheck(filter_dailysales) == True:
                cur.execute("SELECT TO_CHAR(SYSDATE, 'dd-mm-yyyy'), SUM(Orders_Price) FROM Orders WHERE TO_CHAR(Orders_OrderTimeStamp, 'dd-mm-yyyy') = TO_CHAR(SYSDATE, 'dd-mm-yyyy') AND Orders_Status <> 'unpaid'")
        except:
            cur.execute("SELECT TO_CHAR(SYSDATE, 'dd-mm-yyyy'), SUM(Orders_Price) FROM Orders WHERE TO_CHAR(Orders_OrderTimeStamp, 'dd-mm-yyyy') = TO_CHAR(SYSDATE, 'dd-mm-yyyy') AND Orders_Status <> 'unpaid'")
        dailysales = cur.fetchall()
    dailysales= parse(dailysales)
    return dailysales


def monthlySales(filter_monthlysales):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()
        try:
            if filter_NoneCheck(filter_monthlysales) == False:
                cur.execute("SELECT TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM'), SUM(Orders_Price) FROM Orders WHERE Orders_Status <> 'unpaid' AND TO_CHAR(Orders_OrderTimeStamp,'YYYY-MM') = TO_CHAR('"+str(filter_monthlysales)+"') GROUP BY TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM')") 
                monthlysales = cur.fetchall()
            if filter_NoneCheck(filter_monthlysales) == True:
                cur.execute("SELECT TO_CHAR(SYSDATE, 'mm/yyyy'), SUM(Orders_Price) FROM Orders WHERE Orders_Status <> 'unpaid' AND TO_CHAR(Orders_OrderTimeStamp, 'mm/yyyy') = TO_CHAR(SYSDATE, 'mm/yyyy')")
                monthlysales = cur.fetchall()
        except:
            cur.execute("SELECT TO_CHAR(SYSDATE, 'mm/yyyy'), SUM(Orders_Price) FROM Orders WHERE TO_CHAR(Orders_OrderTimeStamp, 'mm/yyyy') = TO_CHAR(SYSDATE, 'mm/yyyy')")
            monthlysales = cur.fetchall()
    monthlysales= parse(monthlysales)
    return monthlysales

def todayOrders():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute("SELECT * FROM Orders WHERE TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM-DD') = TO_CHAR(SYSDATE, 'YYYY-MM-DD') AND Orders_Status <> 'unpaid' ORDER BY Orders_ID DESC")
        todayorders = cur.fetchall() 
    todayorders= parse(todayorders)
    return todayorders

def todayOrderItems():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute("SELECT Orders_ID, Order_Items_ID, Products_ID_FK, (Order_Items_Product_Quantity * Order_Items_Unit_Price * (1 - Order_Items_Discount) + Order_Items_Sales_Tax), Order_Items_Product_Quantity, Orders_OrderTimeStamp, Orders_Status FROM order_items, orders WHERE Orders_ID_FK = Orders_ID AND TO_CHAR(Orders_OrderTimeStamp, 'YYYY-MM-DD') = TO_CHAR(SYSDATE, 'YYYY-MM-DD') AND Orders_Status <> 'unpaid' ORDER BY Orders_ID, Orders_OrderTimeStamp DESC")
        #cur.execute("SELECT Orders_ID, Order_Items_ID, Products_ID_FK, (Order_Items_Product_Quantity * Order_Items_Unit_Price * (1 - Order_Items_Discount) + Order_Items_Sales_Tax), Order_Items_Product_Quantity, Order_Items_Time_Stamp, Order_Items_Status FROM order_items, orders WHERE Orders_ID_FK = Orders_ID AND TO_CHAR(Order_Items_Time_Stamp, 'YYYY-MM-DD') = TO_CHAR(SYSDATE, 'YYYY-MM-DD') AND Order_Items_Status <> 'unpaid' GROUP BY Orders_ID ORDER BY Order_Items_Time_Stamp DESC")
        todayorderitems = cur.fetchall() 
    todayorderitems= parse(todayorderitems)
    return todayorderitems

def fiveProducts():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute(
            """
            SELECT ID, NAME, TOTAL_SALES
            FROM (
                SELECT Products_ID_FK ID, Products_Name NAME, SUM(Order_Items_Product_Quantity) TOTAL_SALES
                FROM products, order_items, orders
                WHERE Products_ID = Products_ID_FK
                AND Orders_ID = Orders_ID_FK
                AND Orders_Status <> 'unpaid'
                GROUP BY Products_ID_FK, Products_Name
                ORDER BY TOTAL_SALES DESC
            )
            WHERE ROWNUM < 6
            """)     
        # ROWNUM INDEXING STARTS FROM 1
        fiveproducts = cur.fetchall() 
    fiveproducts= parse(fiveproducts)
    return fiveproducts

def fiveMembers():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute(
            """
            SELECT ID, USERNAME, TOTAL_SALES
            FROM (
                SELECT Customer_ID ID, Customer_Username USERNAME, SUM(Orders_Price) TOTAL_SALES
                FROM customers, orders
                WHERE Customer_ID = Customer_ID_FK AND Orders_Status <> 'unpaid'
                GROUP BY Customer_ID, Customer_Username
                ORDER BY TOTAL_SALES DESC
            )
            WHERE ROWNUM < 6
            """)
        fivemembers = cur.fetchall() 
    fivemembers= parse(fivemembers)
    return fivemembers

def restockInventory():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute("SELECT Products_Name, Products_ID, Products_Inventory_Quantity FROM Products WHERE Products_Inventory_Quantity = 0")
        restockinventory = cur.fetchall() 
    restockinventory= parse(restockinventory)
    return restockinventory

def productInfor(filter_product_only):
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor()     
        cur.execute("SELECT ID, NAME, TOTAL_SALES FROM (SELECT Products_ID_FK ID, Products_Name NAME, SUM(Order_Items_Product_Quantity) TOTAL_SALES FROM products, order_items, orders WHERE Products_ID = Products_ID_FK AND Orders_ID = Orders_ID_FK AND Orders_Status <> 'unpaid' AND Products_ID = '" + str(filter_product_only) + "' GROUP BY Products_ID_FK, Products_Name ORDER BY TOTAL_SALES DESC)")
        productinfor = cur.fetchall()
        if productinfor==[]:
            cur.execute("SELECT Products_ID, Products_Name FROM products WHERE Products_ID = '" + str(filter_product_only) + "'")
            productinfor = cur.fetchall() 
    productinfor= parse(productinfor)
    return productinfor

def orderStatus():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute(
            """
            SELECT Orders_Status, COUNT(Orders_Status) FROM orders GROUP BY Orders_Status
            """)      
        orderstatus = cur.fetchall() 
    orderstatus= parse(orderstatus)
    return orderstatus


def discountView():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute("SELECT Products_Name, Products_ID, Products_Discount, Products_Selling_Price, Products_Cost_Price FROM Products WHERE Products_Discount <> 0")
        discountview = cur.fetchall() 
    discountview= parse(discountview)
    return discountview


def commentHide():
    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
        cur = conn.cursor() 
        cur.execute("SELECT Comments_ID, Comments_Date, Comments_Text, Customer_ID_FK, Products_ID_FK, Comments_ShowOrHide FROM comments ORDER BY Comments_Date DESC, Comments_ShowOrHide DESC")
        comments = cur.fetchall() 
    comments= parse(comments)
    return comments

#######################################################################################################################

####################################################### DATA DUMP / LOG // DATA DEBUGGING POST PAGE #########################################################

@app.route("/placeholder")
def placeholder():
    return render_template("placeholder.html")

####################################################### REST API #########################################################

@app.route('/getmethod/<jsdata>')
def get_javascript_data(jsdata):
    return jsdata

@app.route('/postmethod', methods = ['POST'])
def get_post_javascript_data():
    global current_page

    jsdata = request.form['javascript_data']
    
    paginated = False

    # pagination
    if len(jsdata) == 3:
        if current_page > 0:
            current_page-=1
        paginated = True
    if len(jsdata) == 2:
        current_page+=1 # Issue: We do not set constraint to max page -- resolved
        paginated = True

    # DB insert commands
    if paginated == False:
        jsdata2 = jsdata[1:-1].split("},")
        jsdicts=[]
        for item in jsdata2:
            try:
                item2 = str(item) + "}"
                jsdicts.append(json.loads(item2))
            except:
                item2 = str(item)
                jsdicts.append(json.loads(item2))

        ######## |!| As soon as the POST request is made we need to update SQL

        # Data dump / print before post-processing
        print(jsdicts)

        if 'employees_id_fk' in jsdicts[0]:
            # order mgmt for employees
            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                for jsdict in jsdicts:
                    status = jsdict['orders_status'].split()[0]
                    string = """UPDATE orders SET Orders_ID = '""" + jsdict['orders_id'] + """', Customer_ID_FK = '""" + jsdict['customer_id_fk'] + """', Employees_ID_FK = '""" + jsdict['employees_id_fk'] + """', Orders_Status = '""" + str(status) + """', Orders_Price = '""" + jsdict['orders_price'] + """', Orders_OrderTimeStamp = TO_DATE('""" + jsdict['orders_ordertimestamp'] + """', 'YYYY-MM-DD HH24:MI:SS'), Orders_DeliveryFee = '""" + jsdict['orders_deliveryfee'] + """', Orders_RequiredDeliveryTimeStamp = TO_DATE('""" + jsdict['orders_requireddeliverytimestamp'] + """', 'YYYY-MM-DD HH24:MI:SS') WHERE Orders_ID = '""" + str(jsdict['orders_id']) + """'"""
                    cur.execute(string)
                    conn.commit()

            

        if 'your first name' in jsdicts[0]:
            jsdict = jsdicts[0]
            # customer profile update
            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                string = """UPDATE customers SET Customer_ID = '""" + jsdict['your customer id'] + """', Customer_FName = '""" + jsdict['your first name'] + """', Customer_LName = '""" + jsdict['your last name'] + """', Customer_Address = '""" + jsdict['your address'] + "', Customer_Email = '""" + jsdict['your email'] + """', Customer_Username = '""" + jsdict['your username'] + """', Customer_Phone_Number = '""" + jsdict['your phone number'] + """' WHERE Customer_ID = """ + str(jsdict['your customer id'])
                cur.execute(string)
                conn.commit()



        if 'date' in jsdicts[0]:
            # comment management
            jsdict = jsdicts[-1] # user can only make 1 comment; only last comment entered will be saved
            # 4. craft & execute INSERT statements on SQL db
            dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
            with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                cur = conn.cursor()
                cur.execute("""SELECT COUNT(*) FROM comments""")
                ROW = cur.fetchone()
                
                # If guest, then 'user' will be an entry "Guest"
                # If not guest, it writes the email -- either search the db for email then assign id, OR have id being recorded during user session
                if jsdict['user'] == 'Guest':
                    usrID=1 # user_id 1 is the default ANONYMOUS user_id for Guest users and employee users
                if jsdict['user'] != 'Guest':
                    try:
                        cur.execute("""SELECT Customer_ID FROM customers WHERE lower(Customer_Email) LIKE '%""" + str(jsdict['user'].lower()) + """%'""")
                        usrID = int(cur.fetchone()[0])
                    except:
                        usrID=1 # user_id 1 is the default ANONYMOUS user_id for Guest users and employee users

                # ERROR if say "I'm super naughty" -- ORA-01756: quoted string not properly terminated
                cur.execute("""SELECT COUNT(*) FROM comments WHERE Products_ID_FK = """ + str(jsdict['product id']))
                row_check = cur.fetchone()[0]
                print(len(jsdicts))
                print(row_check)
                if row_check == len(jsdicts):
                    print()
                else:
                    command = """INSERT INTO comments VALUES('"""+str(int(ROW[0])+1)+"""', sysdate, '""" + jsdict['comment'] + """', '""" + str(min(10,int(jsdict['rating']))) + """', '""" + str(usrID) + """', '""" + jsdict['product id'] + """', 'show')"""
                    cur.execute(command)
                    conn.commit()
                

        if "comment" in jsdicts[0]:
            # Hiding comments for manager
            for jsdict in jsdicts:
                show_and_tell = jsdict['show or hide'].split()[0]
                dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
                with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                    cur = conn.cursor()
                    string = """UPDATE comments SET Comments_ShowOrHide = '""" + show_and_tell + """' WHERE Comments_ID = '""" + str(jsdict['id']) + """'"""
                    cur.execute(string)
                    conn.commit()

        #else: # or do check for products_description
        if "products_inventory_quantity" in jsdicts[0]:
            # product management
            for jsdict in jsdicts:
                dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME)
                
                try: # update row
                    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
                    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                        cur = conn.cursor()
                        Y_or_N = jsdict['products_promotionornot'].split()[0]
                        #print(Y_or_N)
                        # Even sysdate needs to be configured into datetime with TO_DATE once it is in string form -- bug fixed: # 3. Check on a potential bug with old products auto-set for promotion
                        if Y_or_N == "N":
                            string = """UPDATE products SET Products_Name = '""" + jsdict['products_name'] + """', Products_Selling_Price = '""" + jsdict['products_selling_price'] + """', Products_Discount = '""" + jsdict['products_discount'] + """', Products_Cost_Price = '""" + jsdict['products_cost_price'] + """', Products_Inventory_Quantity = '""" + jsdict['products_inventory_quantity'] + """', Products_PromotionOrNot = '""" + Y_or_N + """', Products_PromotionStartDate = sysdate-1, Products_PromotionEndDate = sysdate-1, Products_Description = '""" + jsdict['products_description'] + """', Products_URL = '""" + jsdict['products_url'] + """' WHERE Products_ID = """ + str(jsdict['products_id'])
                        if Y_or_N == "Y":
                            string = """UPDATE products SET Products_Name = '""" + jsdict['products_name'] + """', Products_Selling_Price = '""" + jsdict['products_selling_price'] + """', Products_Discount = '""" + jsdict['products_discount'] + """', Products_Cost_Price = '""" + jsdict['products_cost_price'] + """', Products_Inventory_Quantity = '""" + jsdict['products_inventory_quantity'] + """', Products_PromotionOrNot = '""" + Y_or_N + """', Products_PromotionStartDate = sysdate, Products_PromotionEndDate = sysdate+14, Products_Description = '""" + jsdict['products_description'] + """', Products_URL = '""" + jsdict['products_url'] + """' WHERE Products_ID = """ + str(jsdict['products_id'])
                        # left out discount price computation because there is no real need to keep updating the db with its value; it is automatically recomputed whenever it is displayed to users
                        cur.execute(string)
                        conn.commit()
                except: # insert row
                    dsn_tns = cx_Oracle.makedsn(HOST_NAME, PORT_NUMBER, service_name=SERVICE_NAME) 
                    with cx_Oracle.connect(user=USERNAME, password=PASSWORD, dsn=dsn_tns) as conn:
                       cur = conn.cursor()
                       Y_or_N = jsdict['products_promotionornot'].split()[0]
                       cur.execute("""SELECT COUNT(*) FROM products""")
                       ROW = cur.fetchone()
                       if Y_or_N == "Y":
                           extra_special_products = ['Muller', 'ISOM3260', 'Samuel', 'HKUST', 'product', 'test']
                           if any(substring.lower() in jsdict['products_name'].lower() for substring in extra_special_products): # <Easter Egg>
                               cur.execute("""INSERT INTO products VALUES('""" +str(int(ROW[0])+1)+ """', '""" + jsdict['products_name'] + """', '""" + jsdict['products_selling_price'] + """', '""" + str(float(jsdict['products_selling_price'])*float(jsdict['products_discount'])) + """', '""" + jsdict['products_discount'] + """', '""" + jsdict['products_cost_price'] + """', '""" + jsdict['products_inventory_quantity']+ """', '""" + str(Y_or_N)+"""', sysdate, sysdate+14, '""" + jsdict['products_description'] + """', 'https://facultyprofiles.ust.hk/profiles/images/P000001426.jpg')""")
                           else:
                               cur.execute("""INSERT INTO products VALUES('""" +str(int(ROW[0])+1)+ """', '""" + jsdict['products_name'] + """', '""" + jsdict['products_selling_price'] + """', '""" + str(float(jsdict['products_selling_price'])*float(jsdict['products_discount'])) + """', '""" + jsdict['products_discount'] + """', '""" + jsdict['products_cost_price'] + """', '""" + jsdict['products_inventory_quantity']+ """', '""" + str(Y_or_N)+"""', sysdate, sysdate+14, '""" + jsdict['products_description'] + """', '""" + jsdict['products_url'] + """')""")
                       if Y_or_N == "N":
                           cur.execute("""INSERT INTO products VALUES('""" +str(int(ROW[0])+1)+ """', '""" + jsdict['products_name'] + """', '""" + jsdict['products_selling_price'] + """', '""" + str(float(jsdict['products_selling_price'])*float(jsdict['products_discount'])) + """', '""" + jsdict['products_discount'] + """', '""" + jsdict['products_cost_price'] + """', '""" + jsdict['products_inventory_quantity']+ """', '""" + str(Y_or_N)+"""', sysdate-1, sysdate-1, '""" + jsdict['products_description'] + """', '""" + jsdict['products_url'] + """')""")    
                       conn.commit()

                       # bug fix: # 4. Cannot enter product page for specific new product
                       # new products need a default comment insertion; alternative is try-catch above
                       cur.execute("""SELECT COUNT(*) FROM comments""")
                       ROW2 = cur.fetchone()
                       command = """INSERT INTO comments VALUES ('""" + str(int(ROW2[0])+1) + """', sysdate, 'Add a comment with the + icon', '5', '1', '""" + str(int(ROW[0])+1) + """', 'show')"""
                       cur.execute(command)
                       conn.commit()
                

                ### Cannot just delete, then reinsert - Foreign key of Products ID is connected to Comments table, so integrity errpr
                #  ORA-02292: integrity constraint (DB107.COMMENTS_FK2) violated - child record found
                
    paginated = False
    
    return jsdata




##############################################################################

########################################### HELPER FUNCTIONS ######################################################################


def parse(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(7):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans

def CreateNewOrders_ID(size, chars=string.ascii_uppercase+ string.digits):
	return ''.join(random.choice(chars) for x in range(size))

# This function deals with empty filter boxes and helps automate the check of whether a filter box is empty or not
def filter_NoneCheck(filter):
    if filter == None:
        return_val = True
    if filter!= None:
        if filter=="":
            return_val = True
        if filter != "":
            return_val = False
    else:
        return True
    return return_val



########################################### RUN SITE ######################################################################
if __name__ == '__main__':
    app.run(debug=True)