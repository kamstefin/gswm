import itertools
import sys
import time
import warnings
from datetime import datetime
from threading import Condition, Lock, Thread
from urllib.parse import urlencode

import pandas as pd
import requests
import urllib3

import cmnfunc as cfc


class Bitstamp:
    EXCHANGES=['1incheur', '1inchusd', 'aavebtc', 'aaveeur', 'aaveusd', 'adabtc', 'adaeur', 'adausd', 'algobtc', 'algoeur', 'algousd', 'alphaeur', 'alphausd', 'ampeur', 'ampusd', 'anteur', 'antusd', 'apeeur', 'apeusd', 'audiobtc', 'audioeur', 'audiousd', 'avaxeur', 'avaxusd', 'axseur', 'axsusd', 'bandeur', 'bandusd', 'bateur', 'batusd', 'bchbtc', 'bcheur', 'bchusd', 'btceur', 'btcgbp', 'btcpax', 'btcusd', 'btcusdc', 'btcusdt', 'chzeur', 'chzusd', 'compeur', 'compusd', 'crveur', 'crvusd', 'ctsieur', 'ctsiusd', 'cvxeur', 'cvxusd', 'daiusd', 'dgldeur', 'dgldusd', 'dogeeur', 'dogeusd', 'doteur', 'dotusd', 'dydxeur', 'dydxusd', 'enjeur', 'enjusd', 'enseur', 'ensusd', 'eth2eth', 'ethbtc', 'etheur', 'ethgbp', 'ethpax', 'ethusd', 'ethusdc', 'ethusdt', 'eurcveur', 'eurcvusdt', 'euroceur', 'eurocusdc', 'eurteur', 'eurtusd', 'eurusd', 'feteur', 'fetusd', 'flreur', 'flrusd', 'ftmeur', 'ftmusd', 'galaeur', 'galausd', 'gbpusd', 'godseur', 'godsusd', 'grteur', 'grtusd', 'gusdusd', 'hbareur', 'hbarusd', 'imxeur', 'imxusd', 'injeur', 'injusd', 'knceur', 'kncusd', 'ldoeur', 'ldousd', 'linkbtc', 'linkeur', 'linkgbp', 'linkusd', 'lrceur', 'lrcusd', 'ltcbtc', 'ltceur', 'ltcgbp', 'ltcusd', 'manaeur', 'manausd', 'maticeur', 'maticusd', 'mkreur', 'mkrusd', 'mpleur', 'mplusd', 'neareur', 'nearusd', 'nexoeur', 'nexousd', 'paxusd', 'perpeur', 'perpusd', 'pyusdeur', 'pyusdusd', 'radeur', 'radusd', 'rlyeur', 'rlyusd', 'rndreur', 'rndrusd', 'sandeur', 'sandusd', 'sgbeur', 'sgbusd', 'shibeur', 'shibusd', 'skleur', 'sklusd', 'slpeur', 'slpusd', 'snxeur', 'snxusd', 'soleur', 'solusd', 'storjeur', 'storjusd', 'suieur', 'suiusd', 'sushieur', 'sushiusd', 'sxpeur', 'sxpusd', 'traceur', 'tracusd', 'umaeur', 'umausd', 'unibtc', 'unieur', 'uniusd', 'usdceur', 'usdcusd', 'usdcusdt', 'usdteur', 'usdtusd', 'vegaeur', 'vegausd', 'wbtcbtc', 'wecaneur', 'wecanusd', 'xlmbtc', 'xlmeur', 'xlmgbp', 'xlmusd', 'xrpbtc', 'xrpeur', 'xrpgbp', 'xrpusd', 'xrpusdt', 'yfieur', 'yfiusd', 'zrxeur', 'zrxusd']

    MAX_DATA_REQUEST=1000
    URI = "https://www.bitstamp.net/api/v2/ohlc/"
    INTERVALS=(
        60*1,
        60*5,
        60*15,
        60*30,
        60*60
    )
    MAX_API_CALLS=8000,10*60  #api calls in 10mins must be <8000
    SERVER_UPDATE=3
    
    def __init__(self,
                 exchange:str=EXCHANGES[0],
                 initial_len:int=MAX_DATA_REQUEST,
                 interval:int=INTERVALS[0],
                 continous:bool=False
                 ):
        if exchange not in Bitstamp.EXCHANGES:
            raise UnknownExchangeError(exchange)
        if initial_len>Bitstamp.MAX_DATA_REQUEST:
            raise ValueError("initial_len > Bitstamp.MAX_DATA_REQUEST")
        if interval not in Bitstamp.INTERVALS:
            raise IntervalError(interval)
        self.exchange,self.data_len,self.interval=exchange,initial_len,interval
        self.__df__=pd.DataFrame(columns=cfc.COLUMNS)
        self.__await_lock__=Lock()
        self.__await_data__=Condition(self.__await_lock__)
        self.c_epoch=Bitstamp.current_epoch(self.interval)
        self.api_call_count=1-Bitstamp.MAX_API_CALLS[0]
        self.api_call_timer=self.c_epoch+Bitstamp.MAX_API_CALLS[1]
        self.callbacks=[]
        Thread(target=self.pull,args=(True,)).start()
        if continous:
            self.await_data()
            self.data_len=1
            self.cpull=Thread(target=self.continous_pull)
            self.__should_stop__=False
            self.cpull.start()
            
    @property
    def df(self)->pd.DataFrame:
        return self.__df__.copy()
    
    def has_data(self)->bool:
        return not self.__df__.empty

    def await_data(self)->None:
        if self.has_data():
            return
        with self.__await_lock__:
            self.__await_data__.wait()
            
    def validate_index(self,index,should_notify:bool)->None:
        diff=index-self.interval<self.__df__.index[-1]
        if diff<0:#server might not have finished updating
            warnings.warn(f"server might not have finished updating;\
            sleeping ({Bitstamp.SERVER_UPDATE}s) again",RuntimeWarning)
            time.sleep(Bitstamp.SERVER_UPDATE)
            self.pull(should_notify)
        elif diff>0:
            print(f"index{index} already index {self.__df__.index[-1]}")
            raise Exception(f"malformed data.{index} {self.__df__.index[-1]}")

    def validate_api_restrictions(self)->None:
        if self.api_call_count+1==0 and self.c_epoch>self.api_call_timer:
            raise MaxApiCallsExceededError

    def pull(self,should_notify:bool)->None:
        url=self.make_url(self.data_len,self.c_epoch-self.data_len*self.interval)
        self.validate_api_restrictions()
        try:
            data=requests.get(url,timeout=10)
        except (urllib3.exceptions.MaxRetryError,requests.exceptions.ConnectionError):
            Bitstamp.await_internet()
            self.pull(should_notify)
            return
        try:
            data=data.json()['data']["ohlc"]
        except Exception as e:
            raise Exception("Internal server error",e)
        if not data:
            warnings.warn(f"Server did not update; sleeping ({Bitstamp.SERVER_UPDATE})",RuntimeWarning)
            time.sleep(Bitstamp.SERVER_UPDATE+3)
            self.pull(should_notify)
            return
        df=Bitstamp.json2pandas(data)
        if not self.has_data():
            self.__df__=df
        else:
            self.validate_index(df.index[0],should_notify)#to handle malformed data
            self.__df__=pd.concat([self.__df__,df],axis=0)
        for func in self.callbacks:
            func()
        if should_notify:
            with self.__await_lock__:
                self.__await_data__.notify_all()

    def register_df_changed_callback(self,func)->None:
        self.callbacks.append(func)
        
    def continous_pull(self)->None:
        while  not  self.__should_stop__:
            time2sleep=self.interval-(Bitstamp.current_epoch(1)-Bitstamp.current_epoch(self.interval))
            should_continue=self.__sleep_aware__(time2sleep+Bitstamp.SERVER_UPDATE)
            if not should_continue:
                break
            self.c_epoch=Bitstamp.current_epoch(self.interval)
            self.pull(False)
            
    def __sleep_aware__(self,epoch)->bool:
        for _ in range(epoch):
            for _ in range(10):
                time.sleep(1/10)
                if self.__should_stop__:
                    return False
        return True
    
    def close(self)->None:
        if not hasattr(self,"__should_stop__"):
            raise InvalidOperationError
        self.__should_stop__=True
        self.cpull.join()

    def make_url(self,limit:int,start)->str:
        return f"{Bitstamp.URI}{self.exchange}/?{urlencode({'limit':limit,'step':self.interval,'start':start})}"

    @staticmethod
    def json2pandas(data:tuple[dict])->pd.DataFrame:
        data = pd.DataFrame(data)
        data = data.drop("volume", axis=1).iloc[:, [3, 1, 2, 0, 4]]
        data = data.map(float)
        data.index = (
            pd.Series(data.pop("timestamp"), name="d").map(int)
        )
        data.columns = cfc.COLUMNS
        return data

    @staticmethod
    def current_epoch(relation:int)->int:
        cur_epoch=time.mktime(datetime.now().timetuple())
        cur_epoch-=cur_epoch%relation
        return int(cur_epoch)
    
    @staticmethod
    def await_internet()->None:
        ip="95.217.163.246"#  archlinux.org
        loading,started=itertools.cycle("|\\-/"),False
        while 1:
            try:
                response=urllib3.request("GET",ip,timeout=1)
                break
            except (urllib3.exceptions.NewConnectionError,urllib3.exceptions.MaxRetryError):
                if started==False:
                    print(f"trying to connect, maybe no internet (1s)  ",end="")
                    started=True
                print("\b",next(loading),sep="",end="")
                sys.stdout.flush()
                time.sleep(0.3)
        print("\x1b[1K\rconnected")

class UnknownExchangeError(Exception):
    def __init__(self,exchange:str):
        self.exchange=exchange

    def __str__(self)->str:
        return f"Uknown exchange '{self.exchange}';check Bitstamp.EXCHANGES"

class IntervalError(Exception):
    def __init__(self,interval:int):
        self.interval=interval
        
    def __str__(self)->str:
        return f"interval ({self.interval}) not in Bitstamp.INTERVALS"
    
class InvalidOperationError(Exception):
    def __str__(self)->str:
        return "func:`stop` cannot be called when `continous` attribute is False"

class MaxApiCallsExceededError(Exception):
    def __str__(self)->str:
        return "api calls have exceeded the maximum allowable; stopping not to be banned"
