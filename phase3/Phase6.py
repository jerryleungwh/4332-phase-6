from operator import itemgetter
from datetime import datetime
import re
import sys
import pprint
from pymongo import MongoClient
import json
import subprocess
import csv
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import GRU
from keras.models import model_from_json
import numpy
import time
import keras
import pandas



client = MongoClient('mongodb://localhost:27017')
db = client['hkust']

pp = pprint.PrettyPrinter(width = 160, compact=True)

def testing():
	print('\ntesting here \n')



def testDbConnection():
	print("A document of the collection is printed to test the connection")
	print(db.course.find_one())



def main():
	# here, we need to implement for the flow
	# display the menu
	choice = "0"
	while (choice != "6"):
		print("\n   Main Menu")
		print("=======================")
		print("1. Drop/ Empty Collections")
		print("2. Crawl Data")
		print("3. Search Course")
		print("4. Predict Waiting List Size")
		print("5. Train Waiting List Size")
		print("6. Exit")



		# allow the user to choose one of the functions in the menu
		choice = input("Please input your choice (1-6): ")

		print("")

		# check the input and call the correspondence function
		if (choice == '1'):
			dropAndEmptySuccessful()
		elif (choice == '2'):
			data = input("Please input a URL to be crawled or \"default\" ")
			while (not('http' in data or 'default' in data)):
				data = input("Please input a valid URL or \"dafault\"")
			crawlData(data)
		elif (choice == '3'):
			courseSearch()
		elif (choice == '4'):
			while True:
				try:
					cc = input("Input the course code (in a format of (CCCCXXXXC) where \"C\" denotes a capitalized letter and \"X\" denotes a digit    ")
					while not bool(re.match('[A-Z]{4}[0-9]{4}[A-Z]?', cc)):
						cc = input("Input a correct course code (in a format of (CCCCXXXXC) where \"C\" denotes a capitalized letter and \"X\" denotes a digit    ")
					ln = int(input("Please indicate the lecture number (only numeric value)    "))
					ts = input("Please input time slot (in a format of YYYY-MM-DD HH:mm)    ")
					ts = datetime.strptime(ts, "%Y-%m-%d %H:%M")
					break
				except ValueError:
					print("Please input all values in correct format")
			waitingListSizePrediction(cc, ln, ts)
		elif (choice == '5'):
			waitingListSizeTraining()
		elif (choice == '6'):
			sys.exit()
		else:
			print("Invalid Input!", choice)


# 5.1
def dropAndEmptySuccessful():
	# checking should be done
	db.courses.drop()
	print("Collection dropping and empty collection creating are successful")

# 5.2
def crawlData(enteredURL):
	if enteredURL == 'default':
		
		enteredURL = "http://comp4332.com/realistic"
		print("Default database used")
	else:
		print(enteredURL, "database used")
	with open('url.txt',"w") as f:
		f.write(enteredURL)
	strCommand = 'scrapy crawl mongo'
	subprocess.run(strCommand, shell=True)
	print("Data Crawling is successful and all data are inserted into the database")


# 5.3
def courseSearch():
	print("There are two search operations available:")
	print("\t1. Course Search by Keyword")
	print("\t2. Course Search by Waiting List Size\n")
	choice = input("Please indicate the preferred operation\n")



	# keyword search
	if choice == "1":
		query = input("Please enter your keyword  (you may enter \"Data\" for testing) ")
		keywordSearch(query)
	#waitlist search
	elif choice == "2":
		while True:
			try:
				print("Notes: you may use the f = 0.05, date = 2018-02-01 11:00 and 2018-02-10 12:00 for testing")
				print("Notes: incorrect date format will not be accepted")
				f = input("Please input f value ")
				f = float(f)
				start_ts = input("Please input start time (in a format of YYYY-MM-DD HH:mm) ")
				start_ts = datetime.strptime(start_ts, "%Y-%m-%d %H:%M")
				end_ts = input("Please input end time (in a format of YYYY-MM-DD HH:mm) ")
				end_ts = datetime.strptime(end_ts, "%Y-%m-%d %H:%M")
				break
			except ValueError:
				print("Please input all values in correct format")

		waitingListSearch(f, start_ts, end_ts)
	else:
		print("Please enter a valid choice\n")

