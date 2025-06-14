from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import requests

def get_response_from_url_without_driver(url):
    response = requests.get(url)
    return response.text


def get_tea_store_url_page(product_tile, prefix):
    for link in product_tile.find_all('a', href=True):
            # according to structure, tea page link is first href link
            tea_url = link["href"]
            return f"{prefix}{tea_url}"


def get_response_from_url(prefix, page, wait=None):
    chrome_driver_path = r"C:\chromedriver\chromedriver.exe"
    url = f"{prefix}{page}"
    options = Options()
    options.add_argument("--start-maximized")  # optional
    options.add_argument("--headless")
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    print(url)
    driver.get(url)
    time.sleep(2)  # initial load

    if wait:
        wait(driver)

    return driver


def get_html_from_response(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup


def fetch_listing_html(url, wait=None):
    driver = get_response_from_url(url, "", wait)
    response = driver.page_source
    html = get_html_from_response(response)
    driver.quit()
    return html