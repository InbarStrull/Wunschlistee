import random
import re
import time

from torch.utils.flop_counter import suffixes

from backend.util_functions import insert_to_ingredient_data
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import contains_substring, get_and_remove_suffixes, get_and_remove_suffix, \
    replace_comma_with_dot, get_first_occurrence_of_digit_reversed
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product
from math import ceil

class SonnentorProduct(Product):
    def __init__(self, brand_page_url, html, scraper, base_url):
        super().__init__()
        self.price = None
        self.brand_page_url = brand_page_url
        self.base_url = base_url
        self.html = html
        self.scraper = scraper
        self.brand = "sonnentor"
        self.product_dict = self.create_product_dict()

    def create_product_dict(self):
        return {
            "store_page_url": self.brand_page_url,
            "brand_page_url": self.brand_page_url,
            "brand": self.brand,
            "store": "sonnentor",
            "name": self.get_name,
            "weight": self.get_weight,
            "bag_quantity": self.get_bag_quantity,
            "image_url": self.get_image_url,
            "description": self.get_description,
            "type": self.get_tea_type,
            "ingredients": self.get_ingredients,
            "price": self.get_price,
        }


    @staticmethod
    def manipulate_tea_name(name):
        suffixes = [", lose", " lose", " Kräutertee", "Früchtetee", " Tee"]
        name = get_and_remove_suffixes(name, suffixes)

        # remove ®
        name = name.replace("®", "")
        return name

    @staticmethod
    def manipulate_tea_weight(weight):
        # text structure Doppelkammerbeutel 23,4 g
        weight = weight.split()[-2]
        # replace comma with dot
        weight = weight.replace(",", ".")
        # convert to float
        weight = safe_conversion_float(weight)

        return weight


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        if bag_quantity:
            # Inhalt: 18 Doppelkammerbeutel à 1.3 g
            # take second element
            bag_quantity = bag_quantity.split()[1]
            # convert to int

            return safe_conversion_int(bag_quantity)


    def manipulate_image_url(self, image):
        return f"{self.base_url}{image["href"]}"


    def manipulate_description(self, description):
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        match tea_type:
            case "Kräuter Mischungen":
                return "herbal"

            case "Kräuter Pur":
                return "herbal"

            case "gute Besserung":
                return "herbal"

            case "Kalte Tees":
                return "cold"

            case "Früchtetees":
                return "fruit"

            case "Ingwer, Rooibos & Kurkuma":
                if "Rooibos".lower() in self.name.lower():
                    return "rooibos"
                else:
                    return "herbal"

            case "Chai & Gewürztees":
                return "chai"

            case "Schwarzer, Grüner & Weißer Tee":
                if contains_substring(self.get_name, ["Assam", "Grey", "English Breakfast", "Schwarztee", "Darjeeling"]):
                    return "black"

                elif contains_substring(self.get_name, ["Sencha", "Grüntee", "Jasmin", "Green"]):
                    return "green"

                elif contains_substring(self.get_name, ["Weißtee", "Pai Mu Tan"]):
                    return "white"

            case "Wohlfühl Tees":
                return "herbal"

            case "Kindertees Bio-Bengelchen":
                return "baby"

            case _:
                return


    def manipulate_ingredients(self, ingredient_elements):
        ingredients = []
        for ingredient in ingredient_elements:
            #  if bio appears after percentage
            ingredient = get_and_remove_suffix(ingredient, " bio")
            if "%" in ingredient:
                ingredient = ingredient.replace(",", ".")
                # appears in ()
                if "(" in ingredient and ")" in ingredient:
                    match = re.search(r'\((\d+(?:\.\d+)?)%\)', ingredient)
                    # replace comma
                    ingredient_de = re.sub(r'\s*\(\d+(?:\.\d+)?%\)', '', ingredient).strip()
                    percentage = match.group(1)

                else:
                    # take the part before the %
                    ingredient = ingredient.split("%")[0].strip()
                    percentage = ingredient[get_first_occurrence_of_digit_reversed(ingredient) + 1:]
                    ingredient_de = ingredient[:get_first_occurrence_of_digit_reversed(ingredient) + 1].strip()
                percentage = safe_conversion_float(percentage)

            else:
                ingredient_de = ingredient
                percentage = None
            # if bio appears before percentage
            ingredient_de = get_and_remove_suffix(ingredient_de, " bio")

            ingredient_data = insert_to_ingredient_data(ingredient_de, percentage)
            ingredients.append(ingredient_data)

        return ingredients

    def manipulate_price(self, price):
        price = price.replace("€", "")
        price = price.replace(",", ".")

        price = safe_conversion_float(price)

        return price


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product-information__title",
                                                self.manipulate_tea_name)
        return self.name

    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                   "div.col.font-default-bold",
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        "div.wysiwyg.mt-4.product-information__contents",
                                                        self.manipulate_bag_quantity)
        return self.bag_quantity

    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "a.js-lightbox__item",
                                                    self.manipulate_image_url)
        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       "div.js-expandable__content.expandable-block__content.wysiwyg",
                                                       self.manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                       "li.breadcrumb-item",
                                                       self.manipulate_tea_type, 3)
        return self.tea_type

    @property
    def get_ingredients(self):
        ingredient_elements = self.scraper.get_elements(self.html,
                                                       "div.col-md-3.col-xl-2.col-6.page-break-avoid")

        if not ingredient_elements:
            ingredient_elements = self.scraper.get_field_text_no_manipulation(self.html,
                                                            "p.m-0")

            ingredient_elements = replace_comma_with_dot(ingredient_elements)
            ingredient_elements = ingredient_elements.split(",")

        else:
            ingredient_elements = [ingredient.get_text(strip=True) for ingredient in ingredient_elements]

        self.ingredients = self.manipulate_ingredients(ingredient_elements)
        return self.ingredients

    @property
    def get_price(self):
        self.price = self.scraper.get_field_text(self.html,
                                                       "div.col-auto.font-default-bold.text-right.product-information__price",
                                                       self.manipulate_price)
        return self.price

