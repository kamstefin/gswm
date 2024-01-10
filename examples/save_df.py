import sys

sys.path.append("../")
from bitstamp import Bitstamp

def one_time():
    bitstamp=Bitstamp(exchange="btcusd",initial_len=1000,interval=60) 
    bitstamp.await_data() #block until there is some data
    bitstamp.df.to_csv("main.csv")

def continous():
    bitstamp=Bitstamp(exchange="btcusd",initial_len=1000,interval=60,continous=True) 
    bitstamp.await_data() #block until there is some data
    bitstamp.df.to_csv("main.csv")
    #some logic
    # ...
    #
    bitstamp.close()



