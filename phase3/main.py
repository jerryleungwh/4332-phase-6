import subprocess

def main():
	url = input('Please enter a URL for data crawling: ')
	if url == 'default':
		url = 'http://comp4332.com/realistic'
	with open('url.txt', 'w') as f:
		f.write(url)
	subprocess.run('scrapy crawl mongo', shell=True)
	# We use a file to pass URL, but you can use other methods.
	# A commonly used method is to pass the start_urls using the '-a' argument
	# If interested, you can refer to https://stackoverflow.com/a/15291961

if __name__ == '__main__':
	main()
