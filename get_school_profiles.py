import os
import sys
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

def academic_crawler(name):
	div = soup.find('div', id=name)
	if div == None:
		return None, {}
	else:
		try:
			rating = div.find('div', class_='col-xs-12 col-md-8').get_text().strip().split('/')[0]
		except:
			rating = None
		test = div.find_all('div', class_='test-score-container clearfix')
		d = {}
		for i in test:
			subject = i.find('div', class_='col-xs-12 col-sm-5 subject').get_text().strip()
			if 'Grade' in subject:
				continue
			subject = subject.replace(' ', '_')
			subject = 'Academic:' + div['id'].split('-react-component')[0] +':' + subject
			score = i.find('div', class_='score').get_text()
			d.update({subject:score})
		return rating, d

def equity_dict(html_source):
	soup = BeautifulSoup(html_source, 'html.parser')
	d = {}
	test = soup.find_all('div', class_='test-score-container clearfix')
	for i in test:
		try:
			subject = i.find('div', class_='col-xs-12 col-sm-5 subject').get_text().strip().split('(')[0].strip()
		except:
			continue
		if 'Grade' in subject:
			continue
		score = i.find('div', class_='score').get_text().strip()
		d.update({subject:score})
	return d

cwd = os.path.dirname(os.path.realpath(__file__))

hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
	   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
	   'Accept-Encoding': 'none',
	   'Accept-Language': 'en-US,en;q=0.8',
	   'Connection': 'keep-alive'
}

options = webdriver.ChromeOptions()
prefs = {"profile.managed_default_content_settings.images": 2}
options.add_experimental_option("prefs", prefs)

URLS = []
with open(os.path.join(cwd, 'source', sys.argv[1]+'_schools.txt')) as f:
	lines = f.readlines()
	for line in lines:
		URLS.append(line.split('|')[1].strip())

df_profile = pd.DataFrame()
row = -1

