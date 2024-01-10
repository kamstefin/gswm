import warnings
from datetime import timedelta
from typing import Optional

import numpy as np
import pandas as pd
from matplotlib import dates as mdates
from matplotlib.artist import Artist
from matplotlib.axes._axes import Axes
from matplotlib.dates import DateFormatter, HourLocator
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from matplotlib.ticker import NullFormatter, NullLocator
from matplotlib.widgets import MultiCursor
from typing_extensions import override

import cmnfunc as cfc
from cmnfunc import COLUMNS
from exceptions import *
from template import Template


class Candle(Template):
    LEFT=0 #mouse is dragging right (so we need to add data to the left)
    RIGHT=1 #mouse is draggin left (so we add new data to the right)
    RED, GREEN ,FACE_COLOR= "#ff1010", "green","#102020"
    CANDLE_KWARGS={"linewidth": 1, "fill": None, "alpha": 1}
    CANDLE_WIDTH=0.0003
    CANDLE_CODES=(
        Path.MOVETO,
        Path.LINETO,
        Path.LINETO,
        Path.LINETO,
        Path.LINETO,
        Path.MOVETO,
        Path.LINETO,
        Path.MOVETO,
        Path.LINETO)

    def __init__(self,len_candles:int,ax:Axes,df:pd.DataFrame,at:int=LEFT):
        if len_candles<1:
            raise CandlesLengthError(len_candles)
        if not isinstance(ax,Axes):
            raise Exception(f"Expected ax_ to be a matplotlib axes instance; got {type(ax)}")
        if not isinstance(df,pd.DataFrame):
            raise LogicError(f"Expected a {type(pd.DataFrame())}; got {type(df)}")
        else:
            if len(df)<len_candles:
                raise LogicError("len(df) is less than len(candles)(len_candles)")
        super().__init__(1)
        self.__max_candles_to_update__=len_candles
        self.__internal_state__=np.array([np.zeros(len_candles) for _ in range(3)])
        self.__ax__=ax
        self.__candles__=[
        self.__ax__.add_patch(PathPatch
                              (Path(np.zeros((len(Candle.CANDLE_CODES),2))),
                               **Candle.CANDLE_KWARGS,
                               )
                              )for _ in range(len_candles)]
        self.__set_xscale_format__()
        self.update(df,at)

    @override
    def update(self,df:pd.DataFrame,at:int=LEFT)->tuple[Artist]:
        """updates candles. if len(df)>max_candles_to_update only max_candles_to_update
        will be considered"""
        if at and at!=Candle.RIGHT:
            raise DirectionError
        if not isinstance(df,pd.DataFrame):
            raise LogicError(f"expected a pandas DataFrame; got{type(df)}")
        if df.empty:
            raise EmptyDataFrameError
        self.__validate_df__(df)
        df=df.iloc[:self.__max_candles_to_update__].copy()
        blittables=self.__update__(df,at)
        return blittables
        
    def __update__(self,df:pd.DataFrame,at:int)->tuple[Artist]:
        """
        d:date
        p:price
            ::
               d0 d1 d2
               .......
                  |        --------->p0(high)
                  |
                  |
                +----+     --------->p1(close if close>open else open)Green
                |    |
                |    |
                |    |
                +----+     --------->p2(close if close<open else open)Red
                  |
                  |
                  |        --------->p3(low)
        """
        
        x=self.__internal_state__[0]
        index=len(df) if at else self.__max_candles_to_update__-len(df)
        df["d0"]=df.index
        df["d1"]=df["d0"]+(Candle.CANDLE_WIDTH/2)
        df["d2"]=df["d0"]+Candle.CANDLE_WIDTH
        color=df["c"]>df["o"]
        df["p0"],df["p3"]=df.pop("h"),df.pop("l")
        for i in range(len(df)):
            x=df.iloc[i]
            dir_i_contrlr=i+(index*(not at))
            p1,p2=(x["c"],x["o"]) if color.iloc[i] else (x["o"],x["c"])
            self.__candles__[dir_i_contrlr].set(
                path=Path([
                    (x["d0"],p2),
                    (x["d0"],p1),
                    (x["d2"],p1),
                    (x["d2"],p2),
                    (x["d0"],p2),
                    (x["d1"],x["p3"]),
                    (x["d1"],p2),
                    (x["d1"],x["p0"]),
                    (x["d1"],p1),
                ],Candle.CANDLE_CODES),
                color=Candle.GREEN if color.iloc[i] else Candle.RED
            )
            self.__internal_state__[0][dir_i_contrlr]=x.name
            temp=[x[["p0","p3"]],[p1,p2]]
            self.__internal_state__[1][dir_i_contrlr]=np.min(temp)
            self.__internal_state__[2][dir_i_contrlr]=np.max(temp)
        self.__update_lims__(df)
        blittables=self.__reshape__(index,at)
        x=self.__internal_state__[0]
        return blittables

    def __reshape__(self,index:int,at:int)->tuple[Artist]:
        self.__candles__=self.__candles__[index:]+self.__candles__[:index]
        self.__internal_state__=np.array([np.concatenate((x[index:],x[:index]))for x in self.__internal_state__])
        x=self.__max_candles_to_update__
        blittables=self.__candles__[:index] if at else self.__candles__[-index:]
        return blittables

    def __update_lims__(self,df:pd.DataFrame)->None:
        not_zero=self.__internal_state__[0].min()
        m=self.__internal_state__[0].max()
        if not not_zero:not_zero=self.__internal_state__[0][self.__internal_state__[0]>0].min()
        m=self.__internal_state__[0].max()
        if m==not_zero:not_zero=0
        self.__ax__.set_xlim((not_zero,mdates.date2num(mdates.num2date(m)+timedelta(minutes=2))))
        not_zero=self.__internal_state__[1].min()
        if not not_zero:not_zero=self.__internal_state__[1][self.__internal_state__[0]>0].min()
        m=self.__internal_state__[2].max()
        if m==not_zero:not_zero=0
        self.__ax__.set_ylim((not_zero,m))
        
    def __validate_df__(self,df:pd.DataFrame)->None:
        for col in df.columns:
            if col not in cfc.COLUMNS:
                raise MissingDfColumns(df)
        df=df[cfc.COLUMNS]
        if len(df)>len(self.__candles__):
            warnings.warn("len(DataFrame) > len(candles); some candles might disappear",RuntimeWarning)

    def __set_xscale_format__(self):
       # self.__ax__.set_facecolor(Candle.FACE_COLOR)
        self.__ax__.xaxis.set_minor_locator(NullLocator())
        self.__ax__.xaxis.set_minor_formatter(NullFormatter())
        self.__ax__.xaxis.set_major_locator(HourLocator())
        self.__ax__.xaxis.set_major_formatter(DateFormatter(cfc.FORMAT))
        #self.__cursor_reference__= MultiCursor(
        #    canvas=None,
        #    axes=(self.__ax__,),
        #    useblit=True,
        #    color="gray",
        #    horizOn=True,
        #    ls="--"
        #)