def convertToRE(query):
	keywords = re.sub(r"""[,;.?:'"/\&+-+*!()]""", " ", query).split()

	for index, element in enumerate(keywords):
		keywords[index] = r"(\s|\b)" + element + r"(\s|\b)"

	query = '|'.join(keywords)
	return query

def keywordSearch(query):
	#matchedCourses = []
	#print(re.sub(r"""[,;.?:'"/\&+-+*!()]""", " ", query).split())

	query = convertToRE(query)
	
	
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
	}},
	
	
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

	}},
	
	
	{'$project':{
		'_id':0,
		"code":1,
		"recordTime":"$sections.recordTime",
		"List.sectionId":"$sections.sectionId",
		"List.dateAndTime":"$sections.dateAndTime",
		"List.quota":"$sections.quota",
		"List.enrol":"$sections.enrol",
		"List.Avail":"$sections.Avail",
		"List.wait":"$sections.wait",
	}},
	{'$group':{
		"_id":{
			"code":"$code",
			"recordTime":"$recordTime"
		},
		"List":{'$push':{"List":"$List"}}

	}},
	{'$project':{
		'_id':0,
		"code":"$_id.code",
		"recordTime":"$_id.recordTime",
		"List":"$List.List"

	}},
	#output to a new collection for later use
	{'$out':"allCoursesByrecordTime"}
	],allowDiskUse=True
	)
	
	
	results = db.courses.aggregate([
	#match the course according to the specified requirement, we are using regular expression to check if the title in the database contains the phrase(s) in the query
	{'$match':  {'$or': [{"title": {"$regex": query}},{"description": {"$regex": query}},{"sections.remarks": {"$regex": query}}]}},
	{'$project': {"code":1, "title":1, "credits":1, "_id":0, "sections":1}},
	{'$unwind':"$sections"},
	#to retrieve the section details in sections which has the largest recordTime, we reorder it in descending order
	#by using the $first operation we get the recordTime with latest date, which contains the most updated information
	#$first is a feature that returns the value that results from applying an expression to the first document in a group of documents that share the same group by key. Only meaningful when documents are in a defined order.
	{'$sort':{"title":-1,"sections.recordTime":-1}},
	{'$group':{
		"_id": "$code",
		"CourseTitle": {"$first": "$title"},
		"NoOfcredits": {"$first": "$credits"},
		"MatchedrecordTime": {"$first": "$sections.recordTime"}
		}
	},
	{'$lookup':
		{
			'from': "allCoursesByrecordTime",
			'let':{'time':"$MatchedrecordTime",'courseCode':"$_id"},
			'pipeline':[
				{'$match':
					{'$expr':
						{'$and':
							[
							{'$eq':["$code", "$$courseCode"]},
							{'$eq':["$recordTime", "$$time"]}
							]
						}
					}
				}
				],
			'as': "course_info"
		}
	},
	#output in the return format as required
	{'$project':{'_id':1,'CourseTitle':1,'NoOfcredits':"$credits",'SectionList':"$course_info.List"}},
	{'$sort':{'_id':1}},
	{'$project':{'Course Code':'$_id','CourseTitle':1,'No Of credits':1,"SectionList.sectionId":1,"SectionList.dateAndTime":1,"SectionList.quota":1,"SectionList.enrol":1,"SectionList.Avail":1,"SectionList.wait":1,"SectionList.Satisfied":1,'_id':0}}
	])

	for instance in results:
		pprint.pprint(instance)
		
		
	db.allCoursesByrecordTime.drop()
