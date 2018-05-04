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


def waitingListSizePrediction(cc, ln, ts):

	lectureNo = 'L'+str(ln)

	results=db.courses.aggregate([{'$unwind':"$sections"},
	{'$match': {'$and': [{'code': {'$regex': re.compile(cc, re.IGNORECASE)}},{'sections.sectionId': {'$regex': re.compile(lectureNo, re.IGNORECASE)}}] }},
	{'$project':{'code':1, 'sectionId':'$sections.sectionId','wait':'$sections.wait','sections.recordTime':1, 'timecheck': {'$eq': [ "$sections.recordTime", ts ] }}},
	{'$match':{'timecheck':True}},
	{'$sort':{'sections.recordTime':-1}},
	{'$project':{'_id':0, 'code':1,'sectionId':1,'wait':1,'recordTime':'$sections.recordTime','timecheck':1}}])
	#results_count=results.count()
	value = []
	for items in results:
		value.append(items['wait'])
	if len(value)==1:
		ans = 'The predicted \'wait\' value is '+str(value[0])
		print(ans)
	else:		
		db.courses.aggregate([{'$unwind':"$sections"},
		{'$match': {'$and': [{'code': {'$regex': re.compile(cc, re.IGNORECASE)}},{'sections.sectionId': {'$regex': re.compile(lectureNo, re.IGNORECASE)}}] }},
		{'$project':{'code':1, 'credits':1,'sectionId':'$sections.sectionId','wait':'$sections.wait','enrol':'$sections.enrol','quota':'$sections.quota','sections.recordTime':1, 'timecheck': {'$lte': [ "$sections.recordTime", ts ] }}},
		{'$match':{'timecheck':True}},
		{'$sort':{'sections.recordTime':-1}},
		{'$project':{'_id':0, 'code':1, 'credits':1,'sectionId':1,'enrol':1,'quota':1,'wait':1,'recordTime':'$sections.recordTime','timecheck':1}},
		{'$out' : 'earlierDocuments' }])
		
		getOne = db.earlierDocuments.find().skip(0).limit(1);
		getTwo = db.earlierDocuments.find().skip(0).limit(2);
		getThree = db.earlierDocuments.find().skip(0).limit(3);
		
		#db.earlierDocuments.drop()
		
		model1array = []
		model2array = []
		model3array = []
		for items1 in getOne:
			model1array.append(items1['credits'])
			model1array.append(items1['quota'])
			model1array.append(items1['enrol'])
		for items2 in getTwo:
			model2array.append(items2['wait'])
		for items3 in getThree:
			model3array.append(items3['wait'])
		print(model1array)
		print(model2array)
		print(model3array)
			

cc = input("Input the course code (in a format of (CCCCXXXXC) where \"C\" denotes a capitalized letter and \"X\" denotes a digit    ")
while not bool(re.match('[A-Z]{4}[0-9]{4}[A-Z]?', cc)):
	cc = input("Input a correct course code (in a format of (CCCCXXXXC) where \"C\" denotes a capitalized letter and \"X\" denotes a digit    ")
ln = int(input("Please indicate the lecture number (only numeric value)    "))
ts = input("Please input time slot (in a format of YYYY-MM-DD HH:mm)    ")
ts = datetime.strptime(ts, "%Y-%m-%d %H:%M")

waitingListSizePrediction(cc, ln, ts)