for url in URLS:
	row += 1
	
	driver = webdriver.Chrome(os.path.join(cwd, 'chromedriver'), chrome_options=options)
	driver.set_page_load_timeout(600)
	driver.get(url)
	rsps = driver.page_source
	soup = BeautifulSoup(rsps, 'html.parser')
	
	# Basic info
	school_id = url.split('/')[-2].split('-')[0]
	df_profile.loc[row, 'ID'] = school_id
	print(school_id)
	
	try:
		div = soup.find('div', id='hero')
		s_num = div.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['school-info__item'])[1]\
				.get_text()\
				.strip()\
				.split('\n')[1]\
				.replace(',', '')
		df_profile.loc[row, 'Student_No'] = s_num
		p = div.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['school-info__item'])[2]\
				.get_text()\
				.strip()\
				.split('\n')[1]
		df_profile.loc[row, 'Type'] = p
	except:
		print('ERROR: Even no basic info...')
	
	if 'Public' in p:
		try:
			overall_rating = div.find('div', class_='gs-rating-with-label__rating').get_text().strip().split('/')[0]
			df_profile.loc[row, 'Overall_Rating'] = overall_rating
		except:
			print('ERROR: No Rating...')
		
	# Test Scores
		rating, d = academic_crawler('TestScores')
		df_profile.loc[row,'Academic_TestScore_Rating'] = rating
		for k in d.keys():
			df_profile.loc[row,k] = d[k]
		
	# College Readiness
		rating, d = academic_crawler('CollegeReadiness')
		df_profile.loc[row,'Academic_CollegeReadiness_Rating'] = rating
		for k in d.keys():
			df_profile.loc[row,k] = d[k]
		
	# Student Progress (possibly missing)
		rating, d = academic_crawler('StudentProgress')
		df_profile.loc[row,'Academic_StudentProgress_Rating'] = rating
		for k in d.keys():
			df_profile.loc[row,k] = d[k]
		
	# Advanced STEM Cources (possibly missing)
		rating, d = academic_crawler(re.compile(r'^StemCourses-react-component'))
		for k in d.keys():
			df_profile.loc[row,k] = d[k]
			
	# Race/Ethnicity
		try:
			race = driver.find_element_by_xpath("//div[@id='EquityRaceEthnicity']")
			tabs = race.find_elements_by_xpath("//a[@data-ga-click-action='Equity Race/ethnicity Tabs']")
			for t in tabs:
				location = t.location["y"] - 100
				driver.execute_script("window.scrollTo(0, %d);" %location)
				t.click()
				tab_name = t.text.replace(' ', '_')
				sub_tab_group = race.find_element_by_class_name('sub-nav-group')
				sub_tabs = sub_tab_group.find_elements_by_css_selector("*")
				for s in sub_tabs:
					location = s.location["y"] - 100
					driver.execute_script("window.scrollTo(0, %d);" %location)
					s.click()
					sub_tab_name = s.text.replace(' ', '_')
					html_source = race.get_attribute('innerHTML')
					d = equity_dict(html_source)
					for k in d.keys():
						df_profile.loc[row, 'Equity:Race:'+tab_name+':'+sub_tab_name+':'+k] = d[k]
		except:
			print('ERROR: No race info...')
		
	# Low-income Students
		try:
			lowincome = driver.find_element_by_xpath("//div[@id='EquityLowIncome']")
			tabs = lowincome.find_elements_by_xpath("//a[@data-ga-click-action='Equity Low-income students Tabs']")
			for t in tabs:
				location = t.location["y"] - 100
				driver.execute_script("window.scrollTo(0, %d);" %location)
				t.click()
				tab_name = t.text.replace(' ', '_')
				sub_tab_group = lowincome.find_element_by_class_name('sub-nav-group')
				sub_tabs = sub_tab_group.find_elements_by_css_selector("*")
				for s in sub_tabs:
					location = s.location["y"] - 100
					driver.execute_script("window.scrollTo(0, %d);" %location)
					s.click()
					sub_tab_name = s.text.replace(' ', '_')
					html_source = lowincome.get_attribute('innerHTML')
					d = equity_dict(html_source)
					for k in d.keys():
						df_profile.loc[row, 'Equity:Low-income:'+tab_name+':'+sub_tab_name+':'+k] = d[k]
		except:
			print('ERROR: No low-income info...')
		
	# Students with Disabilities
		try:
			disabilities = driver.find_element_by_xpath("//div[@id='EquityDisabilities']")
			tabs = disabilities.find_elements_by_xpath("//a[@data-ga-click-action='Equity Students with disabilities Tabs']")
			for t in tabs:
				location = t.location["y"] - 100
				driver.execute_script("window.scrollTo(0, %d);" %location)
				t.click()
				tab_name = t.text.replace(' ', '_')
				sub_tab_group = disabilities.find_element_by_class_name('sub-nav-group')
				sub_tabs = sub_tab_group.find_elements_by_css_selector("*")
				for s in sub_tabs:
					location = s.location["y"] - 100
					driver.execute_script("window.scrollTo(0, %d);" %location)
					s.click()
					sub_tab_name = s.text.replace(' ', '_')
					html_source = disabilities.get_attribute('innerHTML')
					d = equity_dict(html_source)
					for k in d.keys():
						df_profile.loc[row, 'Equity:Disabilities:'+tab_name+':'+sub_tab_name+':'+k] = d[k]
		except:
			print('ERROR: No low-income info...')
	
	# Students
	try:
		div = soup.find('div', id='Students', class_='students-container')
		race = div.find('div', class_='col-xs-12 col-sm-5')
		props = race.find_all('div', class_='legend-separator js-highlightPieChart clearfix')
		for p in props:
			r = p.find('div', style='float:left;').get_text()
			num = p.find('div', style='float: right').get_text()
			df_profile.loc[row,'Environment:Students:'+r] = num
	
		if 'Public' in p:
			other_stat = div.find_all('div', 'subgroup col-xs-6 col-sm-4 col-md-6 col-lg-4')
			for s in other_stat:
				title = s.find('div', class_='title').get_text().strip().replace(' ', '_')
				if title == 'Gender':
					title = 'Gender(Male)'
					num = s.find('div', class_='open-sans').get_text()
				else:
					num = s.find('tspan').get_text()
				df_profile.loc[row, 'Environment:Students:'+title] = num
			
		# Teacher Staff
			div = soup.find('div', id='TeachersStaff')
			rating_container = div.find_all('div', class_='rating-container__score-item')
			for r in rating_container:
				title = r.find('div', 'col-xs-6 rating-score-item__label').get_text().strip().replace(' ', '_')
				num = r.find('div', 'rating-score-item__score').get_text().strip().split('\n')[0]
				df_profile.loc[row, 'Environment:Teachers:'+title] = num
			bar_container = div.find_all('div', class_='row bar-graph-display')
			for b in bar_container:
				title = b.find('div', class_='col-xs-12 col-sm-5 subject').get_text().strip().replace(' ', '_')
				num = b.find('div', class_='score').get_text()
				df_profile.loc[row, 'Environment:Teachers:'+title] = num
	except:
		print('ERROR: No students & teacher info...')
	
	# Reviews
	try:
		div = driver.find_element_by_xpath("//div[@class='review-list']")
		try:
			show_more_button = WebDriverWait(div, 10)\
							   .until(EC.presence_of_element_located((By.XPATH,"//div[@class='show-more__button']")))
			location = show_more_button.location["y"] - 100
			driver.execute_script("window.scrollTo(0, %d);" %location)
			show_more_button.click()
		except:
			print('ERROR: Think too much, no more than 10 reviews...')
		
		html_source = div.get_attribute('innerHTML')
		div = BeautifulSoup(html_source, 'html.parser')
		reviews = div.find_all('div', class_='user-reviews-container')
		fh = open(os.path.join(cwd, 'reviews.txt'), 'a')
		for r in reviews:
			user_type = r.find('div', class_='user-type').get_text()
			comment = r.find('div', class_='comment').get_text().strip('\n')
			fh.write(school_id + '\t' + user_type + '\t' + comment + '\n')
		fh.close()
	except:
		print('ERROR: No reviews...')
	
	driver.close()

df_profile.to_csv(os.path.join(cwd, sys.argv[1] + '_school_profiles.txt'), header=True, index=False, sep='|')