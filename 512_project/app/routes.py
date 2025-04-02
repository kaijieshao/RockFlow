from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pickle
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import cvxopt as opt
from cvxopt import solvers
import os
from datetime import datetime, timedelta
import yfinance as yf
import statsmodels.api as sm # This package is needed for the scatter plot of plotly.express
from .portfolio_functions import get_asset_allocation, calc_starting_positions, update_output_Charts
from .portfolio_functions import portfolio_vs_sp500_model
from .default_strategy_implementation import default_strategy_implement
from .stock_info import get_stock_data
from .database_helper import get_user_balance, update_user_balance, record_action, record_stock_purchase, get_user_by_username, get_user_stocks, add_subscription, check_subscription, get_all_assets
from .database_helper import admin_view_users, admin_view_subscribed_users, admin_view_transactions, get_user_by_id, update_user_password, admin_delete_user, admin_stock_record_buy, admin_stock_record_sell
from .stock_info import get_latest_close_price

bp = Blueprint('main', __name__)
investors = pd.read_csv('data/InputData.csv', index_col=0)
assets = pd.read_csv('data/SP500Data.csv', index_col=0)
missing_fractions = assets.isnull().mean().sort_values(ascending=False)
drop_list = sorted(list(missing_fractions[missing_fractions > 0.3].index))
assets.drop(labels=drop_list, axis=1, inplace=True)
# Fill the missing values with the last value available in the dataset.
assets=assets.ffill()
dates = (assets.index.to_series()).apply(lambda x: pd.to_datetime(x))
assets.rename(index=lambda x: pd.to_datetime(x), inplace=True)

# Load the pre-trained model (replace with your actual model path)
with open('model/finalized_model.sav', 'rb') as model_file:
    model = pickle.load(model_file)

# Define the prediction function
def predict_risk(age, inccl, edu, married, kids, occ, risk):
    # Prepare the feature vector for prediction
    features = np.array([[age, inccl, edu, married, kids, occ, risk]])
    
    # Make a prediction using the model
    prediction = model.predict(features)
    
    return prediction[0]

# Route for ML prediction page
@bp.route('/prediction', methods=['GET', 'POST'])
def index():
    if 'username' not in session:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('auth.login'))

    prediction = None
    if request.method == 'POST':
        # Retrieve form data
        try:
            age = int(request.form['age'])
            inccl = int(request.form['inccl'])
            edu = int(request.form['edu'])
            married = int(request.form['married'])
            kids = int(request.form['kids'])
            occ = int(request.form['occ'])
            risk = int(request.form['risk'])
            
            # Get the prediction from the model
            prediction = predict_risk(age, inccl, edu, married, kids, occ, risk)
        except ValueError:
            prediction = "Invalid input. Please enter valid values."

    return render_template('index.html', prediction=prediction)

# Route for logout
@bp.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session to log the user out
    return redirect(url_for('auth.login'))  # Redirect to login page

# Route for portfolio selection
@bp.route('/portfolio_selection', methods=['GET', 'POST'])
def portfolio_selection():
    # Load the CSV file to get the column names for the dropdown
    columns = assets.columns.tolist()[1:]

    default_columns = ['GOOGL', 'FB', 'GS', 'MS', 'GE', 'MSFT']

    if request.method == 'POST':
        # Get the values from the form
        amount_to_invest = float(request.form['amount_to_invest'])
        risk_level = float(request.form['risk_level'])
        
        # Get the selected columns as a list
        selected_columns = request.form.getlist('selected_columns')  # This returns a list of selected columns
        
        selected_date = request.form['selected_date']  # Get the date input
        print(selected_columns)

        # Call get_asset_allocation to get the two dataframes
        Alloc, returns_sum_pd = get_asset_allocation(risk_level, selected_columns)
        print(Alloc)
        
        # Call calc_starting_positions to calculate how many share to buy for each asset
        starting_position = calc_starting_positions(amount_to_invest, risk_level, selected_columns, selected_date)
        
        result_df = starting_position

        # Call function B to get the two plots and a dataframe
        plot1, plot2 = update_output_Charts(risk_level, selected_columns, starting_position, selected_date)

        # Convert plots to HTML so they can be displayed in the template
        plot1_html = plot1.to_html(full_html=False)
        plot2_html = plot2.to_html(full_html=False)

        # Render the portfolio selection page with the plots
        return render_template('portfolio_selection.html', plot1_html=plot1_html, plot2_html=plot2_html, result_df=result_df.to_html(), columns=columns, default_columns=default_columns)

    return render_template('portfolio_selection.html', columns=columns, default_columns=default_columns)