'''
def newFunction(f, start, end):
	#print(start)
	#print(end )
	db.course2.aggregate([
	{'$unwind':"$TimeList"},
	{'$project':{'_id':0,'Cname':1,'TimeList':1}},
	{'$unwind':"$TimeList.SectionList"},
	{'$project':{
		'_id':0,
		'Cname':1,
		"TimeList.timeslot":1,
		"TimeList.SectionList.section":1,
		"TimeList.SectionList.date_time":1,
		"TimeList.SectionList.quota":1,
		"TimeList.SectionList.enrol":1,
		"TimeList.SectionList.available":1,
		"TimeList.SectionList.wait":1,
		#compute the f * enrol for later use
		"fenrol":{'$multiply':[f,"$TimeList.SectionList.enrol"]}}},
	{'$project':{
		'_id':0,
		'Cname':1,
		"TimeList.timeslot":1,
		"TimeList.SectionList.section":1,
		"TimeList.SectionList.date_time":1,
		"TimeList.SectionList.quota":1,
		"TimeList.SectionList.enrol":1,
		"TimeList.SectionList.available":1,
		"TimeList.SectionList.wait":1,
		"fenrol":1,
		#check if the required condition is saitified, adding the new attribute
		"TimeList.SectionList.Satisfied":{
			'$cond':{
				'if':{
					'$gte': ["$TimeList.SectionList.wait", "$fenrol"]
				},
				'then': "Yes",
				'else': "No",
			}
		}
	}},
	{'$project':{
		'_id':0,
		"Cname":1,
		"timeslot":"$TimeList.timeslot",
		"List.section":"$TimeList.SectionList.section",
		"List.date_time":"$TimeList.SectionList.date_time",
		"List.quota":"$TimeList.SectionList.quota",
		"List.enrol":"$TimeList.SectionList.enrol",
		"List.available":"$TimeList.SectionList.available",
		"List.wait":"$TimeList.SectionList.wait",
		"List.Satisfied":"$TimeList.SectionList.Satisfied"
	}},
	{'$group':{
		"_id":{
			"Cname":"$Cname",
			"timeslot":"$timeslot"
		},
		"List":{'$push':{"List":"$List"}}

	}},
	{'$project':{
		'_id':0,
		"Cname":"$_id.Cname",
		"timeslot":"$_id.timeslot",
		"List":"$List.List"

	}},
	#output to a new collection for later use
	{'$out':"allWithStatisfied"}
	]
	)

	results2 = db.course2.aggregate([
	{'$unwind':"$TimeList"},
	#//match the timeslot(Date object) twice to filter out only the time within the range using the gte and lte operations
	{'$project': {'Course_Code':1, 'Cname':1, 'Units':1, '_id':0, 'TimeList':1, 'greater_than_start': {'$gte': ["$TimeList.timeslot", start]} ,'less_than_end': {'$lte': ["$TimeList.timeslot", end]}}},
	{'$match': {'greater_than_start':'true'}},
	{'$match': {'less_than_end':'true'}},
	{'$unwind':"$TimeList.SectionList"},
	#//match only the section of object is Lecture using regular expression, as required
	{'$match': {"TimeList.SectionList.section":'/^L/i'}},
	#	//would match again to keep only the section that match the waitlist requirement (i.e. the number of students in the waiting list of this lecture section is greater than or equal to f multiplied by the number of students enrolled in this lecture section in that time slot.)
	#//The initial value of f is hardcoded as 0.05.
	{'$project':{'Course_Code':1, 'Cname':1, 'Units':1, '_id':0, 'TimeList':1,"fenrol":{'$multiply':[f,"$TimeList.SectionList.enrol"]}}},
	{'$project': {'Course_Code':1, 'Cname':1, 'Units':1, '_id':0, 'TimeList':1, 'wait_list_fulfilled': {'$gte': ["$TimeList.SectionList.wait", "$fenrol"]}}},
	{'$match': {'wait_list_fulfilled':'true'}},
	#	//to retrieve the most updated information, we order it in descedning order; the $first operation can get the most updated info
	#//$first is a feature that returns the value that results from applying an expression to the first document in a group of documents that share the same group by key. Only meaningful when documents are in a defined order.
	{'$sort':{'Cname':-1,"TimeList.timeslot":-1}},
	{'$group':{
		"_id": "$Course_Code",
		"CourseTitle": {"$first": "$Cname"},
		"NoOfUnits": {"$first": "$Units"},
		"MatchedTimeSlot": {"$first": "$TimeList.timeslot"}
		}
	},
	#//lookup the information of the course_section that fulfill the waitlist requirement from the "All" document we outputted at the beginning
	#//used a complicated operation, joining them using two attributes i.e. course name and timeslot. 
	{'$lookup':
		{
			'from': "allWithStatisfied",
			'let':{'time':"$MatchedTimeSlot",'name':"$CourseTitle"},
			'pipeline':[
				{'$match':
					{'$expr':
						{'$and':
							[
							{'$eq':["$Cname", "$$name"]},
							{'$eq':["$timeslot", "$$time"]}
							]
						}
					}
				}
				],
			'as': "course_info"
		}
	},
	#output the information as required
	{'$project':{'_id':1,'CourseTitle':1,'NoOfUnits':1,'MatchedTimeSlot':1,'SectionList':"$course_info.List"}},
	{'$project':{'_id':1,'CourseTitle':1,'NoOfUnits':1,'MatchedTimeSlot':1,"SectionList.section":1,"SectionList.date_time":1,"SectionList.quota":1,"SectionList.enrol":1,"SectionList.available":1,"SectionList.wait":1,"SectionList.Satisfied":1}}
	])

	for instance in results2:
		print(instance)


def printAllCourses(courses):
	if len(courses) == 0:
		print("There is no match")
	else:
		print("Here are all the matched courses")
		for course in courses:
			printACourse(course)

def printACourse(courseDetails):
	print('Course Code:', courseDetails[0])
	print('Course Title', courseDetails[1])
	print('No. of Units/Credits', courseDetails[2])
	for section in courseDetails[6]:
		print('\nSection Details: ')
		print('\tSection', section[0])
		print('\tDate & Time', section[1])
		print('\tQuota', section[4])
		print('\tEnrol', section[5])
		print('\tAvail', section[6])
		print('\tWait', section[7])
		print('\n')
	print('\n')
''' 

	
	
	
	
