import sys
sys.path.append("../")

import pandas as pd
from candle import Candle
from matplotlib import pyplot as plt
import cmnfunc as cfc

df=cfc.load_df("main.csv",drop_timestamp=True,date_2_num=True)

def simple_plot():
    fig,ax=plt.subplots()
    candles=Candle(len_candles=200,ax=ax,df=df)
    plt.show()

    
def adding_artists():
    fig,ax=plt.subplots()
    candles=Candle(len_candles=200,ax=ax,df=df)
    sma=cfc.sma(df['c'],20)
    ax.plot(sma)
    sma=cfc.sma(df['c'],30)
    ax.plot(sma)
    plt.show()

def addational_args_to_subplots():
    fig, ax = plt.subplots(layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax,df=df)
    plt.show()

def adding_axes():
    fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax[0],df=df)
    plt.show()

def other1():
    fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax[0],df=df)
    cfc.macd(df,ax[1])
    plt.show()


simple_plot()



