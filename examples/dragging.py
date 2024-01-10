import sys

sys.path.append("../")

import cmnfunc as cfc
import pandas as pd
from candle import Candle
from keyboard import Keyboard
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation

df=cfc.load_df("main.csv",drop_timestamp=True,date_2_num=True)

def simple_plot():
    fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax[0],df=df)
    plt.show()

def simple_navigation():#press either arrow keys (<- | ->)
    fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax[0],df=df)
    keyboard=Keyboard(fig=fig,candles=candles,df=df)
    def update(frame)->None:
        pass
    a=FuncAnimation(fig,frames=60,func=update)
    plt.show()

def addational_navigation():
    fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
    candles=Candle(len_candles=200,ax=ax[0],df=df)
    keyboard=Keyboard(fig=fig,candles=candles,df=df,counter=20)
    cfc.macd(df,ax[1])
    def update(frame)->None:
        pass
    a=FuncAnimation(fig,frames=60,func=update)
    plt.show()

