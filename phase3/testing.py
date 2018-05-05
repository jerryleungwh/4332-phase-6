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


def newFunction(f, start, end):
	#print(start)
	#print(end )
	'''
	result = db.courses.aggregate([
	{'$unwind':"$sections"},
	{'$project':{'_id':0,'code':1,'credits':1,'Matched Time Slot':'$sections.recordTime','title':1,'sections':1}},
	{'$project':{
		'_id':0,
		'code':1,
		'credits':1,
		'Matched Time Slot':1,
		'title':1,
		"sections.recordTime":1,
		"sections.sectionId":1,
		"sections.dateAndTime":"$sections.offerings.dateAndTime",
		"sections.quota":1,
		"sections.enrol":1,
		"sections.Avail":{'$subtract': ["$sections.quota","$sections.enrol"] },
		"sections.wait":1,
		#compute the f * enrol for later use
		"fenrol":{'$multiply':[f,"$sections.enrol"]}}},
	
	
	{'$project':{
		'_id':0,
		'code':1,
		'credits':1,
		'Matched Time Slot':1,
		'title':1,
		"sections.recordTime":1,
		"sections.sectionId":1,
		"sections.dateAndTime":1,
		"sections.quota":1,
		"sections.enrol":1,
		"sections.Avail":1,
		"sections.wait":1,
		"fenrol":1,
		#check if the required condition is saitified, adding the new attribute
		"sections.Satisfied":{
			'$cond':{
				'if':{
					'$gte': ["$sections.wait", "$fenrol"]
				},
				'then': "Yes",
				'else': "No",
			}
		}
	}},
	
	
	{'$project':{
		'_id':0,
		"title":1,
		"recordTime":"$sections.recordTime",
		"List.sectionId":"$sections.sectionId",
		"List.dateAndTime":"$sections.dateAndTime",
		"List.quota":"$sections.quota",
		"List.enrol":"$sections.enrol",
		"List.Avail":"$sections.Avail",
		"List.wait":"$sections.wait",
		"List.Satisfied":"$sections.Satisfied"
	}},
	{'$group':{
		"_id":{
			"title":"$title",
			"recordTime":"$recordTime"
		},
		"List":{'$push':{"List":"$List"}}

	}},
	{'$project':{
		'_id':0,
		"title":"$_id.title",
		"recordTime":"$_id.recordTime",
		"List":"$List.List"

	}},
	#output to a new collection for later use
	{'$out':"allWithStatisfied"}
	],allowDiskUse=True
	)
	'''
	
	
	results2 = db.courses.aggregate([
	{'$unwind':"$sections"},
	#//match the recordTime(Date object) twice to filter out only the time within the range using the gte and lte operations
	{'$project': {'code':1, 'title':1, 'credits':1, '_id':0, 'sections':1, 'greater_than_start': {'$gte': ["$sections.recordTime", start]} ,'less_than_end': {'$lte': ["$sections.recordTime", end]}}},
	{'$match': {'greater_than_start':True}},
	{'$match': {'less_than_end':True}},
	#//match only the section of object is Lecture using regular expression, as required
	{'$match': {'sections.sectionId': {'$regex': re.compile('^L', re.IGNORECASE)}}},
	
	#	//would match again to keep only the section that match the waitlist requirement (i.e. the number of students in the waiting list of this lecture section is greater than or equal to f multiplied by the number of students enrolled in this lecture section in that time slot.)
	#//The initial value of f is hardcoded as 0.05.
	{'$project':{'code':1, 'title':1, 'credits':1, '_id':0, 'sections':1,"fenrol":{'$multiply':[f,"$sections.enrol"]}}},
	{'$project': {'code':1, 'title':1, 'credits':1, '_id':0, 'sections':1, 'wait_list_fulfilled': {'$gte': ["$sections.wait", "$fenrol"]}}},
	{'$match': {'wait_list_fulfilled':True}},
	#	//to retrieve the most updated information, we order it in descedning order; the $first operation can get the most updated info
	#//$first is a feature that returns the value that results from applying an expression to the first document in a group of documents that share the same group by key. Only meaningful when documents are in a defined order.
	{'$sort':{'title':-1,"sections.recordTime":-1}},
	{'$group':{
		"_id": "$code",
		"CourseTitle": {"$first": "$title"},
		"NoOfcredits": {"$first": "$credits"},
		"MatchedrecordTime": {"$first": "$sections.recordTime"}
		}
	},
	#//lookup the information of the course_section that fulfill the waitlist requirement from the "All" document we outputted at the beginning
	#//used a complicated operation, joining them using two attributes i.e. course name and recordTime. 
	{'$lookup':
		{
			'from': "allWithStatisfied",
			'let':{'time':"$MatchedrecordTime",'name':"$CourseTitle"},
			'pipeline':[
				{'$match':
					{'$expr':
						{'$and':
							[
							{'$eq':["$title", "$$name"]},
							{'$eq':["$recordTime", "$$time"]}
							]
						}
					}
				}
				],
			'as': "course_info"
		}
	},
	#output the information as required
	{'$project':{'_id':1,'CourseTitle':1,'NoOfcredits':1,'MatchedrecordTime':1,'SectionList':"$course_info.List"}},
	{'$project':{'Course Code':'$_id','CourseTitle':1,'No Of credits':1,'Matched Time Slot':'$MatchedrecordTime',"SectionList.sectionId":1,"SectionList.dateAndTime":1,"SectionList.quota":1,"SectionList.enrol":1,"SectionList.Avail":1,"SectionList.wait":1,"SectionList.Satisfied":1,'_id':0}}
	])
	
	
	
	for items in results2:
		pprint.pprint(items)
		
		
		
		
		
start_ts = datetime.strptime('2018-01-26 10:00', "%Y-%m-%d %H:%M")

end_ts = datetime.strptime('2018-01-26 13:00', "%Y-%m-%d %H:%M")

newFunction(0.5, start_ts, end_ts)