# need testing

def waitingListSearch(f, start, end):
	
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
		"code":1,
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
			"code":"$code",
			"recordTime":"$recordTime"
		},
		"List":{'$push':{"List":"$List"}}

	}},
	{'$project':{
		'_id':0,
		"code":"$_id.code",
		"recordTime":"$_id.recordTime",
		"List":"$List.List"

	}},
	#output to a new collection for later use
	{'$out':"allWithStatisfied"}
	],allowDiskUse=True
	)
	
	
	
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
			'let':{'time':"$MatchedrecordTime",'courseCode':"$_id"},
			'pipeline':[
				{'$match':
					{'$expr':
						{'$and':
							[
							{'$eq':["$code", "$$courseCode"]},
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
	{'$sort':{'_id':1}},
	{'$project':{'Course Code':'$_id','CourseTitle':1,'No Of credits':1,'Matched Time Slot':'$MatchedrecordTime',"SectionList.sectionId":1,"SectionList.dateAndTime":1,"SectionList.quota":1,"SectionList.enrol":1,"SectionList.Avail":1,"SectionList.wait":1,"SectionList.Satisfied":1,'_id':0}}
	])
	

	
	for items in results2:
		pprint.pprint(items)

	db.allWithStatisfied.drop()


def printAllMatched(matchedCourseDetails):
	for course in matchedCourseDetails:
		printACourseWS(course[1])



def printACourseWS(courseDetails):
	print('Course Code:', courseDetails[0])
	print('Course Title', courseDetails[1])
	print('No. of Units/Credits', courseDetails[2])
	print('Matched Time Slot', courseDetails[-1])
	for section in courseDetails[6]:
		print('\nSection Details: ')
		print('\tSection', section[0])
		print('\tDate & Time', section[1])
		print('\tQuota', section[4])
		print('\tEnrol', section[5])
		print('\tAvail', section[6])
		print('\tWait', section[7])
		print('\tSatisfied', section[9])
		print('\n')
	print('\n')

# offerings = {cid : [courseDetails]}
# sectionDetails = [Section Num, DateTime, Room, Instructor, Quota, Enrol, Avail, Wait, Remarks]
# courseDetails = [CourseCode, Course Title, Credits, [Pre-re(Course Code)], [Exclusion(Course Code], Course Descr, [[sectionDetails](s)]]
courseOfferings = {'COMP4332L1':
					   ['COMP4332', 'Big Data Mining and Management', 3,[], [], "This is a big data course that teaches problem solving",
						[['L1', '2018-02-01 15:30', 'G010', 'Prof Raymond', 100, 51, 49, 0,'can take' ]]],
				   'RMBI4310L1':
					   ['RMBI4310', 'Advanced Data Mining for Risk Management and Business Intelligence', 3,[], [], "This is a big data course that teaches problem solving",
						[['L1', '2018-02-01 15:30', 'G010', 'Prof Raymond', 100, 52, 48, 0,'can take' ]]],
				   'COMP4333L1':
					   ['COMP4333', 'Big Data Mining and Management', 3,[], [], "This is a big data course that teaches problem solving",
						[['L1', '2018-02-01 15:30', 'G010', 'Prof Raymond', 100, 51, 49, 0,'can take' ]]]
				   }
courses = ["COMP4332" , "ELEC1010", "COMP3221", "Big Data Management", "Dumb Data", "sth"]
#courses = courseOfferings.keys()

# 5.4
def waitingListSizePrediction(cc, ln, ts):
	#print("The predicted waiting list size of", cc, "Lecture", ln, "in", ts, "is \n")
	#print("1, 3, 5, 8, 12")
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
			
		#flip array 2 and 3
		model2array = model2array[::-1]
		model3array = model3array[::-1]
		
		model1array = numpy.array(model1array)
		model2array = numpy.array(model2array)
		model3array = numpy.array(model3array)
		model1array = model1array.reshape(1,3)
		model2array = model2array.reshape(1,2)
		model3array = model3array.reshape(1,3)
		
		numpy.savetxt("model1input.csv", model1array, delimiter=",")
		numpy.savetxt("model2input.csv", model2array, delimiter=",")
		numpy.savetxt("model3-5input.csv", model3array, delimiter=",")
		
		#first model prediction
		with open('model1.json', "r") as f:
			model_json = f.read()
		model = model_from_json(model_json)
		model.load_weights('model1.h5')
		newX = numpy.loadtxt('model1input.csv', delimiter=",")
		newX = newX.reshape(1,3)
		newY1 = model.predict(newX, batch_size=50)
		newY1 = newY1.reshape(1)


		#second model prediction
		with open('model2.json', "r") as f:
			model_json = f.read()
		model = model_from_json(model_json)
		model.load_weights('model2.h5')
		newX = numpy.loadtxt('model2input.csv', delimiter=",")
		newX = newX.reshape(1,2)
		newY2 = model.predict(newX, batch_size=5)
		newY2 = newY2.reshape(1)


		#third model prediction
		with open('model3.json', "r") as f:
			model_json = f.read()
		model = model_from_json(model_json)
		model.load_weights('model3.h5')
		newX = numpy.loadtxt('model3-5input.csv', delimiter=",")
		newX = newX.reshape(1,3)
		newY3 = model.predict(newX, batch_size=50)
		newY3 = newY3.reshape(1)


		#fourth model prediction
		with open('model4.json', "r") as f:
			model_json = f.read()
		model = model_from_json(model_json)
		model.load_weights('model4.h5')
		newX = numpy.loadtxt('model3-5input.csv', delimiter=",")
		newX = newX.reshape(1,3,1)
		newY4 = model.predict(newX, batch_size=50)
		newY4 = newY4.reshape(1)


		#fifth model prediction
		with open('model5.json', "r") as f:
			model_json = f.read()
		model = model_from_json(model_json)
		model.load_weights('model5.h5')
		newX = numpy.loadtxt('model3-5input.csv', delimiter=",")
		newX = newX.reshape(1,3,1)
		newY5 = model.predict(newX, batch_size=50)
		newY5 = newY5.reshape(1)

		
		print('predicted values of model 1-5:')
		print(int(newY1),',',int(newY2),',',int(newY3),',',int(newY4),',',int(newY5))
		
		db.earlierDocuments.drop()
# 5.5
def  waitingListSizeTraining():


	#get all needed records
	'''
	results=db.courses.aggregate([{'$unwind':"$sections"},
	{'$match': {'$or': [{'code': {'$regex': re.compile('^COMP1942', re.IGNORECASE)}}, {'code': {'$regex': re.compile('^COMP42', re.IGNORECASE)}},{'code': {'$regex': re.compile('^COMP43', re.IGNORECASE)}},{'code': {'$regex': re.compile('^RMBI', re.IGNORECASE)}}] }},
	{'$project':{'code':1,'semester':1,'title':1,'credits':1,'recordTime':'$sections.recordTime','sectionId':'$sections.sectionId','quota':'$sections.quota','enrol':'$sections.enrol','wait':'$sections.wait','_id':0}}])

	for item in results:
		break
	keys = item.keys()
	with open('record.csv', 'w') as output_file:
		dict_writer = csv.DictWriter(output_file, keys)
		dict_writer.writeheader()
		dict_writer.writerows(results)
	'''
	
	#get credits, quota, enrol and wait for model 1
	'''
	results2=db.courses.aggregate([{'$unwind':"$sections"},
	{'$match': {'$or': [{'code': {'$regex': re.compile('^COMP1942', re.IGNORECASE)}}, {'code': {'$regex': re.compile('^COMP42', re.IGNORECASE)}},{'code': {'$regex': re.compile('^COMP43', re.IGNORECASE)}},{'code': {'$regex': re.compile('^RMBI', re.IGNORECASE)}}] }},
	{'$project':{'credits':1,'quota':'$sections.quota','enrol':'$sections.enrol','wait':'$sections.wait','_id':0}}])
	
	for item in results2:
		break
	keys = item.keys()
	with open('firstTrain.csv', 'w') as output_file:
		dict_writer = csv.DictWriter(output_file, keys)
		#dict_writer.writeheader()
		dict_writer.writerows(results2)
	
	#shuffler('firstTrain.csv','firstTrainShuffled.csv')
	'''
	
	
	#get wait number with lookback=2 for model 2
	'''
	results3=db.courses.aggregate([{'$unwind':"$sections"},
	{'$match': {'$or': [{'code': {'$regex': re.compile('^COMP1942', re.IGNORECASE)}}, {'code': {'$regex': re.compile('^COMP42', re.IGNORECASE)}},{'code': {'$regex': re.compile('^COMP43', re.IGNORECASE)}},{'code': {'$regex': re.compile('^RMBI', re.IGNORECASE)}}] }},
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

	numpy.savetxt("secondTrain.csv", waitArray, delimiter=",")
	'''
	
	
	#get wait number with lookback=3 for model 3,4,5
	'''
	results4=db.courses.aggregate([{'$unwind':"$sections"},
	{'$match': {'$or': [{'code': {'$regex': re.compile('^COMP1942', re.IGNORECASE)}}, {'code': {'$regex': re.compile('^COMP42', re.IGNORECASE)}},{'code': {'$regex': re.compile('^COMP43', re.IGNORECASE)}},{'code': {'$regex': re.compile('^RMBI', re.IGNORECASE)}}] }},
	{'$project':{'sectionId':'$sections.sectionId','code':1,'wait':'$sections.wait','_id':0}},
	{'$match': {'sectionId': {'$regex': re.compile('^L.', re.IGNORECASE)}}},
	{'$project':{'sectionId':1,'code':1,'wait':1,'_id':0}}])

	temp = []
	codes = []
	sectionIds = []
	waits = []

	for items in results4:
		codes.append(str(items['code']))
		sectionIds.append(str(items['sectionId']))
		waits.append(int(items['wait']))
		
	for i in range(2,len(codes)):
		if codes[i]==codes[i-1] and codes[i]==codes[i-2] and codes[i]==codes[i-3] and sectionIds[i]==sectionIds[i-1] and sectionIds[i]==sectionIds[i-2] and sectionIds[i]==sectionIds[i-3]:
			temp.append(waits[i-3])
			temp.append(waits[i-2])
			temp.append(waits[i-1])
			temp.append(waits[i])
		
	waitArray = numpy.array(temp)
	waitArray = waitArray.reshape(int(len(temp)/4),4)

	numpy.savetxt("thirdTrain.csv", waitArray, delimiter=",")
	'''
	
	
	#model 1
	'''
	print('training model 1')
	numpy.random.seed(int(time.time()))
	dataset = numpy.loadtxt('firstTrain.csv', delimiter=",")
	X = dataset[:,0:3]
	Y = dataset[:,3]
	model = Sequential()
	model.add(Dense(12, input_dim=3, activation='relu'))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='relu'))
	keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)#, amsgrad=False)
	model.compile(loss="mae", optimizer="adam", metrics=["accuracy"])
	#earlyStopping=keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')
	model.fit(X, Y, validation_split=0.2, epochs=150, batch_size=50)#, callbacks=[earlyStopping])
	scores = model.evaluate(X, Y)
	print("")
	print("{}: {}".format(model.metrics_names[1], scores[1]*100))
	model_json = model.to_json()
	with open('model1.json', "w") as f:
	    f.write(model_json)
	model.save_weights('model1.h5')
	'''

	#model 2
	'''
	print('training model 2')
	numpy.random.seed(int(time.time()))
	dataset = numpy.loadtxt('secondTrain.csv', delimiter=",")
	X = dataset[:,0:2]
	Y = dataset[:,2]
	model = Sequential()
	model.add(Dense(12, input_dim=2, activation='relu'))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='relu'))
	keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)#, amsgrad=False)
	model.compile(loss="mse", optimizer="adam", metrics=["accuracy"])
	#earlyStopping=keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')
	model.fit(X, Y, validation_split=0.2, epochs=150, batch_size=5)#, callbacks=[earlyStopping])
	scores = model.evaluate(X, Y)
	print("")
	print("{}: {}".format(model.metrics_names[1], scores[1]*100))
	model_json = model.to_json()
	with open('model2.json', "w") as f:
	    f.write(model_json)
	model.save_weights('model2.h5')
	'''
	
	#model 3
	'''
	print('training model 3')
	numpy.random.seed(int(time.time()))
	dataset = numpy.loadtxt('thirdTrain.csv', delimiter=",")
	X = dataset[:,0:3]
	Y = dataset[:,3]
	model = Sequential()
	model.add(Dense(12, input_dim=3, activation='relu'))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='relu'))
	keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)#, amsgrad=False)
	model.compile(loss="mae", optimizer="adam", metrics=["accuracy"])
	#earlyStopping=keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')
	model.fit(X, Y, validation_split=0.2, epochs=150, batch_size=50)#, callbacks=[earlyStopping])
	scores = model.evaluate(X, Y)
	print("")
	print("{}: {}".format(model.metrics_names[1], scores[1]*100))
	model_json = model.to_json()
	with open('model3.json', "w") as f:
	    f.write(model_json)
	model.save_weights('model3.h5')
	'''
	
	#model 4
	'''
	print('training model 4')
	numpy.random.seed(int(time.time()))
	dataset = numpy.loadtxt('thirdTrain.csv', delimiter=",")
	X = dataset[:,0:3]
	X = X.reshape(9834,3,1)
	Y = dataset[:,3]
	model = Sequential()
	model.add(LSTM(10, input_shape=(3,1)))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='relu'))
	keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)#, amsgrad=False)
	model.compile(loss="mae", optimizer="adam", metrics=["accuracy"])
	#earlyStopping=keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')
	model.fit(X, Y, validation_split=0.2, epochs=150, batch_size=50)#, callbacks=[earlyStopping])
	scores = model.evaluate(X, Y)
	print("")
	print("{}: {}".format(model.metrics_names[1], scores[1]*100))
	model_json = model.to_json()
	with open('model4.json', "w") as f:
	    f.write(model_json)
	model.save_weights('model4.h5')
	'''
	
	#model 5
	'''
	print('training model 5')
	numpy.random.seed(int(time.time()))
	dataset = numpy.loadtxt('thirdTrain.csv', delimiter=",")
	X = dataset[:,0:3]
	X = X.reshape(9834,3,1)
	Y = dataset[:,3]
	model = Sequential()
	model.add(GRU(10, input_shape=(3,1)))
	model.add(Dense(8, activation='relu'))
	model.add(Dense(1, activation='relu'))
	keras.optimizers.Adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0)#, amsgrad=False)
	model.compile(loss="mae", optimizer="adam", metrics=["accuracy"])
	#earlyStopping=keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0, patience=0, verbose=0, mode='auto')
	model.fit(X, Y, validation_split=0.2, epochs=150, batch_size=50)#, callbacks=[earlyStopping])
	scores = model.evaluate(X, Y)
	print("")
	print("{}: {}".format(model.metrics_names[1], scores[1]*100))
	model_json = model.to_json()
	with open('model5.json', "w") as f:
	    f.write(model_json)
	model.save_weights('model5.h5')
	'''
	
	print("Waiting list size training is successful")

	
	













	
		

	
	

	

if __name__ =='__main__':
	#testDbConnection()
	#testing()
	main()
	

client.close()
