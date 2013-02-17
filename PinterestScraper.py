# PinterestScraper.py
# Author: Erika Ellison
# Version: .8
#
# A web scraper that creates a local copy of your (or anyone else's!) public Pinterest boards.
#
# Right now this works on the command line if Python2.x is installed, so I'm considering it finished, even though could use the following improvements:
#		optimize regexes that search for three main "pin" attributes (super easy)
#		refactor to make use of threading - run time could be improved if multiple HTTP GET requests ran in parallel
#		refactor - turn this messy big class into multiple smaller classes
#		make a simple GUI for it and export to an executable

import sys
import os
import urllib2
import re
import time

verbose = False
main = False

for arg in sys.argv:
	if arg == 'verbose':
		verbose = True
		
if __name__ == '__main__':
	main = True


class PinterestScraperError(Exception):
	pass

class PinterestScraper(object):
	"a web crawler/scraper that creates a local copy of a Pinterest user's images and the captions and URLs the images are associated with"
	
	# constants
	BASE_URL = 'http://pinterest.com'
	HTTP_SUCCESS = 200
	
	def __init__(self, username, download_folder):
		"initialize the scraper with username and download_folder"
		self.username = username
		self.download_folder = download_folder
		self.scrape_folder = 'PinterestData'
		if verbose:
			print 'Preparing to scrape {0}\'s PinterestData into folder {1}...'.format(self.username, self.download_folder)
		
		
		
	def getAllData(self):
		"gets full-size images and the captions and URLs associated with them"
		
		# create the folder where local copies of boards and pins will be saved
		self.createDownloadFolder()
		
		# scrape the user's main profile page to get names and urls for each board
		board_urls = self.getBoards()
		
		# for each board, create a folder, an index HTML file for the folder, and scrape the board's contents into the folder
		for board_url in board_urls:
			board_name = board_url[len(self.username)+2:-1]
			if verbose:
				print 'Preparing to scrape board {0}...'.format(board_name)
			board_folder = os.path.join(self.download_folder, self.scrape_folder, self.username, board_name)
			try:
				os.mkdir(board_folder)
			except OSError as e:
				pass # do something more robust later
			index_file = os.path.join(board_folder, 'index.html')
			index_html = open(index_file, 'w')
			html_prefix = '<html><head><title>' + board_name + '</title></head><body><h1>' + board_name + '</h1>'
			index_html.write(html_prefix)
			self.scrapeBoard(board_url, board_folder, index_html)
			html_suffix = '</body><html>'
			index_html.write(html_suffix)
			index_html.close()
		
		
	def createDownloadFolder(self):
		"creates a local folder as a child of the download_folder given in initialization, where all scraped Pinterest data will be stored"
		try:
			os.mkdir(os.path.join(self.download_folder, self.scrape_folder))
		except OSError as e: # will be thrown when download_folder/PinterestData exists already
			pass # do something more robust later
		
		try:
			os.mkdir(os.path.join(self.download_folder, self.scrape_folder, self.username))
		except OSError as e: # will be thrown when download_folder/PinterestData/[USERNAME] exists already
			pass # do something more robust later



	def getBoards(self):
		"scrapes a Pinterest user's main profile page and returns a list of urls of all of their pin boards"
		board_urls = [] # list to be returned
		
		if verbose:
			print '    retrieving the list of boards...'
		# retrieve the profile contents
		profile_contents = self.requestPage(self.BASE_URL + '/' + self.username)
		
		# parse the profile contents for the board names: <h3 class="serif"><a href="/[USERNAME]/[BOARD RELATIVE URL]/">[BOARD NAME]</a></h3>		
		board_pattern = re.compile(r'<h3 class="serif"><a href="/' + self.username + r'/.*?</a></h3>')
		all_boards = re.findall(board_pattern, profile_contents)
		url_pattern = re.compile(r'/' + self.username + '/.*?/')
		for board in all_boards:
			url = (re.search(url_pattern, board)).group(0)
			board_urls.append(url)
		
		# return the list of board urls
		return board_urls



	def scrapeBoard(self, board_url, board_folder, index_html):
		"scrapes a Pin Board - downloads all full size images, and their associated caption texts and original URLs (if any)"
		
		if verbose:
			print '    retrieving a list of pins from board {0}'.format(board_url)
		
		# retrieve the board contents
		board_contents = self.requestPage(self.BASE_URL + board_url)
		
		# parse the board contents for the pin links
		pin_pattern = re.compile(r'<a href="/pin/\d*/" class="PinImage ImgLink">')
		all_pins = re.findall(pin_pattern, board_contents)
		pin_urls = []
		for pin in all_pins:
			url_pattern = re.compile(r'/pin/\d*/')
			url = (re.search(url_pattern, pin)).group(0)
			pin_urls.append(url)

		# scrape each pin
		pin_number = 0
		digit_width = len(str(len(pin_urls)))
		for pin_url in pin_urls:
			self.scrapePin(pin_url, board_folder, index_html, pin_number, digit_width)
			pin_number += 1

			
			
	def scrapePin(self, pin_url, board_folder, index_html, pin_number, digit_width):
		"scrapes a pin into the folder of board, and adds the information about the pin to the board HTML file"
		
		if verbose:
			print '        scraping {0} into board {1}'.format(pin_url, board_folder)
		
		# retrieve the pin content page
		pin_contents = self.requestPage(self.BASE_URL + pin_url)
			
		# parse the pin contents for the image, the caption, and the original link (if any)
		description_pattern = re.compile(r'"og:description".*?/>', re.DOTALL)
		image_pattern = re.compile(r'og:image.*?/>', re.DOTALL)
		source_pattern = re.compile(r'og:see_also.*?/>', re.DOTALL)
		content_pattern = re.compile(r'content=".*?"')
		
		description_match = re.search(description_pattern, pin_contents)
		description = ''
		if description_match:
			content_match = re.search(content_pattern, description_match.group(0))
			if content_match:
				description = (content_match.group(0))[9:-1]
		
		image_match = re.search(image_pattern, pin_contents)
		image_url = ''
		if image_match:
			content_match = re.search(content_pattern, image_match.group(0))
			if content_match:
				image_url = (content_match.group(0))[9:-1]
		
		source_match = re.search(source_pattern, pin_contents)
		source_url = ''
		if source_match:
			content_match = re.search(content_pattern, source_match.group(0))
			if content_match:
				source_url = (content_match.group(0))[9:-1]
			
		if not image_url:
			return
		
		ext = image_url[-4:]
		filename = ('%0*d' % (digit_width, pin_number)) + ext
		image = self.requestPage(image_url)
		outfile = open(os.path.join(board_folder, filename), 'wb')
		outfile.write(image)
		outfile.close()
		pin_info = '<p><img src="' + filename + '" /><br />' + description 
		if source_url:
			pin_info += '<br /><a href="' + source_url + '">original source</a>'
		pin_info += '</p>'
		index_html.write
		
		

	def requestPage(self, url):
		"given a URL, return the resource's contents"
		data = None
		headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:12.0) Gecko/ 20120405 Firefox/14.0.1'}
		request = urllib2.Request(url, data, headers)
		http_response = urllib2.urlopen(request)
		if not http_response.getcode() == self.HTTP_SUCCESS:
			raise PinterestScraperError(url + ' couldn\'t be opened. HTTP error code: ' + http_response.getcode())
		contents = http_response.read()
		return contents


	
if main:
	if len(sys.argv) < 3:
		print 'Usage: python PinterestScraper.py <pinterest_username> <download_folder>'
		quit()
	
	url = sys.argv[1]
	download_folder = sys.argv[2]
	ps = PinterestScraper(url, download_folder)
	start = time.time()
	ps.getAllData()
	end = time.time()
	print 'time elapsed: {0}'.format(end - start)
