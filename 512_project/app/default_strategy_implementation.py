import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime
import plotly.express as px

def default_strategy_implement(stock_symbol):
    ticker = stock_symbol 

    # Define the time period you want to fetch the data for
    start_date = '2024-03-01'
    end_date = '2025-03-01'

    # Download the stock data with an hourly interval
    data_hourly = yf.download(ticker, start=start_date, end=end_date, interval='1h')
    data_daily = yf.download(ticker, start=start_date, end=end_date, interval='1d')
    
    data_hourly.columns = data_hourly.columns.map(lambda x: x[0].lower())
    data_daily.columns = data_daily.columns.map(lambda x: x[0].lower())
    
    data_hourly['timestamp'] = data_hourly.index
    data_daily['timestamp'] = data_daily.index
    
    data_hourly.reset_index(drop = True, inplace = True)
    data_daily.reset_index(drop = True, inplace = True)
    
    def calc_trd_prd(dt):
        return [
            ts.isocalendar()[0] + ts.isocalendar()[1]/100 for ts in dt
        ]
    data_hourly['trd_prd'] = calc_trd_prd(
        data_hourly['timestamp']
    )
    data_daily['trd_prd'] = calc_trd_prd(
        data_daily['timestamp']
    )

    vol_calcs = pd.DataFrame(
        data={"obs_vol": None},
        index=data_daily['trd_prd'].unique()
    )

    def calc_vol(trd_prd):
        return np.std(
            np.log(
                np.array(
                    data_hourly[
                    data_hourly['trd_prd'] == trd_prd
                    ]['close'][1:]
                ) / np.array(
                    data_hourly[
                    data_hourly['trd_prd'] == trd_prd
                    ]['close'][:-1]
                )
            )
        )*np.sqrt(32.5)

    for trd_prd in vol_calcs.index:
        vol_calcs.loc[trd_prd, 'obs_vol'] = calc_vol(trd_prd)

    vol_calcs['exp_vol'] = vol_calcs['obs_vol'].shift(1)
    
    blotter = pd.DataFrame(
        data={
            'entry_timestamp': None,
            'qty': 0,
            'exit_timestamp': None,
            'entry_price': None,
            'exit_price': None,
            'success': pd.NA
        },
        index=data_daily['trd_prd'].unique()[1:]
    )

    ledger = pd.DataFrame({
        'date': data_daily.loc[
            data_daily['trd_prd'] != data_daily[
                'trd_prd'].iloc[0],
            'timestamp'
        ],
        'position': 0,
        'cash': 0.0,
        'mark': data_daily.loc[
            data_daily['trd_prd'] != data_daily[
                'trd_prd'].iloc[0],
            'close'
        ],
        'mkt_value': 0
    })

    for trd_prd in blotter.index:
        entry_timestamp = data_hourly.loc[
            data_hourly['trd_prd'] == trd_prd,
            'timestamp'
        ].min()
        entry_price = data_daily[
            data_daily['trd_prd'] == trd_prd
            ].iloc[0]['open']
        if data_daily.iloc[
            data_daily.loc[
                data_daily['trd_prd'] < trd_prd
            ]['timestamp'].idxmax()
        ]['close'] >= entry_price:
            qty = 100
            exit_param = 'high'
            exit_price_strategy = entry_price*(1+vol_calcs.loc[trd_prd, 'exp_vol'])
            exit_timestamp = data_hourly.loc[
                (data_hourly['trd_prd'] == trd_prd) & (
                        data_hourly[exit_param] >= exit_price_strategy
                ),
                'timestamp'
            ]

        else:
            qty = -100
            exit_param = 'low'
            exit_price_strategy = entry_price*(1-vol_calcs.loc[trd_prd, 'exp_vol'])
            exit_timestamp = data_hourly.loc[
                (data_hourly['trd_prd'] == trd_prd) & (
                        data_hourly[exit_param] <= exit_price_strategy
                ),
                'timestamp'
            ]

        if len(exit_timestamp) == 0:
            last_ts_row_this_week = ""
            if len(last_ts_row_this_week) > 0:
                last_ts_this_week = datetime.combine(
                    last_ts_row_this_week.index[0],
                    last_ts_row_this_week['end_time'].iloc[0]
                )
            else:
                last_ts_this_week = data_hourly['timestamp'].min()

            if data_hourly['timestamp'].max() < last_ts_this_week:
                # Then the exit order hasn't filled yet, but there is still time
                exit_price = None
                success = pd.NA
                exit_timestamp = None
            else:
                # Then we had to close at market price on the last trading day
                #   of the period
                exit_timestamp = data_hourly.loc[
                    data_hourly['trd_prd'] == trd_prd,
                    'timestamp'
                ].max()
                exit_price = data_daily.loc[
                    data_daily['trd_prd'] == trd_prd, 'close'].iloc[-1]
                success = False
        else:    
            exit_price = exit_price_strategy
            success = True
            exit_timestamp = exit_timestamp.iloc[0]

        blotter.loc[trd_prd, 'entry_timestamp'] = entry_timestamp
        blotter.loc[trd_prd, 'qty'] = qty
        blotter.loc[trd_prd, 'exit_timestamp'] = exit_timestamp
        blotter.loc[trd_prd, 'entry_price'] = entry_price
        blotter.loc[trd_prd, 'exit_price'] = exit_price
        blotter.loc[trd_prd, 'success'] = success

        ledger_idx_entry = ledger.index[ledger['date'].apply(lambda x: x.date()) >= entry_timestamp.date()]
        ledger.loc[
            ledger_idx_entry, 'position'
        ] = ledger.loc[ledger_idx_entry, 'position'] + qty
        ledger.loc[
            ledger_idx_entry, 'cash'
        ] = round(ledger.loc[ledger_idx_entry, 'cash'] - qty*entry_price, 2)

        if exit_timestamp is not None:
            ledger_idx_exit = ledger.index[ledger['date'].apply(lambda x: x.date()) >= exit_timestamp.date()]
            ledger.loc[
                ledger_idx_exit, 'position'
            ] = ledger.loc[ledger_idx_exit, 'position'] - qty
            ledger.loc[
                ledger_idx_exit, 'cash'
            ] = round(ledger.loc[ledger_idx_exit, 'cash'] + qty*exit_price, 2)



    ledger['mkt_value'] = round(
            ledger['position'] * ledger['mark'] + ledger['cash'], 2
    )

    nav_fig = px.bar(
        ledger,
        x='date',
        y='mkt_value',
        color='position',
        title='End-of-Day Strategy Market Value: '
    ).update_layout(
        yaxis=dict(
            tickfont=dict(size=12),
            showgrid=False,
            title=dict(text="Market Value"),
            # titlefont=dict(size=15)
        ),
        xaxis=dict(
            tickfont=dict(size=12),
            title=dict(text="Date"),
            # titlefont=dict(size=15),
        ),
        yaxis_tickprefix='$',
        plot_bgcolor='gray'
    )

    ticker = '^GSPC'

    # Define the time period for which you want to fetch the data
    start_date = '2024-03-01'
    end_date = '2025-03-01'

    # Download the hourly data for the S&P 500 index
    data_sp500 = yf.download(ticker, start=start_date, end=end_date, interval='1h')
    data_sp500.columns = data_sp500.columns.map(lambda x: x[0].lower())
    data_sp500['timestamp'] = data_sp500.index
    data_sp500.reset_index(drop = True, inplace = True)

    def calc_rtns(row, bench):
        row['trade_rtn'] = np.log(
            row['exit_price']/row['entry_price']
        ) * np.sign(row['qty'])
        row['bench_rtn'] = np.log(
            bench.loc[
                bench['timestamp'] == row['exit_timestamp'],
                'open'
            ].values[0] / bench.loc[
                bench['timestamp'] == row['entry_timestamp'],
                'open'
            ].values[0]
        )
        return row

    ab_self_data = blotter.apply(
        calc_rtns, args=(data_hourly,), axis=1
    )[['trade_rtn', 'bench_rtn', 'qty']]

    ab_self_fig = px.scatter(
        ab_self_data*100,
        x='bench_rtn',
        y='trade_rtn',
        color='qty',
        trendline='ols',
        title='Strategy Realized Returns Sensitivity wrt the Underlying:'
    )

    longs_fig = px.scatter(
        ab_self_data[ab_self_data['qty'] >= 0]*100,
        x='bench_rtn',
        y='trade_rtn',
        trendline='ols',
        trendline_color_override="yellow"
    )
    shorts_fig = px.scatter(
        ab_self_data[ab_self_data['qty'] < 0]*100,
        x='bench_rtn',
        y='trade_rtn',
        trendline='ols',
        trendline_color_override="blue"
    )

    ab_self_fig.add_trace(longs_fig.data[1])
    ab_self_fig.add_trace(shorts_fig.data[1])

    longs_ab=px.get_trendline_results(longs_fig).iloc[0]["px_fit_results"].params
    shorts_ab=px.get_trendline_results(shorts_fig).iloc[0]["px_fit_results"].params
    overall=px.get_trendline_results(ab_self_fig).iloc[0]["px_fit_results"].params

    ab_self_fig = ab_self_fig.add_annotation(
        text="<b>Longs</b>: alpha=" + str(round(longs_ab[0], 3)) +
            "%; beta=" + str(round(longs_ab[1], 3)),
        xref="paper",
        yref="paper",
        x=0.90,
        y=1.17,
        showarrow=False,
        font=dict(size=15, color='yellow')
    ).add_annotation(
        text="<b>Shorts</b>: alpha=" + str(round(shorts_ab[0], 3)) +
            "%; beta=" + str(round(shorts_ab[1], 3)),
        xref="paper",
        yref="paper",
        x=0.91,
        y=1.10,
        showarrow=False,
        font=dict(size=15, color='blue')
    ).add_annotation(
        text="<b>Overall</b>: alpha=" + str(round(overall[0], 3)) +
            "%; beta=" + str(round(overall[1], 3)),
        xref="paper",
        yref="paper",
        x=0.05,
        y=1.17,
        showarrow=False,
        font=dict(size=15, color='orange')
    ).update_layout(
        yaxis=dict(
            tickfont = dict(size=12),
            tickformat = ".3s",
            showgrid=False,
            title=dict(text="Strategy Return per trading period"),
            # titlefont=dict(size=15)
        ),
        xaxis=dict(
            tickfont = dict(size=12),
            tickformat = ".3s",
            showgrid=False,
            title=dict(text="Underlying Asset Return, Same Timestamps"),
            # titlefont=dict(size=15),
        ),
        yaxis_ticksuffix = '%',
        xaxis_ticksuffix = '%',
        plot_bgcolor='gray'
    ).update_traces(
        marker=dict(size=10)
    )

    ab_benchmark_data = blotter.apply(
        calc_rtns, args=(data_hourly,), axis=1
    )[['trade_rtn', 'bench_rtn', 'qty']]


    ab_benchmark_fig = px.scatter(
        ab_benchmark_data*100,
        x='bench_rtn',
        y='trade_rtn',
        color='qty',
        trendline='ols',
        title='Strategy Realized Returns Sensitivity wrt the S&P 500:'
    )

    longs_fig = px.scatter(
        ab_benchmark_data[ab_benchmark_data['qty'] >= 0]*100,
        x='bench_rtn',
        y='trade_rtn',
        trendline='ols',
        trendline_color_override="yellow"
    )
    shorts_fig = px.scatter(
        ab_benchmark_data[ab_benchmark_data['qty'] < 0]*100,
        x='bench_rtn',
        y='trade_rtn',
        trendline='ols',
        trendline_color_override="blue"
    )

    ab_benchmark_fig.add_trace(longs_fig.data[1])
    ab_benchmark_fig.add_trace(shorts_fig.data[1])

    longs_ab=px.get_trendline_results(longs_fig).iloc[0]["px_fit_results"].params
    shorts_ab=px.get_trendline_results(shorts_fig).iloc[0]["px_fit_results"].params
    overall=px.get_trendline_results(ab_benchmark_fig).iloc[0]["px_fit_results"].params

    ab_benchmark_fig = ab_benchmark_fig.add_annotation(
        text="<b>Longs</b>: alpha=" + str(round(longs_ab[0], 3)) +
            "%; beta=" + str(round(longs_ab[1], 3)) + "\n", 
        xref="paper",
        yref="paper",
        x=0.90,
        y=1.17,
        showarrow=False,
        font=dict(size=15, color='yellow')
    ).add_annotation(
        text="<b>Shorts</b>: alpha=" + str(round(shorts_ab[0], 3)) +
            "%; beta=" + str(round(shorts_ab[1], 3)) + "\n",
        xref="paper",
        yref="paper",
        x=0.91,
        y=1.10,
        showarrow=False,
        font=dict(size=15, color='blue')
    ).add_annotation(
        text="<b>Overall</b>: alpha=" + str(round(overall[0], 3)) +
            "%; beta=" + str(round(overall[1], 3)) + "\n",
        xref="paper",
        yref="paper",
        x=0.05,
        y=1.17,
        showarrow=False,
        font=dict(size=15, color='orange')
    ).update_layout(
        yaxis=dict(
            tickfont = dict(size=12),
            tickformat = ".3s",
            showgrid=False,
            title=dict(text="Strategy Return per trading period"),
            # titlefont=dict(size=15)
        ),
        xaxis=dict(
            tickfont = dict(size=12),
            tickformat = ".3s",
            showgrid=False,
            title=dict(text="Underlying Asset Return, Same Timestamps"),
            # titlefont=dict(size=15),
        ),
        yaxis_ticksuffix = '%',
        xaxis_ticksuffix = '%',
        plot_bgcolor='gray'
    ).update_traces(
        marker=dict(size=10)
    )
    
    return nav_fig, ab_benchmark_fig
