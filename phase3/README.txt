a. To run this program, you can run either
python main.py
or
scrapy crawl mongo


=======================================

b. Process to create this project

1. scrapy startproject phase3

2. cd phase3

3. add the following lines to phase3/settings.py
# log to file instead of the console.
LOG_FILE = 'log.txt'

# only log error messages, ignore irrelevant messages
# to know more about log levels, see https://doc.scrapy.org/en/latest/topics/logging.html#log-levels
LOG_LEVEL = 'ERROR'

# does not redirect standard output to the log file
# i.e., we want the output from the print() method is shown in the console
LOG_STDOUT = False

4. write "phase3/spiders/mongo_spider.py" (i.e., place "mongo_spider.py" found in the zipped file to 
   folder "phase3/spiders")

5. keep all other files (i.e., __init__.py, items.py, middlewares.py, pipelines.py) unchanged.
