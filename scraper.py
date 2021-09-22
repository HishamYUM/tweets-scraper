import csv
from getpass import getpass 
from time import sleep

from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By

def create_webdriver():
	# Using Google Chrome webdriver
	return webdriver.Chrome(ChromeDriverManager().install())

def login_to_twitter(username, password, driver):

	# Define login url
	login_url = 'https://twitter.com/login'
    
    # Go to login url
	driver.get(login_url)
	
	sleep(2)
	current_url = driver.current_url

	# Logic to take account for redirect to different login page
	if current_url == login_url:
		xpath_username = '//input[@name="session[username_or_email]"]'
		WebDriverWait(driver, 15).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_username)))
		uid_input = driver.find_element_by_xpath(xpath_username)
		uid_input.send_keys(username)

		pwd_input = driver.find_element_by_xpath('//input[@name="session[password]"]')
		pwd_input.send_keys(password)
		pwd_input.send_keys(Keys.RETURN)
		url = "https://twitter.com/home"
		WebDriverWait(driver, 10).until(expected_conditions.url_to_be(url))

	else:
		xpath_username = '//input[@name="username"]'
		WebDriverWait(driver, 15).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_username)))
		uid_input = driver.find_element_by_xpath(xpath_username)
		uid_input.send_keys(username)
		uid_input.send_keys(Keys.RETURN)

		xpath_password = '//input[@name="password"]'
		WebDriverWait(driver, 5).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_password)))
		pwd_input = driver.find_element_by_xpath(xpath_password)
		pwd_input.send_keys(password)

		try:
			pwd_input.send_keys(Keys.RETURN)
			url = "https://twitter.com/home"
			WebDriverWait(driver, 5).until(expected_conditions.url_to_be(url))

		except exceptions.TimeoutException:
			print("Timeout while waiting for home screen")
	
	return True

def search_tweets(search_term, driver):

	# Define xpath for searching tweets
	xpath_tweet_search = '//input[@aria-label="Search query"]'

	WebDriverWait(driver, 5).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_tweet_search)))
	
	search_input = driver.find_element_by_xpath(xpath_tweet_search)
	search_input.send_keys(search_term)
	search_input.send_keys(Keys.RETURN)

	return True

def change_twitter_tabs(tab_name, driver):
	
	# Sleep two seconds to wait page is fully loaded, then switch to 'Latest' tab
	sleep(2)
	driver.find_element_by_link_text(tab_name).click()


def scroll_down_page(driver, last_height, num_seconds_to_load=10, scroll_attempt=0, max_attempts=10):

	# By default we've not reached end of scroll region
	end_of_scroll_region = False

	# Scroll down to bottom
	driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # wait time to load
	sleep(num_seconds_to_load)

    # Calculate new scroll height and compare with last scroll height
	new_height = driver.execute_script("return document.body.scrollHeight")

    # break condition when the page can't be scrolled further
	if new_height == last_height:
		end_of_scroll_region = True

	# Set last height equal to new height
	last_height = new_height

	return last_height, end_of_scroll_region

def generate_tweet_id(tweet):

	# Generate a unique id for each tweet
	return ''.join(tweet)

def collect_all_tweets_from_current_view(driver, lookback_limit=25):
	
	# Return all tweets from current view 
	sleep(2)
	return driver.find_elements_by_xpath('//article[@data-testid="tweet"]')


def extract_tweet_data(tweet):

	# Extract tweet characterictics
	like_search = tweet.find_element_by_xpath('.//div[@data-testid="like"]').text
	reply_search = tweet.find_element_by_xpath('.//div[@data-testid="reply"]').text
	retweet_search = tweet.find_element_by_xpath('.//div[@data-testid="retweet"]').text

	# username 
	try:
		username = tweet.find_element_by_xpath('.//span').text
	except exceptions.NoSuchElementException:
		username = ""

	# post date of tweet
	try:
		timestamp = tweet.find_element_by_xpath('.//time').get_attribute('datetime') 
	except exceptions.NoSuchElementException:
		timestamp = ""

	# body content of tweet
	try:
		body = tweet.find_element_by_xpath('.//div[2]/div[2]/div[2]/div[2]/div').text
	except exceptions.NoSuchElementException:
		body = ""

	# like_count
	if like_search != '':
	    like_count = like_search
	else:
	    like_count = 0
	    
	# reply_count
	if reply_search != '':
	    reply_count = reply_search
	else:
	    reply_count = 0
	    
	# retweet_count
	if retweet_search != '':
	    retweet_count = retweet_search
	else:
		retweet_count = 0

	# Return tweet as a tuple
	return (username, timestamp, body, str(like_count), str(reply_count), str(retweet_count))

def save_tweets_to_csv(records, filepath, mode='a+'):

	# First define schema of the file
	schema = ['username', 'tweet_ts', 'tweet_text', 'like_count', 'reply_count', 'retweet_count']
	
	with open(filepath, mode=mode, newline='', encoding='utf-8') as f:
	    writer = csv.writer(f)
	    if mode == 'w':
	        writer.writerow(schema)
	    if records:
	    	writer.writerow(records)

## Main 
def main(username, password, search_term, file_path, tab_name='Latest'):
	save_tweets_to_csv(None, file_path, 'w')  # create file for saving records
	last_height = None
	end_of_scroll_region = False
	unique_tweets = set()

	# 1. Create driver
	driver = create_webdriver()

	# 2. Login to Twitter
	login = login_to_twitter(username, password, driver)
	if not login:
	    return

	# 3. Enter search_term for tweets
	search_found = search_tweets(search_term, driver)
	if not search_found:
	    return

	# 4. Change tabs to 'Latest'
	change_twitter_tabs(tab_name, driver)

	# 5. Scrape tweets
	while not end_of_scroll_region:
		tweets = collect_all_tweets_from_current_view(driver)
		for tweet in tweets:
			try:
				tweet_data = extract_tweet_data(tweet)
			except exceptions.StaleElementReferenceException:
				continue
			if not tweet:
				continue
			tweet_id = generate_tweet_id(tweet_data)
			if tweet_id not in unique_tweets:
				unique_tweets.add(tweet_id)
				save_tweets_to_csv(tweet_data, file_path)
		last_height, end_of_scroll_region = scroll_down_page(driver, last_height)

	driver.quit()

if __name__ == '__main__':
    username = "" 			# Fill in twitter username
    password = "" 			# Fill in twitter password
    file_path = ""			# Fill in file_path to save tweets
    search_query = ""		# Fill in search query for type of tweets

    main(username, password, search_query, file_path)
