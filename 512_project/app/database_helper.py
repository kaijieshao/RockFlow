import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'instance/users.db'

def create_user_table():
    """ Create the users table if it doesn't already exist """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def register_user(username, password):
    """ Register a new user with a hashed password and balance of 0 """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # hashed_password = generate_password_hash(password)
    hashed_password = password
    cursor.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, hashed_password, 0))
    
    conn.commit()
    conn.close()

def get_user_by_username(username):
    """ Retrieve user by username """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def check_password(user, password):
    """ Check if the provided password matches the stored hashed password """
    return password == user[2]
    # return check_password_hash(user[2], password)

def create_action_table():
    """ Create the action table to track deposits and stock purchases """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            action INTEGER,
            amount REAL,
            date_time TEXT,
            FOREIGN KEY (userid) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def create_stock_table():
    """ Create the stock table to track stock purchases """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            stock_symbol TEXT,
            num_of_shares INTEGER,
            date_time TEXT,
            FOREIGN KEY (userid) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

def get_user_balance(userid):
    """ Get the disposable money (balance) of the user """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (userid,))
    balance = cursor.fetchone()
    conn.close()
    return balance[0] if balance else None

def update_user_balance(userid, new_balance):
    """ Update the user's disposable money after deposit or stock purchase """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, userid))
    conn.commit()
    conn.close()

def record_action(userid, action, amount):
    """ Record a deposit or stock purchase action in the actions table """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO actions (userid, action, amount, date_time)
        VALUES (?, ?, ?, ?)
    """, (userid, action, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def record_stock_purchase(userid, stock_symbol, num_of_shares):
    """ Record a stock purchase in the stocks table """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stocks (userid, stock_symbol, num_of_shares, date_time)
        VALUES (?, ?, ?, ?)
    """, (userid, stock_symbol, num_of_shares, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# Get the stock that the client possesses
def get_user_stocks(userid, stock_symbol):
    """ Retrieve the user's stock holdings by stock symbol """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT userid, sum(num_of_shares) FROM stocks WHERE userid = ? AND stock_symbol = ?", (userid, stock_symbol))
    stocks = cursor.fetchall()
    conn.close()
    return stocks

def create_subscription_table():
    """ Create the subscription table if it doesn't already exist """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            card_number TEXT,
            cardholder_name TEXT,
            safety_code TEXT,
            subscription_date TEXT,
            FOREIGN KEY (userid) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

# Add a user as vip to the table subscriptions
def add_subscription(userid, card_number, cardholder_name, safety_code):
    """ Add a new subscription record """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subscriptions (userid, card_number, cardholder_name, safety_code, subscription_date)
        VALUES (?, ?, ?, ?, ?)
    """, (userid, card_number, cardholder_name, safety_code, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
# Verify whether a user already subscribed
def check_subscription(userid):
    """ Check if the user is already subscribed """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscriptions WHERE userid = ?", (userid,))
    subscription = cursor.fetchone()
    conn.close()
    return subscription

# Get all assets the client current have
def get_all_assets(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT userid, stock_symbol, SUM(num_of_shares) AS total_shares
        FROM stocks
        WHERE userid = ?
        GROUP BY userid, stock_symbol
        HAVING total_shares > 0
        ORDER BY total_shares DESC
    """, (user_id,))
    user_stocks = cursor.fetchall()
    conn.close()
    return user_stocks

# Create the administrators table if it doesn't already exist
def create_administrators_table():
    """ Create the administrators table if it doesn't already exist """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administrators (
            administrator_id INTEGER PRIMARY KEY AUTOINCREMENT,
            administrator_userid TEXT NOT NULL UNIQUE,
            administrator_password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    
def register_administrator(administrator_userid, administrator_password):
    """ Register a new administrator with a hashed password """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    hashed_password = generate_password_hash(administrator_password)
    cursor.execute("INSERT INTO administrators (administrator_userid, administrator_password) VALUES (?, ?)",
                   (administrator_userid, hashed_password))

    conn.commit()
    conn.close()
    
def get_administrator_by_userid(administrator_userid):
    """ Retrieve administrator by administrator_userid """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM administrators WHERE administrator_userid = ?", (administrator_userid,))
    administrator = cursor.fetchone()
    conn.close()
    return administrator

def check_administrator_password(administrator, administrator_password):
    """ Check if the provided password matches the stored hashed password for admin """
    return check_password_hash(administrator[2], administrator_password)

def admin_view_users():
     # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query all users from the 'users' table
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()  # Fetch all records

    # Close the database connection
    conn.close()
    
    return users

def admin_view_subscribed_users():
    # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query all records from the table subscriptions
    cursor.execute('SELECT * FROM subscriptions')
    users = cursor.fetchall()  # Fetch all records

    # Close the database connection
    conn.close()
    
    return users

def admin_view_transactions():
     # Connect to the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query all users from the 'users' table
    cursor.execute('SELECT * FROM stocks')
    transactions = cursor.fetchall()  # Fetch all records

    # Close the database connection
    conn.close()
    
    return transactions

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_password(user_id, new_password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE id=?", (new_password, user_id))
    conn.commit()
    conn.close()
    
def admin_delete_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id))
    cursor.execute("DELETE FROM stocks WHERE userid=?", (user_id))
    cursor.execute("DELETE FROM actions WHERE userid=?", (user_id))
    cursor.execute("DELETE FROM subscriptions WHERE userid=?", (user_id))
    conn.commit()
    conn.close()
    
def admin_stock_record_buy():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT stock_symbol, SUM(num_of_shares) as num_purchased
                   FROM stocks 
                   WHERE num_of_shares > 0 
                   GROUP BY stock_symbol 
                   ORDER BY num_purchased DESC"""
                   )
    records = cursor.fetchall()
    conn.close()
    return records

def admin_stock_record_sell():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""SELECT stock_symbol, -1 * SUM(num_of_shares) as num_sold
                   FROM stocks 
                   WHERE num_of_shares < 0 
                   GROUP BY stock_symbol 
                   ORDER BY num_sold DESC"""
                   )
    records = cursor.fetchall()
    conn.close()
    return records
