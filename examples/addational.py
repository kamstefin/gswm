import sys

sys.path.append("../")

import cmnfunc as cfc
import pandas as pd
from bitstamp import Bitstamp
from candle import Candle
from keyboard import Keyboard
from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import MultiCursor
from template import Template
from typing_extensions import override

#to use navigation functionality in any other axes apart from the one
#containing candles, wrap it to override Temaplate.update function.
#this function is called in every update.
#lets wrap macd.

class Wrapmacd(Template):
    def __init__(self,df,len_candles,ax):
        super().__init__(len_candles+100)
        x,y=cfc.macd(df['c'])
        self.artists=[]
        self.artists.append(ax.plot(x)[0])
        self.artists.append(ax.plot(y)[0])

    @override
    def update(self,df:pd.DataFrame,at:int)->None:
        x,y=cfc.macd(df['c'])
        self.artists[0].set_data(df.index,x)
        self.artists[1].set_data(df.index,y) 

class Realtime():
    def __init__(self,len_candles:int=300,exchange:str="btcusd"):
        self.bitstamp=Bitstamp(exchange=exchange,interval=60,continous=True,initial_len=400)
        self.bitstamp.register_df_changed_callback(self.df_changed)
        df=self.mod_bitstamp_indexing()
        fig, ax = plt.subplots(2,1,layout="constrained",sharex=True)
        self.candles=Candle(len_candles,ax[0],df=df[cfc.COLUMNS])
        self.keyboard=Keyboard(fig,self.candles,df[cfc.COLUMNS],20)
        self.rmacd=Wrapmacd(df,len_candles,ax[1])
        self.keyboard.register(self.rmacd)
        cursor_reference=MultiCursor(fig.canvas,axes=ax)
        self.animation=FuncAnimation(fig,self.update,frames=90)
        plt.show()
        self.bitstamp.close()

        
    def update(self,frame)->None:
        pass
        
    def df_changed(self)->None:
        df=self.mod_bitstamp_indexing()
        self.keyboard.set_df(df)

    def mod_bitstamp_indexing(self)->pd.DataFrame:
        df=self.bitstamp.df
        df.index=pd.Series(df.index).apply(cfc.convert).apply(mdates.date2num)
        return df

Realtime()
