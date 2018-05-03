from operator import itemgetter
from datetime import datetime
import re
import sys
import pprint
from pymongo import MongoClient
import json
import subprocess
import csv

import numpy
import time

import pandas

client = MongoClient('mongodb://localhost:27017')
db = client['hkust']


#get wait number with lookback
results3=db.courses.aggregate([{'$unwind':"$sections"},
{'$project':{'sectionId':'$sections.sectionId','code':1,'wait':'$sections.wait','_id':0}},
{'$match': {'sectionId': {'$regex': re.compile('^L.', re.IGNORECASE)}}},
{'$project':{'sectionId':1,'code':1,'wait':1,'_id':0}}])

temp = []
codes = []
sectionIds = []
waits = []

for items in results3:
	codes.append(str(items['code']))
	sectionIds.append(str(items['sectionId']))
	waits.append(int(items['wait']))
	
for i in range(2,len(codes)):
	if codes[i]==codes[i-1] and codes[i]==codes[i-2] and sectionIds[i]==sectionIds[i-1] and sectionIds[i]==sectionIds[i-2]:
		temp.append(waits[i-2])
		temp.append(waits[i-1])
		temp.append(waits[i])
	
waitArray = numpy.array(temp)
waitArray = waitArray.reshape(int(len(temp)/3),3)

numpy.savetxt("foo.csv", waitArray, delimiter=",")
