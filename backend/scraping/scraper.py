import time

from backend.crud.tea import create_tea_process, delete_tea_according_to_brand
from backend.database import SessionLocal
from backend.utils.scraping import fetch_listing_html


class Scraper:
    def __init__(self, brand_or_store, url):
        self.brand_or_store = brand_or_store
        self.url = url


    def get_elements(self, html, selector):
        element = html.select(selector)
        if element:
            return element
        return None


    def get_element(self, html, selector, index=None):
        if index:
            elements = self.get_elements(html, selector)
            if elements:
                try:
                    element = elements[index]
                except IndexError as e:
                    print(html)

        else:
            element = html.select_one(selector)

        return element


    def get_element_text(self, html, selector, index=None, separator=""):
        element = self.get_element(html, selector, index)

        if element:
            return element.get_text(strip=True, separator=separator)
        return None


    def get_field_text_no_manipulation(self, html, selector, index=None, separator=""):
        field_text = self.get_element_text(html, selector, index, separator)
        # replace to regular space
        if field_text:
            field_text = field_text.replace("\u00a0", " ").replace("&nbsp;", " ")

        return field_text

    def get_field_text(self, html, selector, manipulation_func, index=None, separator=""):
        field_text = self.get_field_text_no_manipulation(html, selector, index, separator)
        # replace to regular space
        if field_text:
            return manipulation_func(field_text.strip())


    def get_field_url(self, html, selector, manipulation_func, index=None):
        field_url = self.get_element(html, selector, index)
        return manipulation_func(field_url)


    def print_data(self, tea_data):
        print(f"\n{tea_data['name']}")
        for k, v in tea_data.items():
            if k == "ingredients":
                for elem in tea_data[k]:
                    print(elem)
            else:
                print(k, v)


    def parse_tea(self, tea_html, scraper):
        raise NotImplementedError

    def get_tea_url(self, html):
        raise NotImplementedError


    def add_to_db_func(self, db, tea_data):
        create_tea_process(db, tea_data)

    def add_tea_to_db(self, tea_data):
        with SessionLocal() as db:
            try:
                with db.begin():
                    self.add_to_db_func(db, tea_data)
            except Exception as e:
                print(str(e))
                #logging.exception(f"Failed to process and commit tea {tea_data} data")
                raise


    def delete_before_adding_according_to_brand(self, brand_name):
        with SessionLocal() as db:
            try:
                with db.begin():
                    delete_tea_according_to_brand(db, brand_name)
            except Exception as e:
                print(str(e))
                #logging.exception(f"Failed to process and commit tea {tea_data} data")
                raise


    def handle_tea_elements(self, tea_elements):
        for tea_html in tea_elements:
            tea_data = self.parse_tea(tea_html, self)
            if not tea_data:
                continue

            self.print_data(tea_data)
            self.add_tea_to_db(tea_data)


    def run_one_page(self, selector, wait_func=None):
        html = fetch_listing_html(self.url, wait_func)
        tea_elements = self.get_elements(html, selector)

        self.handle_tea_elements(tea_elements)


    def run_multiple_pages(self, selector, start, end=None, page_func=lambda x: x + 1):
        page = start

        # while True (if end is None) or while page < end
        while not end or page < end:
            html = fetch_listing_html(f"{self.url}{page}")
            tea_elements = self.get_elements(html, selector)

            if not tea_elements:
                break

            self.handle_tea_elements(tea_elements)

            time.sleep(1)
            #page += 1
            page = page_func(page)