import os
import cPickle as pickle

# read bnc statistics using cpickle to read binary file 
BNCfile = os.path.join(os.path.dirname(__file__), "bnc.p")
fdistBNC = pickle.load( open( BNCfile, "rb" ) )

# total number of words in bnc
sumBNC = sum(v for k,v in fdistBNC.items())
