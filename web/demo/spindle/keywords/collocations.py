from collections import defaultdict
import sys
from collections import OrderedDict
import math
import json
from stopwords import stopwords as my_stopwords
from bnc import fdistBNC, sumBNC

def ngrams(words, n=2, padding=False):
    "Compute n-grams with optional padding"
    pad = [] if not padding else [None]*(n-1)
    grams = pad + words + pad
    return (tuple(grams[i:i+n]) for i in range(0, len(grams) - (n - 1)))

def keywords_and_ngrams(input):
    # Text input statistics
    # frequency distribution of the text
    fdistPodcasts = {}

    # Total number of words in the text, sans stopwords
    sumPodcasts = 0

    # List of all words in text
    listWords = []

    for line in input:
        for w in line.split():
            w = w.lower()
            listWords.append(w)
            if w not in my_stopwords and w.isalpha() and len(w) > 2:
                sumPodcasts = sumPodcasts+1
                if w not in fdistPodcasts.keys():
                    fdistPodcasts[w] = 1
                else:
                    fdistPodcasts[w] = fdistPodcasts[w]+1

    # dictionary containing log-likelihood
    # key: word, value: log-likelihood
    dicLL = {}

    for k, v in fdistPodcasts.items():
        a = fdistBNC.get(k)
        b = fdistPodcasts.get(k)
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
    
    listKeywords = [(k, dicLL[k]) for k in sorted_x[0:100] if k.isalpha()]

    keywords = [keyw[0] for keyw in listKeywords]

    # grab n-grams

    # show frequency
    counts = defaultdict(int)
    for ng in ngrams(listWords, 2, False):
        counts[ng] += 1

    listCol = []
    for c, ng in sorted(((c, ng) for ng, c in counts.iteritems()), reverse=False):
        #print c, ng
        w0 = ng[0]
        w1 = ng[1]
        #print w, ng, listKeywords
        if w0 in keywords and w1 in keywords and c>2:
            listCol.append((ng, c))
            
    return (listKeywords, listCol)