class SonnentorScraper(Scraper):
    BASE_URL = "https://www.sonnentor.com"
    PRODUCTS_TO_IGNORE = ["kraeuter-pur/kleine-kraeuterfibel",
                          "geschenke/themenboxen/rein-in-den-fruehling-2025-themenbox-bio",
                          "zubehoer-wissen/zubehoer/teesiebloeffel-mit-logo",
                          "geschenke/geschenksets/teezeit-geschenkkarton-31-5x28-5x10-5-cm-bio2",
                          "geschenke/ostern/frohe-ostern-geschenkset-14-5x13x6-cm-bio",
                          "grosspackung",
                          "london-bus",
                          "probier-mal",
                          "nikolaus-krampus",
                          "adventkalender"]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    def get_tea_url(self, html):
        return self.get_field_url(html,"a.stretch-link__link", self.manipulate_tea_url)


    def manipulate_tea_url(self, url):
        return f"{self.base_url}{url["href"]}"


    def is_captcha_page(self, detail_html):
        target_title = "reCAPTCHA-Aufgabe läuft in zwei Minuten ab"
        found = detail_html.find(attrs={"title": target_title}) is not None

        return found


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)
        if not brand_page_url or contains_substring(brand_page_url, self.products_to_ignore):
            return None

        detail_html = fetch_listing_html(brand_page_url)

        # wait and try again if robot test
        if self.is_captcha_page(detail_html):
            print("captcha")
            wait_time = random.uniform(60, 180)
            time.sleep(wait_time)
            detail_html = fetch_listing_html(brand_page_url)

        product = SonnentorProduct(brand_page_url, detail_html, scraper, self.base_url)
        return product.product_dict


if __name__ == "__main__":
    sonnentor_scraper = SonnentorScraper("https://www.sonnentor.com/de-at/onlineshop/tee?page=", "sonnentor")
    sonnentor_scraper.run_multiple_pages("div.col-md-3.col-6", 9, None, lambda x: x - 1)