from datetime import datetime
import logging
import logging.config
from random import randint
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        ElementNotInteractableException,
                                        StaleElementReferenceException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
import json
import math
import os

formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

fh = logging.FileHandler("scraper.log", mode="w")
fh.setFormatter(formatter)
fh.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)

logger = logging.getLogger("scraper")
logger.setLevel(logging.INFO)
logger.addHandler(ch)
logger.addHandler(fh)


def random_wait():
    sleep(randint(1, 3))


def wait_for_element_update(driver, timeout, xpath, ref_element):
    start_time = datetime.now()

    while True:
        if (datetime.now() - start_time).total_seconds() > timeout:
            raise "Element at '%s' did not update within specified timeout"

        try:
            element = driver.find_element_by_xpath(xpath)
            if not element == ref_element:
                return
            logger.debug("Waiting for %s to change", xpath)
            sleep(0.1)
        except Exception as e:
            logger.error(e)
            return


def wait_for_element(driver, timeout, xpath):
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath)))


def search_lyrics(driver, query):
    X_SEARCH_INPUT = "//form[@action='/search']//input[@name='q']"
    X_SEARCH_BUTTON = "//form[@action='/search']//input[@type='submit']"
    driver.get("https://google.com")
    wait_for_element(driver, 3, X_SEARCH_INPUT)

    search_input = driver.find_element_by_xpath(X_SEARCH_INPUT)
    search_button = driver.find_element_by_xpath(X_SEARCH_BUTTON)
    
    search_input.send_keys(query)
    search_input.send_keys(Keys.RETURN)

    X_SEARCH_RESULTS = "//div[@id='search']"
    X_LYRICS_CONTAINER = "//div[@data-lyricid]"
    X_SHOW_MORE = "//*[contains(text(), 'Show more')]"
    wait_for_element(driver, 3, X_LYRICS_CONTAINER)
    lyrics_div = driver.find_element_by_xpath(X_LYRICS_CONTAINER)
    more_link = driver.find_element_by_xpath(X_SHOW_MORE)
    
    if more_link is not None:
        more_link.click()
        sleep(1)
        return lyrics_div.text

    return None


if __name__ == "__main__":
    CURRENT_DATE = datetime.utcnow().strftime("%Y-%m-%d")
    start_time = datetime.now()

    logger.info("Starting selenium session")
    lyrics_csv = os.getenv("SONG_TSV", "conductor-20k-redflag-violence.txt")
    output_dir = os.getenv("OUTPUT_DIR", "./lyrics")

    if not os.path.exists(output_dir):
        logger.info('%s folder does not exist, creating it...' % output_dir)
        os.makedirs(output_dir)

    existing_lyrics = [l.replace('.txt', '') for l in os.listdir(output_dir)]
    logger.info('Found %i existing lyrics' % len(existing_lyrics))

    driver = webdriver.Chrome()
    driver.set_page_load_timeout(10)

    with open(lyrics_csv, 'r') as f:
        lines = f.readlines()
        logger.info("Read %i lines from song file" % (len(lines)))
        for line in lines:
            parts = line.replace('\n', '').split('\t')
            song_id = parts[0]

            if (song_id in existing_lyrics):
                logger.warn("%s lyrics already found. Skipping." % song_id)
                continue

            song_title = parts[1]
            song_artist = parts[2]
            
            try:
                lyrics = search_lyrics(driver, "%s %s lyrics" % (song_title, song_artist))
                if lyrics is not None:
                    with open('%s/%s.txt' % (output_dir, song_id), 'w') as fw:
                        fw.write(lyrics)
                else:
                    logger.warn("Couldn't find lyrics for %s by %s" % (song_title, song_artist))
            except Exception as e:
                logger.warn("Couldn't find lyrics for %s by %s" % (song_title, song_artist))

    # Close the selenium driver session
    logger.info("Closing the selenium session")
    driver.close()

    logger.info("Took %s (seconds)", datetime.now() - start_time)
