#!/usr/bin/python3

import os
import sys
import time
from random import randint
from multiprocessing import Pool

import numpy as np
import requests
from bs4 import BeautifulSoup
import MySQLdb

from selenium import webdriver
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

thread_num = 5
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

cwd = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(cwd, 'chromedriver')
DOWNLOAD_DIR = os.path.join(cwd, 'downloads')
# db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="redfin", charset="utf8")
# cur = db.cursor()
hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 'Accept-Encoding': 'none','Accept-Language': 'en-US,en;q=0.8','Connection': 'keep-alive'}

options = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2, "download.default_directory" : DOWNLOAD_DIR}
options.add_experimental_option("prefs", prefs)
# options.add_argument("download.default_directory=" + DOWNLOAD_DIR)

# base_url = "https://www.redfin.com"
base_url = "https://www.redfin.com/school/108854/IL/Elk-Grove-Village/Elk-Grove-High-School/filter/property-type=house+condo+townhouse,include=forsale+mlsfsbo+construction+fsbo+foreclosed+sold-3mo"

def get_properties(info):#,proxy):
	state, school_city, school_id, school_name = info
	driver = webdriver.Chrome(os.path.join(cwd, 'chromedriver'), chrome_options=options)
	driver.set_page_load_timeout(600)
	driver.get(base_url)
	time.sleep(5)

	try:
		q = school_name + " " + state.upper() + "\n"
		print(school_name)
		driver.find_element_by_name("searchInputBox").send_keys(q)
		time.sleep(randint(2,5))
		
		link = driver.current_url
		link2 = link.replace("https://www.redfin.com/school/", "")
		region_id = link2.split("/")[0].strip()
		print(region_id)

		#proxies = {"http":"%s" % proxy}
		#proxy_support = urllib3.ProxyHandler(proxies)
		#opener = urllib3.build_opener(proxy_support, urllib3.HTTPHandler(debuglevel=1))
		#urllib3.install_opener(opener)
		req = requests.get(link, headers=hdr)
		source = req.text
		soup = BeautifulSoup(source, "lxml")
		show_tag = soup.find("div", {"class": "homes summary"})
		text = show_tag.getText().strip().lower()
		if text == 'showing 0 homes':
			return

		# get the link to download all
		url = "https://www.redfin.com/stingray/api/gis-csv?al=1&market=dc&num_homes=350&ord=price-asc&page_number=1&region_id="+region_id+"&region_type=7&sf=1,2,3,4,5,6,7&sold_within_days=180&sp=true&status=9&uipt=1,2,3&v=8"
		print(url)
		
		driver.get(url)
		time.sleep(3)
		fnames = os.listdir(DOWNLOAD_DIR)
		fname = ""
		new_fname = ""
		for f in fnames:
			if os.path.splitext(f)[1] == ".csv" and f.startswith("redfin"):
				fname = os.path.join(DOWNLOAD_DIR, f)
				new_fname = os.path.join(DOWNLOAD_DIR, state + "_" + school_id + ".csv")
				break
		os.rename(fname, new_fname)
	except:
		print("ERRORS......")
		with open(os.path.join(cwd, 'exceptions.txt'), 'a') as f:
			f.write(state + '|' + school_city + '|' + school_id + '|' + school_name + '\n')
	print("\n")
	time.sleep(randint(10,30))
	driver.close()
	# db.close()

def assign(thread):
	if thread == thread_num - 1:
		temp_list = source_list[thread * trunk:]
	else:
		temp_list = source_list[thread * trunk : (thread+1) * trunk]

	for i in temp_list:
		print("Processing:", temp_list[2], ",", temp_list[1])
		if os.path.exists(os.path.join(DOWNLOAD_DIR, state + "_" + school_id + ".csv")):
			continue
		get_properties(i)

if __name__ == "__main__":
	school_file = sys.argv[1]
	state = sys.argv[2]
	start = int(sys.argv[3])

	#valid_proxy_file = sys.argv[4]

	#fh = open(valid_proxy_file,'r')
	#proxies = fh.readlines()
	#fh.close()

	fh = open(school_file, 'r')
	rows = fh.readlines()
	fh.close()

	source_list = []
	for i in range(start, len(rows)):
		arr = rows[i-1].strip().split("|")
		school_id = arr[0].strip()
		school_name = arr[2].strip()
		school_city = arr[3].strip().split(",")[-2].strip()
		source_list.append([state, school_city, school_id, school_name])

		# p = np.random.randint(len(proxies))
		# proxy = proxies[p].strip()
		# print proxy
		# get_properties(state,school_city,school_id,school_name)#,proxy)
	trunk = int(len(source_list)/thread_num)
	p = Pool(thread_num)
	p.map(assign, range(thread_num))
