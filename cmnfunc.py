from pytz import utc
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import numpy as np
from matplotlib import axes

COLUMNS = ["o", "h", "l", "c"]
FORMAT = "%d/%H:%M"

def mdate2readable(x):
    return datetime.strftime(mdates.num2date(x), FORMAT)

def sma(ser: pd.Series, window: int):
    return ser.rolling(window=window).mean()

def convert(__loc1):
    """Makes a datetime.datetime object without a timezone from an epoch timestamp"""
    return datetime.strptime(
        utc.localize(datetime.fromtimestamp(__loc1)).strftime(
            "%y-%m-%d %H:%M",
        ),
        "%y-%m-%d %H:%M",
    )

def avg_tr(df: pd.DataFrame, ax: axes._axes.Axes = None, window: int = 14):
    """Average true range"""
    hl = df["h"] - df["l"]
    hc = np.abs(df["h"] - df["c"].shift(1))
    lc = np.abs(df["l"] - df["c"].shift(1))
    r = np.max(pd.concat([hl, hc, lc], axis=1), axis=1).rolling(window).sum() / window
    if ax:
        ax.plot(r, lw=0.9)
        ax.set_ylim((r.min(), r.max()))
        ax.axhline(15, lw=0.9, marker="v", color="red")
    return r

def stoch(
    df: pd.DataFrame, period=14, ax: axes = None, h="h", l="l", c="c"
) -> tuple[pd.Series, pd.Series]:
    h = df[h].rolling(9).max()
    l = df[l].rolling(36).min()
    num = df[c] - l
    denom = h - l
    k = ((num / denom) * 100).rolling(period).mean()
    D = k.rolling(12).mean()
    if ax:
        ax.plot(k, label="k", lw=0.8)
        ax.plot(D, label="d", lw=0.8)
        ax.legend()
    return k, D

def load_df(_csv_name,drop_timestamp=False,reset_index=False,column1toindex=False,convert_2_readable=False,date_2_num=False,) -> pd.DataFrame:
    df = pd.read_csv(_csv_name, index_col=None)
    index = df.index
    if convert_2_readable:
        index = df["d"].apply(convert)
    if date_2_num:
        index = df["d"].apply(convert).apply(mdates.date2num)
    if column1toindex:
        index = df["d"]
    if drop_timestamp:
        df = df.drop("d", axis=1)
    df.index = index
    if reset_index:
        df.reset_index(inplace=True, drop=True)
    return df

def rsi(__ser: pd.Series, period: int = 14):
    __ser = __ser.diff()
    up = __ser.clip(lower=0)
    down = -1 * __ser.clip(upper=0)
    ma_up = up.rolling(period).mean()
    ma_down = down.rolling(period).mean()
    rsi = ma_up / ma_down
    rsi = 100 - (100 / (1 + rsi))
    return rsi

def macd(ser: pd.Series, ax: axes = None, x=12, y=26, z=9):
     ema_12 = ser.ewm(span=x, adjust=False).mean()
     ema_26 = ser.ewm(span=y, adjust=False).mean()
     md = ema_12 - ema_26
     signal = md.ewm(span=z, adjust=False).mean()
     if ax:
         ax.plot(md, label="m", lw=0.9)
         ax.plot(signal, label="s", lw=0.9)
         ax.legend()
     return signal, md
