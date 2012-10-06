from collocations import keywords_and_ngrams
import json
import sys

d = keywords_and_ngrams(sys.stdin.readlines())

print json.dumps(d)
