class EmptyDataFrameError(Exception):
    pass

class LogicError(Exception):
    def __init__(self,msg):
        self.msg=msg
    def __str__(self):
        return self.msg
        
class DirectionError(Exception):
    def __str__(self):
        return "Unknown direction"

class MissingDfColumns(Exception):
    def __init__(self,df):
        self.errdf=df.columns
    def __str__(self):
        return f"Some columns are missing from {list(self.errdf)}"

class CandlesLengthError(Exception):
    def __init__(self,elen_candle):
        self.elen_candle=elen_candle
    def __str__(self):
        return f"expected candle length >1; got {self.elen_candle}"
    
class CandlesToUpdateError(Exception):
    def __init__(self,candle_len):
        self.elen_candle=candle_len
    def __str__(self):
        return f"expected candles to update  to be >1; got {self.elen_candle}"