# New route for Portfolio vs SP500 page
@bp.route('/Portfolio_VS_SP500', methods=['GET', 'POST'])
def portfolio_vs_sp500():
    columns = assets.columns.tolist()[1:]

    default_columns = ['GOOGL', 'FB', 'GS', 'MS', 'GE', 'MSFT']
    plot1_html = None
    float_output1 = None
    float_output2 = None
    
    if request.method == 'POST':
        # Retrieve form data
        risk_level = float(request.form['risk_level'])
        selected_columns = request.form.getlist('selected_columns')
        
        # Get the three outputs from the portfolio_vs_sp500 function
        plot1, float_output1, float_output2 = portfolio_vs_sp500_model(risk_level, selected_columns)
        plot1_html = plot1.to_html(full_html=False)

    # Render the portfolio_vs_sp500 page with the three outputs
    return render_template('portfolio_vs_sp500.html', plot1_html=plot1_html, float_output1=float_output1, float_output2=float_output2, columns=columns, default_columns=default_columns)

@bp.route('/default_strategy', methods=['GET', 'POST'])
def default_strategy():
    plot1_html = None
    plot2_html = None
    stock_symbol = None
    
    if request.method == 'POST':
        try:
            stock_symbol = request.form['stock_symbol']
            plot1, plot2 = default_strategy_implement(stock_symbol)  # Call the function to get the plots
            plot1_html = plot1.to_html(full_html=False)
            plot2_html = plot2.to_html(full_html=False)
        except Exception:
            plot1_html, plot2_html = None, None
    

    return render_template('default_strategy_implementation.html', plot1_html=plot1_html, plot2_html=plot2_html, stock_symbol=stock_symbol)

# New route for individual stock analysis
@bp.route('/individual_stock_analysis', methods=['GET', 'POST'])
def individual_stock_analysis():
    stock_data = None
    plot_html = None
    
    if request.method == 'POST':
        stock_symbol = request.form['symbol']
        stock_data, plot = get_stock_data(stock_symbol)
        plot_html = plot.to_html(full_html=False)
        
        if stock_data is None:
            return render_template('individual_stock_analysis.html', stock_data=None, plot_url=None)
    
    return render_template('individual_stock_analysis.html', stock_data=stock_data, plot_url=plot_html)

@bp.route('/personal_center', methods=['GET', 'POST'])
def personal_center():
    if 'username' not in session:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('auth.login'))  # Redirect to login page if not logged in

    user_id = get_user_by_username(session['username'])[0]  # Assuming user ID is the first column in the users table
    balance = np.round(get_user_balance(user_id), 2)
    # Check subscription status
    subscription_status = check_subscription(user_id)

    if not subscription_status:
        # If not subscribed, show the message instead of full features
        return render_template('personal_center.html', balance=balance, subscription_status=False)

    # If the user is subscribed, show the full personal center

    if request.method == 'POST':
        if 'deposit' in request.form:
            # Handle deposit
            amount_to_deposit = float(request.form['deposit_amount'])
            credit_card_number = request.form['credit_card_number']
            cardholder_name = request.form['cardholder_name']
            safety_code = request.form['safety_code']
            
            # Update balance and record action
            new_balance = balance + amount_to_deposit
            update_user_balance(user_id, new_balance)
            record_action(user_id, 1, amount_to_deposit)  # Action 1 for deposit
            flash(f"Deposit successful! New balance: {new_balance}", 'success')

        elif 'buy_stock' in request.form:
            # Handle stock purchase
            stock_symbol = request.form['stock_symbol']
            num_of_shares = int(request.form['num_of_shares'])
            
            # Assume get_stock_data is a function that gets the price of a stock
            stock_price = float(get_latest_close_price(stock_symbol, 'ALPHA_VANTAGE_API_KEY'))
            total_cost = stock_price * num_of_shares

            if balance >= total_cost:
                new_balance = balance - total_cost
                update_user_balance(user_id, new_balance)
                record_action(user_id, -1, total_cost)  # Action -1 for stock purchase
                record_stock_purchase(user_id, stock_symbol, num_of_shares)
                flash(f"Stock purchase successful! New balance: {new_balance}", 'success')
            else:
                flash("Insufficient balance, please deposit before buying the stock.", 'danger')
                
        # Handle Sell Asset
        elif 'sell_asset' in request.form:
            stock_symbol = request.form['sell_stock_symbol']
            num_of_shares = int(request.form['sell_num_of_shares'])
            
            # Check if user has enough shares
            user_stocks = get_user_stocks(user_id, stock_symbol)
            if user_stocks and user_stocks[0][1] >= num_of_shares:
                # Update stocks table with negative number of shares
                record_stock_purchase(user_id, stock_symbol, -1 * num_of_shares)
                
                # Update user's balance based on current market value of the stock
                stock_price = float(get_latest_close_price(stock_symbol, 'ALPHA_VANTAGE_API_KEY'))
                total_revenue = stock_price * num_of_shares
                balance = get_user_balance(user_id)
                new_balance = balance + total_revenue
                update_user_balance(user_id, new_balance)

                # Record the sell action
                record_action(user_id, action=1, amount=total_revenue)
                
            else:
                flash("Insufficient asset to sell.", "danger")

        return redirect(url_for('main.personal_center'))  # Refresh the page after action

    return render_template('personal_center.html', balance=balance, subscription_status=True)

