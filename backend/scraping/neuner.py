import time

from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import (contains_substring,
                                             get_first_occurrence_of_digit_reversed, replace_texts)
from backend.utils.scraping import fetch_listing_html


from scraper import Scraper
from product import Product
from math import ceil

class NeunerProduct(Product):
    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        self.brand = "neuner's"
        self.product_dict = self.create_product_dict()

    def create_product_dict(self):
        return {
            "brand": self.brand,
            "brand_page_url": self.brand_page_url,
            "name": self.get_name,
            "weight": self.get_weight,
            "bag_quantity": self.get_bag_quantity,
            "image_url": self.get_image_url,
            "description": self.get_description,
            "type": self.get_tea_type,
            "ingredients": self.get_ingredients
        }


    @staticmethod
    def manipulate_tea_name(name):
        # remove bio
        texts_to_replace = ["Früchte-Kräutertee offen", "BIO Früchte-Kräutertee", "BIO Kräutertee", "Früchte-Kräutertee"]
        name = replace_texts(name, texts_to_replace)
        return name.strip()


    def manipulate_tea_weight(self, weight):
        """

        if "Aufgussbeutel geknüpft à " in weight:
            grams = weight.split("Aufgussbeutel geknüpft à ")[-1].split("g")[0]
            grams = grams.replace(",", ".")
            grams = safe_conversion_float(grams)
            if self.get_bag_quantity:
                final_weight = self.get_bag_quantity * grams

        """

        if "Aufgussbeutel" in weight:
            if "Aufgussbeutel à " in weight:
                weight = weight.replace("Aufgussbeutel à ", "Aufgussbeutel geknüpft à ")
            grams = weight.split("Aufgussbeutel geknüpft à ")[-1].split("g")[0]
            grams = grams.replace(",", ".")
            grams = safe_conversion_float(grams)
            if self.get_bag_quantity and grams:
                grams = self.get_bag_quantity * grams

        else:
            phases = weight.count("Inhalt")
            grams = weight.split("Inhalt")[phases].strip()
            #grams = weight.split("Inhalt")[1]
            grams = grams.split("g")[0].strip()
            grams = grams[get_first_occurrence_of_digit_reversed(grams) + 1:]
            grams = safe_conversion_float(grams)

        return grams


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        if "Aufgussbeutel" in bag_quantity:
            phases = bag_quantity.count("Aufgussbeutel")
            bag_quantity = bag_quantity.split("Aufgussbeutel")[phases - 1].strip()
            bag_quantity = bag_quantity[get_first_occurrence_of_digit_reversed(bag_quantity) + 1:]
            return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    def manipulate_description(self, description):
        description = description.split("Zutaten")[0].strip()
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        if "Früchtete" in tea_type:
            return "fruit"

        elif "Kräutertee" in tea_type:
            return "herbal"



    def manipulate_ingredients(self, ingredient_text):
        ingredient_text = ingredient_text.replace(" koffeinhaltiger Tee", "")
        # with aus kontrolliert biologischem Anbau suffix
        if "aus kontrolliert" in ingredient_text:
            zutaten_prefix = ["Zutaten BIO Früchte-Kräutertee",
                                             "ZutatenBIO Kräutertee",
                                             "BIO Kräutertee Zutaten"]

            for elem in zutaten_prefix:
                ingredient_text = ingredient_text.replace(elem, "Zutaten BIO Kräutertee")
            # get text between Zutaten BIO Kräutertee and *aus kontrolliert biologischem Anbau
            ingredient_text = ingredient_text.split(
                "Zutaten BIO Kräutertee")[-1]
            ingredient_text = ingredient_text.split(
                "aus kontrolliert")[0].strip()

        # without aus kontrolliert biologischem Anbau suffix
        else:
            # some tees are only herbal and some are herbal fruit
            ingredient_text = ingredient_text.replace("Früchte-", "")
            # get text between räutertee Zutaten and Kräutertee Zubereitung
            ingredient_text = ingredient_text.split(
                "Kräutertee Zutaten")[-1].split(
                "Kräutertee Zubereitung")[0].strip()

        return super().manipulate_ingredients(ingredient_text)


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product-detail-name",
                                                self.manipulate_tea_name)
        return self.name

    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                   "div.product-detail-description-text",
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        "div.product-detail-description-text",
                                                        self.manipulate_bag_quantity)
        return self.bag_quantity

    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "img.img-fluid.gallery-slider-image.magnifier-image.js-magnifier-image",
                                                    self.manipulate_image_url)
        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       "div.product-detail-description-text",
                                                       self.manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                       "h1.product-detail-name",
                                                       self.manipulate_tea_type)
        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "div.product-detail-description-text",
                                                       self.manipulate_ingredients)
        return self.ingredients

class NeunerScraper(Scraper):
    BASE_URL = "https://www.neuners.com"


    def __init__(self, url, brand, products_to_ignore, products_to_include):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = products_to_ignore # List of products to skip
        self.products_to_include = products_to_include


    def get_tea_url(self, html):
        return html["href"]
        #return self.get_field_url(html,"a.product-link", self.manipulate_tea_url)


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)
        if not brand_page_url:
            return None

        if self.products_to_ignore:
            if contains_substring(brand_page_url, self.products_to_ignore):
                return None

        if self.products_to_include:
            if not contains_substring(brand_page_url, self.products_to_include):
                return None

        #brand_page_url = f"{self.BASE_URL}{brand_page_url}"
        detail_html = fetch_listing_html(brand_page_url)
        product = NeunerProduct(brand_page_url, detail_html, scraper)
        return product.product_dict

"""
    def run(self, scraper):
        page = 1

        while True:
            html = fetch_listing_html(f"{self.url}{page}")
            tea_elements = self.get_elements(html, "a.product-image-link.is-standard")

            if not tea_elements:
                break

            for tea_html in tea_elements:
                tea_data = self.parse_tea(tea_html, scraper)
                if not tea_data:
                    continue

                self.print_data(tea_data)
                self.add_tea_to_db(tea_data)

            time.sleep(1)
            page += 1
"""


if __name__ == "__main__":
    neuner_scraper = NeunerScraper("https://www.neuners.com/Produkte/Bio-Kraeutertees/?p=",
                                   "neuner's",
                                   [
                                       "Teeaufsteller-aus-Holz",
                                       "Teebox-aus-Bambus",
                                        "Teetasse-TEA-TIME"],
                                   None)
    #neuner_scraper.delete_before_adding_according_to_brand("neuner's")
    neuner_scraper.run_multiple_pages("a.product-image-link.is-standard", 1)
    neuner_scraper = NeunerScraper("https://www.neuners.com/Produkte/Tradition-Kraeutertees-Einreibungen/?p=",
                                   "neuner's",
                                   None,
                                   ["Tradition-Kraeutertee", "Haustee"])
    neuner_scraper.run_multiple_pages("a.product-image-link.is-standard", 1)