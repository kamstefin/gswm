import warnings
from typing import Optional

import numpy as np
import pandas as pd
from matplotlib import dates as mdates
from matplotlib.backend_bases import Event
from matplotlib.figure import Figure

import cmnfunc as cfc
from candle import Candle
from exceptions import *
from template import Template


class Keyboard:
    def __init__(self,fig:Figure,candles:Candle,df:pd.DataFrame,counter:int=1):
        if counter<1:
            raise CounterError
        self.counter=counter
        if not isinstance(fig,Figure):
            raise NotFigureError(fig)
        if not isinstance(df,type(None)):
            if not isinstance(df,pd.DataFrame):
                raise LogicError(f"Expected a pandas DataFrame; got {type(df)}")
            self.idf=df
        else:
            self.idf=pd.DataFrame()
        if not isinstance(candles,Candle):
            raise LogicError(f"Expected a {type(Candle)} instance; got {type(candles)}")
        self.fig=fig
        self.__children__=[]
        self.max_min=0
        self+=candles
        self.__df_min__=self.df_counter=len(candles.__candles__)
        self.__init_keyboard__()
        self.__keys__={
            "left":0,
            "right":1,
        }

    def set_df(self,df:pd.DataFrame)->None:
        if not isinstance(df,pd.DataFrame):
            raise LogicError(f"expected a {type(self.idf)} got {type(df)}")
        if self.idf.index[0]!=df.index[0]:
            warnings.warn(f"({self.idf.index[0],df.index[0]}) Dataframe indexing has changed which may result in plots behaving wierdly",RuntimeWarning)
        if len(df)<len(self.idf):
            warnings.warn("len(df) < existing DataFrame which harms indexing; use `concat` instead",UserWarning)
            exit(1)
        self.idf=df

    def concat_down(self,df:pd.DataFrame)->None:
        if not isinstance(df,pd.DataFrame):
            raise LogicError(f"expected a {type(self.idf)} got {type(df)}")
        self.idf=pd.concat([self.idf,df],axis=0)

    def __iadd__(self,artist:Template):
        self.register(artist)
        return self

    def register(self,artist:Template):
        try:
            artist.__should_call__(-1,self.idf,0)
        except:
             raise SubclassError(artist)
        if self.max_min<artist.minimum:
             self.max_min=artist.minimum
        self.__children__.append(artist)

    def __init_keyboard__(self)->None:
        self.fig.canvas.mpl_connect("key_press_event",self.on_key_press)
        
    def on_key_press(self,event:Event)->None:
        key=event.key
        if key=="left" or key=="right":
            direction=self.__keys__[key]
            self.__can_call__(direction)
            
    def __can_call__(self,direction:int)->None:
        df_counter=self.df_counter
        counter=self.counter
        if (df_counter+counter)>len(self.idf)>df_counter:
            counter=len(self.idf)-df_counter
        if (df_counter-counter)<self.__df_min__<df_counter:
            counter=df_counter-self.__df_min__
        df_counter+=counter if direction else -counter
        if df_counter>len(self.idf) or df_counter<self.__df_min__:
            return
        for x in self.__children__:
            if direction:
                a=df_counter-max(counter,x.minimum)
                b=df_counter
            else:
                if x.minimum<self.__df_min__ :
                    a=df_counter-self.__df_min__
                    b=a+max(counter,x.minimum)
                else:
                    a=df_counter-x.minimum
                    b=a+x.minimum
            if min(a,b)<0:
                continue
            x.__should_call__(x.minimum,self.idf.iloc[a:b],direction)
        if counter!=self.counter:
            df_counter=len(self.idf)if direction else self.__df_min__
        self.df_counter = df_counter

class SubclassError(Exception):
    def __init__(self,eclass):
        self.eclass=type(eclass)
        
    def __str__(self):
        return f"{self.eclass} does not is not a subclass of {Template}"

class CounterError(Exception):
    pass

