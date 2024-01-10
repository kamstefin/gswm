from matplotlib.artist import Artist
import pandas as pd
from exceptions import LogicError
from typing import Optional

import warnings
class Template:
    def __init__(self,minimum_len:int):
        if minimum_len<0:
            raise LogicError("'minimum_len' <0")
        self.minimum=minimum_len

    def __should_call__(self,minimum:int,df:pd.DataFrame,at:int)->Optional[tuple[Artist]]:
        if self.minimum<=minimum:
            return self.update(df,at)
        else:
            if minimum!=-1:
                warnings.warn("len(df) < 'self.minimum'; not updating",RuntimeWarning)

    def update(self,df:pd.DataFrame,at:int)->tuple[Artist]:
        pass
    
