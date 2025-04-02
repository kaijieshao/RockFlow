from app.database_helper import create_user_table, create_action_table, create_stock_table, create_subscription_table, create_administrators_table

# Initialize the database by creating the users table
create_user_table()
create_action_table()
create_stock_table()
create_subscription_table()
create_administrators_table()


print("Database initialized.")
