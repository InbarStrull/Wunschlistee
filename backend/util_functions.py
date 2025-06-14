from deep_translator import GoogleTranslator
import wikipedia
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import requests
import re

from selenium.webdriver.support.wait import WebDriverWait

from backend.utils.translation import get_name_translation

#LANGS = ['iw', 'en', 'de'] # supporting hebrew, english, german
"""
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


def google_translate(text_source, source_language, target_language):
    return GoogleTranslator(source=source_language, target=target_language).translate(text=text_source)


def get_wikipedia_url(term, language):
    wikipedia.set_lang(language)
    try:
        page = wikipedia.page(term).url
        return page

    except wikipedia.exceptions.PageError:
        return None

    # perhaps multiple pages for desired term, take the first suggestion
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            # take the first suggestion
            page = wikipedia.page(e.options[0]).url
            return page

        except:
            return None

def get_name_translation(ingredient_data, ingredient, language):
    for lang in LANGS:
        if lang == language:
            ingredient_data[f"name_{lang}"] = ingredient
            continue
        # if translation fails, add name as None
        try:
            ingredient_data[f"name_{lang}"] = google_translate(ingredient, language, lang)

        except Exception:
            ingredient_data[f"name_{lang}"] = ""

    return ingredient_data



def get_wikipedia_page_url(ingredient_data):
    if ingredient_data['name_en']:
        ingredient_data['wikipedia_url'] = get_wikipedia_url(ingredient_data['name_en'], 'en')

    #return ingredient_data

def get_html_from_response(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup



def get_suffix(name, suffix, return_value=None):
    if not return_value:
        return_value = suffix

    if name.endswith(suffix):
        return return_value

    return ""


def remove_suffix(name, suffix):
    if suffix:
        name = name[:(-1) * len(suffix)]

    return name


def get_prefix(name, prefix, return_value):
    if name.endswith(prefix):
        return return_value


def safe_conversion_float(text):
    if text:
        try:
            text = float(text)
            return text

        except (ValueError, AttributeError) as e:
            print(str(e))


def safe_conversion_int(text):
    if text:
        try:
            text = int(text)
            return text

        except (ValueError, AttributeError) as e:
            print(str(e))


def contains_substring(input_string, substrings):
    contains = any(substring in input_string for substring in substrings)
    return contains


def handle_percentage_format(ingredient_text):
    # handle percentage format
    ingredient_text = ingredient_text.replace(" %", "%")    # remove space between number and %
    ingredient_text = replace_comma_with_dot(ingredient_text) # replace german decimal comma with dot
    ingredient_text = re.sub(r'\((\d+(?:\.\d+)?)%\)', r'\1%', ingredient_text) # remove () from percentage

    return ingredient_text


def replace_comma_with_dot(text):
    text = re.sub(r'(?<=\d),(?=\d\s*)', '.', text)  # replace german decimal comma with dot
    return text


def add_space_between_digit_and_character(ingredient):
    for i, char in enumerate(ingredient):
        if char.isdigit():
            return ingredient[:i] + ' ' + ingredient[i:]
    return ingredient


def handle_percentage(ingredient):
    ingredient = ingredient.strip()
    percentage_sign = "%"
    dot = "."
    percentage_dot = f"{percentage_sign}{dot}"

    # check percentage
    # if %  or %. appears in the end
    #print("hi", ingredient)
    if ingredient[-1] == percentage_sign or ingredient[-2:] == percentage_dot:
        if ingredient[-2:] == percentage_dot:
            to_replace = percentage_dot
        else:
            to_replace = percentage_sign

        # add space between number and ingredient

        if " " not in ingredient:
            ingredient = add_space_between_digit_and_character(ingredient)

        # split ingredient into to parts from the right
        try:
            ingredient_de, percentage = ingredient.rsplit(" ", 1)

        except ValueError as e:
            # ingredient and percentage are not separated by a space
            # find the index of the first numeric digit and split accordingly
            match = re.search(r'\d', ingredient)
            index = match.start() if match else -1
            # split according to that index
            ingredient_de, percentage = ingredient[:index], ingredient[index:]
        # remove % or %.
        percentage = percentage.replace(to_replace, "")


    # if % appears in a different place
    elif percentage_sign in ingredient:
        percentage, ingredient_de = ingredient.split(percentage_sign)

    # no %
    else:
        ingredient_de, percentage = ingredient, None

    # convert percentage to float
    percentage = safe_conversion_float(percentage)

    return ingredient_de, percentage


def omit_asterix(text):
    # first make sure the asterix has a space after it
    text = re.sub(r'\*+(?!\s)', '* ', text)
    text = re.sub(r"\*+", "", text)
    return text


def get_first_occurance_of_digit_reversed(text):
    for c in range(len(text) - 1, -1, -1):
        if not text[c].isdigit():
            return c

    return -1

def fetch_listing_html(url, wait=None):
    driver = get_response_from_url(url, "", wait)
    response = driver.page_source
    html = get_html_from_response(response)
    driver.quit()
    return html

def replace_texts(string, old_texts, new_text=""):
    for text in old_texts:
        string = string.replace(text, new_text)

    return string


def split_text(string, texts_to_split_by, index=0):
    for text in texts_to_split_by:
        string = string.split(text)[index]

    return string
"""
def create_ingredient_data(ingredient, language):
    ingredient_data = dict()

    get_name_translation(ingredient_data, ingredient, language)

    # used english wikipedia because it is more readable than german and has more pages than hebrew
    #get_wikipedia_page_url(ingredient_data)

    return ingredient_data

def insert_to_ingredient_data(ingredient_name, percentage, lang='de'):
    ingredient_data = create_ingredient_data(ingredient_name, lang)
    ingredient_data["percentage"] = percentage

    return ingredient_data