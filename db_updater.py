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

# fake orders data -- FOR DEBUGGING PURPOSES ONLY -- WARNING: initializing shopping cart upon database creation means customer has orders before even adding to cart
c.execute(
        """
    insert into orders values ('1', 1.2, sysdate, 1, sysdate, 'unpaid', '1', '1')    
    """)
    
c.execute(
        """
        insert into orders values ('2', 1.4, sysdate, 9, sysdate, 'completed', '1', '2')            
    """)
    
c.execute(
        """
    insert into orders values ('3', 1.7, sysdate, 9, sysdate, 'completed', '1', '3')    
    """)

c.execute(
        """
    insert into orders values ('4', 1.2, sysdate-1, 1, sysdate-1, 'completed', '1', '1')    
    """)
    
c.execute(
        """
        insert into orders values ('5', 1.4, sysdate-1, 9, sysdate-1, 'completed', '1', '2')            
    """)
    
c.execute(
        """
    insert into orders values ('6', 1.7, sysdate-1, 9, sysdate-1, 'completed', '1', '3')    
    """)

c.execute(
        """
    insert into orders values ('7', 1.2, sysdate-31, 1, sysdate-31, 'completed', '1', '1')    
    """)
    
c.execute(
        """
        insert into orders values ('8', 1.4, sysdate-31, 9, sysdate-31, 'completed', '1', '2')            
    """)
    
c.execute(
        """
    insert into orders values ('9', 1.7, sysdate-31, 9, sysdate-31, 'completed', '1', '3')    
    """)

c.execute(
        """
    insert into orders values ('10', 1.2, sysdate-365, 1, sysdate-365, 'completed', '1', '1')    
    """)
    
c.execute(
        """
        insert into orders values ('11', 1.4, sysdate-365, 9, sysdate-365, 'delivery', '1', '2')            
    """)
    
c.execute(
        """
    insert into orders values ('12', 1.7, sysdate-365, 9, sysdate-365, 'delivery', '1', '3')    
    """)

c.execute(
        """
    insert into orders values ('13', 1.2, sysdate-365, 1, sysdate-365, 'delivery', '1', '1')    
    """)
    
c.execute(
        """
        insert into orders values ('14', 1.4, sysdate-1000, 9, sysdate-1000, 'delivery', '1', '2')            
    """)
    
c.execute(
        """
    insert into orders values ('15', 1.7, sysdate-1000, 9, sysdate-1000, 'delivery', '1', '3')    
    """)


# fake order items

c.execute(
    """
    INSERT into order_items values ('1', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
    """)
c.execute(
    """
    INSERT into order_items values ('2', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
    """)
c.execute(
    """
    INSERT into order_items values ('3', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
    """)
c.execute(
    """
    INSERT into order_items values ('4', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
    """)
c.execute(
    """
    INSERT into order_items values ('5', 1 , 20, 0.5, 0.2, sysdate, 'delivery', 1, 1)
    """)

c.execute("commit")

print("Fake data initialized")