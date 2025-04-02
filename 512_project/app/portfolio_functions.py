import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
import cvxopt as opt
from cvxopt import solvers
import os
from datetime import datetime, timedelta
import yfinance as yf
import statsmodels.api as sm

def get_asset_allocation(riskTolerance, stock_ticker):
    assets = pd.read_csv('data/SP500Data.csv', index_col=0)
    missing_fractions = assets.isnull().mean().sort_values(ascending=False)
    drop_list = sorted(list(missing_fractions[missing_fractions > 0.3].index))
    assets.drop(labels=drop_list, axis=1, inplace=True)
    # Fill the missing values with the last value available in the dataset.
    assets=assets.ffill()
    dates = (assets.index.to_series()).apply(lambda x: pd.to_datetime(x))
    assets.rename(index=lambda x: pd.to_datetime(x), inplace=True)

    assets_selected = assets.loc[:, stock_ticker]
    return_vec = np.array(assets_selected.pct_change().dropna(axis=0)).T
    n = len(return_vec)
    mus = 1 - riskTolerance

    # Convert to cvxopt matrices
    S = opt.matrix(np.cov(return_vec))
    pbar = opt.matrix(np.mean(return_vec, axis=1))

    # Create constraint matrices
    G = -opt.matrix(np.eye(n))  # negative n x n identity matrix
    h = opt.matrix(0.0, (n, 1))
    A = opt.matrix(1.0, (1, n))
    b = opt.matrix(1.0)

    # Calculate efficient frontier weights using quadratic programming
    portfolios = solvers.qp(mus * S, -pbar, G, h, A, b)
    w = portfolios['x'].T
    Alloc = pd.DataFrame(
        data=np.array(portfolios['x']),
        index=assets_selected.columns
    )

    # Calculate efficient frontier weights using quadratic programming
    returns_final = (np.array(assets_selected) * np.array(w))
    returns_sum = np.sum(returns_final, axis=1)
    returns_sum_pd = pd.DataFrame(returns_sum, index=assets.index)
    returns_sum_pd = returns_sum_pd - returns_sum_pd.iloc[0, :] + 100
    return Alloc, returns_sum_pd

def update_asset_allocationChart(risk_tolerance, stock_ticker):

    Allocated, InvestmentReturn = get_asset_allocation(risk_tolerance,
                                                       stock_ticker)

    return [{'data': [go.Bar(
        x=Allocated.index,
        y=Allocated.iloc[:, 0],
        marker=dict(color='red'),
    ),
    ],
        'layout': {'title': " Asset allocation - Mean-Variance Allocation"}

    },
        {'data': [go.Scatter(
            x=InvestmentReturn.index,
            y=InvestmentReturn.iloc[:, 0],
            name='OEE (%)',
            marker=dict(color='red'),
        ),
        ],
            'layout': {'title': "Portfolio value of $100 investment"}

        }]
    

def calc_starting_positions(amount_to_invest, risk_tolerance, stock_ticker, start_date):
    assets = pd.read_csv('data/SP500Data.csv', index_col=0)
    missing_fractions = assets.isnull().mean().sort_values(ascending=False)
    drop_list = sorted(list(missing_fractions[missing_fractions > 0.3].index))
    assets.drop(labels=drop_list, axis=1, inplace=True)
    # Fill the missing values with the last value available in the dataset.
    assets=assets.ffill()
    dates = (assets.index.to_series()).apply(lambda x: pd.to_datetime(x))
    assets.rename(index=lambda x: pd.to_datetime(x), inplace=True)
    
    alloc_dta = update_asset_allocationChart(risk_tolerance, stock_ticker)[0]
    
    cash_position = np.array(alloc_dta['data'][0]['y']) * amount_to_invest
    prices = np.array(assets.loc[start_date, alloc_dta['data'][0]['x']])
    shares = [round(x) for x in cash_position / prices]
    return pd.DataFrame({
        'Asset': alloc_dta['data'][0]['x'],
        'position': shares
    })

def update_output_Charts(risk_tolerance, stock_ticker, starting_position, start_date):
    assets = pd.read_csv('data/SP500Data.csv', index_col=0)
    missing_fractions = assets.isnull().mean().sort_values(ascending=False)
    drop_list = sorted(list(missing_fractions[missing_fractions > 0.3].index))
    assets.drop(labels=drop_list, axis=1, inplace=True)
    # Fill the missing values with the last value available in the dataset.
    assets=assets.ffill()
    dates = (assets.index.to_series()).apply(lambda x: pd.to_datetime(x))
    assets.rename(index=lambda x: pd.to_datetime(x), inplace=True)
    
    Allocated, InvestmentReturn = get_asset_allocation(risk_tolerance,
                                                       stock_ticker)
    starting_position = pd.DataFrame.from_dict(starting_position)
    starting_position['prices'] = assets.loc[start_date, starting_position['Asset'].values].values
    starting_position['value'] = starting_position['prices'] * starting_position['position']
    fig1 = px.pie(
            starting_position,
            values='value',
            names='Asset',
            title = 'Portfolio weights as of ' + str(start_date)
    )
    fig2 = px.scatter(
            x=InvestmentReturn.index,
            y=InvestmentReturn.iloc[:, 0],
    )

    return fig2, fig1

def portfolio_vs_sp500_model(risk_tolerance, stock_ticker):
    try:
        assets = pd.read_csv('data/SP500Data.csv', index_col=0)
        missing_fractions = assets.isnull().mean().sort_values(ascending=False)
        drop_list = sorted(list(missing_fractions[missing_fractions > 0.3].index))
        assets.drop(labels=drop_list, axis=1, inplace=True)
        # Fill the missing values with the last value available in the dataset.
        assets=assets.ffill()
        dates = (assets.index.to_series()).apply(lambda x: pd.to_datetime(x))
        assets.rename(index=lambda x: pd.to_datetime(x), inplace=True)
        
        Allocated, InvestmentReturn = get_asset_allocation(risk_tolerance,
                                                           stock_ticker)
        # print(InvestmentReturn)
        Investment_LogReturn = [np.log(x/y) for x, y in zip(list(InvestmentReturn.iloc[:, 0])[:-1],
                                                list(InvestmentReturn.iloc[:, 0])[1:])]
        # print(Investment_LogReturn)
        ticker = '^GSPC'
        start_dt, end_dt = min(dates), max(dates) + timedelta(days = 1)
        # Needs to add one day to include the very last date
        sp500_data = yf.download(ticker, start=start_dt, end=end_dt)
        sp500_LogReturn = [np.log(x/y) for x, y in zip(list(sp500_data['Close'].iloc[:, 0])[:-1],
                                                list(sp500_data['Close'].iloc[:, 0])[1:])]
        # print(len(sp500_LogReturn))
        # print(len(Investment_LogReturn))
        fig = px.scatter(x= sp500_LogReturn, y=Investment_LogReturn, trendline="ols")
        fig.update_layout(
            xaxis_title="S&P 500 log return",
            yaxis_title="Portfolio log return",
        )
        Y = Investment_LogReturn
        X = sp500_LogReturn
        X = sm.add_constant(X)
        model = sm.OLS(Y, X)
        alpha = np.round(model.fit().params[0], 5)
        beta = np.round(model.fit().params[1], 5)
        # print(model.fit().params)
    except KeyError:
        fig = px.scatter()
        alpha, beta = 0, 0

    return fig, alpha, beta
