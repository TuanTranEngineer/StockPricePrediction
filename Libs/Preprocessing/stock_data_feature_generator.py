import pandas as pd
import numpy as np

def __addTarget(df):
    df["y"] = df["return"].shift(-1)
    df = df.iloc[:-1]
    return df

def return_features(df):
    df["return"] = df["close"] / df["close"].shift(1)
    df["close_to_open"] = df["close"] / df["open"]
    df["close_to_high"] = df["close"] / df["high"]
    df["close_to_low"] = df["close"] / df["low"]
    return __addTarget(df).iloc[1:]

def macd(df):
    ema_12_day = df["close"].ewm(com=(12-1)/2).mean()
    ema_26_day = df["close"].ewm(com=(26-1)/2).mean()
    df["macd_line"] = ema_12_day - ema_26_day
    df["macd_9_day"] = df["macd_line"].ewm(com=(9-1)/2).mean()
    df["macd_diff"] = df["macd_line"] - df["macd_9_day"]
    return df

def ma(df):
    df["ma_50_day"] = df["close"].rolling(50).mean()
    df["ma_200_day"] = df["close"].rolling(200).mean()
    df["ma_50_200"] = df["ma_50_day"] - df["ma_200_day"]
    return df

def parabolic_sar(df):
    df["sar"] = np.nan
    step = 5
    acc_factor = 0.02
    uptrend = False
    prior_sar = max(df.loc[1:step, "close"])
    extreme_point = min(df.loc[1:step, "close"])
    for i, row in df.iloc[step:].iterrows():
        if uptrend:
            df.at[i, "sar"] = prior_sar + acc_factor*(extreme_point - prior_sar)
            if df.at[i, "low"] < df.at[i, "sar"]:
                # reverse to downtrend
                uptrend = False
                prior_sar = max(df.loc[i-step:i, "close"])
                extreme_point = min(df.loc[i-step:i, "close"])
            else:
                # continue uptrend
                if df.at[i, "close"] > extreme_point:
                    extreme_point = df.at[i, "close"]
                    acc_factor = min(0.2, acc_factor+0.02)
        else:
            df.at[i, "sar"] = prior_sar - acc_factor*(prior_sar - extreme_point)
            if df.at[i, "high"] > df.at[i, "sar"]:
                # reverse to uptrend
                uptrend = True
                prior_sar = min(df.loc[i-step:i, "close"])
                extreme_point = max(df.loc[i-step:i, "close"])
            else:
                # continue downtrend
                if df.at[i, "close"] < extreme_point:
                    extreme_point = df.at[i, "close"]
                    acc_factor = min(0.2, acc_factor+0.02)
        prior_sar = df.at[i, "sar"]
    return df

def stochastic_oscillator(df):
    lookback = 14
    df["stochastic_oscillator"] = ((df["close"] - df["close"].rolling(lookback).min()) /
        (df["close"].rolling(lookback).max() - df["close"].rolling(lookback).min())) * 100
    return df

def commodity_channel_index(df):
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    mean_dev = abs(typical_price - typical_price.rolling(20).mean()).rolling(20).mean()
    df["cci"] = (typical_price - typical_price.rolling(20).mean()) / (0.15 * mean_dev)
    return df

def rsi(df):
    df["dollar_pnl"] = df["close"].shift(1) - df["close"]
    avg_gains = df["dollar_pnl"].iloc[:14][df["dollar_pnl"].iloc[:14] > 0].sum() / 14
    avg_losses = abs(df["dollar_pnl"].iloc[:14][df["dollar_pnl"].iloc[:14] < 0].sum()) / 14
    for i, row in df.iloc[14:].iterrows():
        if row["dollar_pnl"] > 0:
            avg_gains = (avg_gains * 13 + row["dollar_pnl"]) / 14
        else:
            avg_losses = (avg_losses * 13 + abs(row["dollar_pnl"])) / 14
        if avg_losses == 0:
            rs = 100
        else:
            rs = avg_gains / avg_losses
        df.loc[i, "rsi"] = 100 - 100 / (1 + rs)
    return df

def bollinger_bands(df):
    df["bollinger"] = ((df["close"] - df["close"].rolling(21).mean()) / 
        2 * df["close"].rolling(21).std())
    return df

def average_true_range(df):
    high_vs_low = df["high"] - df["low"]
    high_vs_prev_close = df["high"] - df["close"].shift(-1)
    low_vs_prev_close = df["low"] - df["close"].shift(-1)
    tr = high_vs_low.to_frame("high_vs_low")
    tr["high_vs_prev_close"] = high_vs_prev_close
    tr["low_vs_prev_close"] = low_vs_prev_close
    tr["tr"] = tr.max(axis=1)
    df["atr"] = tr["tr"].rolling(14).mean()
    return df

def on_balance_volume(df):
    df["dollar_pnl"] = df["close"].shift(1) - df["close"]
    df["on_balance_volume"] = df["volume"]
    df["on_balance_volume"] = df.apply(lambda row: row.volume * -1 if row.dollar_pnl < 0 else row.volume, axis=1)
    df["on_balance_volume"] = df["on_balance_volume"].cumsum()
    return df

def chaikin_oscillator(df):
    money_flow_multiplier = ((df["close"] - df["low"]) / (df["high"] - df["low"])) / (df["high"] - df["low"])
    money_flow_volume = df["volume"] * money_flow_multiplier
    adl = money_flow_volume.cumsum()
    df["chaikin_oscillator"] = adl.ewm(com=(3-1)/2).mean() - adl.ewm(com=(10-1)/2).mean()
    return df