@bp.route('/subscription', methods=['GET', 'POST'])
def subscription():
    user_id = get_user_by_username(session['username'])[0]

    # Check if user is already subscribed
    subscription_status = check_subscription(user_id)

    if request.method == 'POST':
        # Process subscription form
        card_number = request.form['card_number']
        name = request.form['name']
        safety_code = request.form['safety_code']
        
        # Insert the user into the subscription table
        add_subscription(user_id, card_number, name, safety_code)

        flash("Subscription successful! All features are now unlocked.", "success")
        return redirect(url_for('main.personal_center'))

    # Render subscription page with subscription status
    return render_template('subscription.html', subscription_status=subscription_status)

# New route for checking user assets
@bp.route('/my_assets', methods=['GET'])
def my_assets():
    if 'username' not in session:
        # If the user is not logged in, redirect to the login page
        return redirect(url_for('auth.login'))

    user_id = get_user_by_username(session['username'])[0]  # Assuming user ID is the first column in the users table
    
    # Query the database for user assets where num_of_shares > 0
    user_stocks = get_all_assets(user_id)
    if not user_stocks:
        flash("You have no assets in your portfolio.", "info")
        
    return render_template('my_assets.html', user_stocks=user_stocks)

@bp.route('/admin/dashboard')
def admin_dashboard():
    if 'administrator_userid' not in session:
        return redirect(url_for('auth.administrator_login'))  # Redirect to admin login if not logged in

    return render_template('admin_dashboard.html')  # Admin dashboard page

@bp.route('/view_users')
def view_users():
    users = admin_view_users()
    return render_template('view_users.html', users=users)

@bp.route('/view_subscribed_users')
def view_subscribed_users():
    users = admin_view_subscribed_users()
    return render_template('view_subscribed_users.html', users=users)

@bp.route('/view_transactions')
def view_transactions():
    transactions = admin_view_transactions()
    return render_template('view_transactions.html', transactions=transactions)

@bp.route('/change_user_password', methods=['GET', 'POST'])
def change_user_password():
    if request.method == 'POST':
        user_id = request.form['user_id']
        new_password = request.form['new_password']

        # Check if user exists
        user = get_user_by_id(user_id)
        if user:
            # Update the password in the database
            update_user_password(user_id, new_password)
            flash("User password has been updated.", 'success')
            return redirect(url_for('main.change_user_password'))
        else:
            flash("User ID does not exist.", 'danger')
    
    return render_template('change_user_password.html')

@bp.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    if request.method == 'POST':
        user_id = request.form['user_id']

        # Check if user exists
        user = get_user_by_id(user_id)
        if user:
            # Update the password in the database
            admin_delete_user(user_id)
            flash("User has been deleted.", 'success')
            return redirect(url_for('main.delete_user'))
        else:
            flash("User ID does not exist.", 'danger')
            
    return render_template('delete_user.html')

@bp.route('/stock_record_analysis', methods=['GET', 'POST'])
def stock_record_analysis():
    stock_buy_agg = admin_stock_record_buy()
    stock_sell_agg = admin_stock_record_sell()
    return render_template('stock_record_analysis.html', stock_buy = stock_buy_agg, stock_sell = stock_sell_agg)
