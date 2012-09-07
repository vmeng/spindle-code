import sys, os
import operator
import math
from stopwords import stopwords as my_stopwords
from bnc import fdistBNC, sumBNC

def keywords(input):
    # Text input statistics
    # frequency distribution of the text
    fdistPodcast = {}

    # total number of words in the text
    sumPodcasts = 0

    for line in input:
        for w in line.split():
            w = w.lower()
            if w not in my_stopwords and w.isalpha() and len(w) > 2:
                sumPodcasts = sumPodcasts+1
                if w not in fdistPodcast.keys():
                    fdistPodcast[w] = 1
                else:
                    fdistPodcast[w] = fdistPodcast[w]+1

    # dictionary containing log-likelihood
    # key: word, value: log-likelihood
    dicLL = {}

    for k, v in fdistPodcast.items():
        a = fdistBNC.get(k)
        b = fdistPodcast.get(k)
        if a == None:
            a = 0
        if b == None:
            b = 0

        # rename variables to follow wikipedia equation
        c = sumBNC
        d = sumPodcasts

        # ugly but effective, catching exceptions in case of division
        # by 0 or other issues
        try:
            E1 = float(c)*((float(a)+float(b))/ (float(c)+float(d)))
        except:
            E1 = 0

        try:
            E2 = float(d)*((float(a)+float(b))/ (float(c)+float(d)))
        except:
            E2 = 0      

        try:
            aE1 = math.log(a/E1)
        except:
            aE1 = 0

        try:
            aE2 = math.log(b/E2)
        except:
            aE2 = 0   

        try:
            dicLL[k] = float(2* ((a*aE1)+(b*aE2)))
        except:
            dicLL[k] == 0

    # sorting dictionary by value from more likely to less likely
    sorted_x = sorted(dicLL, key=dicLL.__getitem__, reverse=True)
    return [(k, dicLL[k]) for k in sorted_x[0:100] if k.isalpha()]
