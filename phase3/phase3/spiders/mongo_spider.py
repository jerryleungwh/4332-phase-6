import scrapy
import pymongo
from datetime import datetime
# import re # uncomment this line if you want to try out the simpler methods using regular expression

class MongoSpider(scrapy.Spider):
	name = 'mongo'
	mongo_uri = 'mongodb://localhost:27017'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		with open('url.txt', 'r') as f:
			url = f.read()
			self.start_urls = [ url ]
		self.client = pymongo.MongoClient(self.mongo_uri)
		self.db = self.client['hkust']

		# used as cache for database to check whether 
		# courses are already inserted 
		# you can also check from database directly
		self.inserted_courses = set()

	def parse(self, response):
		for a in response.xpath('//ul/li/a'):
			yield response.follow(a, callback=self.parse_snapshot)

	def parse_snapshot(self, response):
		for a in response.xpath('//div[@class="depts"]/a'):
			yield response.follow(a, callback=self.parse_dept)

	def parse_dept(self, response):
		title = response.xpath('//title/text()').extract_first()

		# ====== extract semester and time =========
		i = title.find(': Snapshot taken at ')
		semester = title[:i-5] # each dept has a length of 4
		time_str = title[i + len(': Snapshot taken at '):]
		year = int(time_str[:4])
		month = int(time_str[5:7])
		day = int(time_str[8:10])
		hour = int(time_str[11:13])
		minute = int(time_str[-2:])
		record_time = datetime(year, month, day, hour, minute)

		# simpler method using regular expression and strptime
		# m = re.search(r'(.*) \w+: Snapshot taken at (.*)', title)
		# semester = m.group(1)
		# record_time = datetime.strptime(m.group(2), '%Y-%m-%d %H:%M')
		# ==========================================

		# uncomment the following two lines if you want the progress to be displayed
		#dept = response.url[-9:-5]
		#print('Processing %s %s' % (time_str, dept))

		courses = response.xpath('//div[@class="course"]')
		for course in courses:
			self.parse_course(course, semester, record_time)

	def parse_course(self, el, semester, record_time):
		# extract_first() is the same as extract()[0]
		header = el.xpath('.//h2/text()').extract_first()
		i = header.find('-')
		j = header.rfind('(')
		k = header.rfind('unit')
		code = header[:i].replace(' ', '')
		if (code, semester) not in self.inserted_courses:
			course = {
				'code': code,
				'semester': semester
			}
			course['title'] = header[i+1:j].strip()
			course['credits'] = float(header[j+1:k])

			# ========== process 'COURSE INFO' ==============
			# the function fix_case removes '(', ')' , '-' and ' ' from the keys and
			# change them to camel case.
			# e.g., 'PRE-REQUISITE' -> 'prerequisite'
			# 'CO-LIST WITH' -> 'colistWith'
			# you can achieve the same goal using a sequence of 'if-else' statements
			# i.e., 
			# key = ' '.join(tr.xpath('.//th//text()').extract())
			# if key == 'PRE-REQUISITE':
			#     key = 'prerequisite'
			# elif key == 'CO-LIST WITH':
			#     key = 'colistWith'
			# ...
			for tr in el.xpath('.//div[contains(@class, "courseattr")]/div/table/tr'):
				key = self.fix_case(' '.join(tr.xpath('.//th//text()').extract()))
				value = '\t'.join([
					x.strip()
					for x in tr.xpath('.//td//text()').extract()
				])
				course[key] = value
			# =================================================

			self.inserted_courses.add((code, semester))
			self.db.courses.insert_one(course)
		self.parse_sections(el.xpath('.//table[@class="sections"]//tr')[1:], code, semester, record_time)

	def parse_sections(self, trs, code, semester, record_time):
		sections = []
		prev_sect = None
		for tr in trs:
			class_name = tr.xpath('./@class').extract_first()
			if 'newsect' in class_name:
				sectionId = tr.xpath('./td[1]/text()').extract_first().split('(', 1)[0].strip()
				section = {
					'recordTime': record_time,
					'sectionId': sectionId,
					'offerings': [
						{
							# most complicated case: 2016-17 Summer MGMT5410
							'dateAndTime': '\t'.join(tr.xpath('./td[2]/text()').extract()),
							'room': tr.xpath('./td[3]/text()').extract_first(),
							'instructors': tr.xpath('./td[4]/text()').extract()
						}
					],
					# the text may be inside its children
					# example: 2016-17 Spring ACCT5140 L1
					'quota': int(tr.xpath('./td[5]//text()').extract_first()),
					'enrol': int(tr.xpath('./td[6]//text()').extract_first()),
					# if avail is 0, it is enclosed by <strong>
					#'avail': int(tr.xpath('./td[7]//text()').extract_first()),
					'wait': int(tr.xpath('./td[8]//text()').extract_first())
				}
				remarks = '\t'.join([
					text.strip()
					for text in tr.xpath('./td[9]//text()').extract()
					if text.strip() != ''
				])
				if remarks != '':
					section['remarks'] = remarks
				sections.append(section)
				prev_sect = section
			else:
				offering = {
					# index starts from 1
					# TODO: split dateAndTime to daysOfWeek and time
					'dateAndTime': ' '.join(tr.xpath('./td[1]/text()').extract()),
					'room': tr.xpath('./td[2]/text()').extract_first(),
					'instructors': tr.xpath('./td[3]/text()').extract()
				}
				prev_sect['offerings'].append(offering)

		self.db.courses.update_one(
			{ 'code': code, 'semester': semester },
			{ '$push': {
					'sections': {
						'$each': sections
					}
				}
			}
		)

	def closed(self, reason):
		self.client.close()
		print('Data Crawling is successful and all data are inserted into the database')

	def fix_case(self, key):

		# ======= remove characters '(', ')' and '-' ===========
		s = key.translate({ord(c): '' for c in '()-'})
		# using regular expression
		#s = re.sub(r'[()-]', '', key)
		# ======================================================
		
		res = s.title().replace(' ', '')
		return res[0].lower() + res[1:]
