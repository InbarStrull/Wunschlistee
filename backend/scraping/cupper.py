import time

from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import contains_substring
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product
from math import ceil

class CupperProduct(Product):
    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        self.brand = "cupper"
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
            "ingredients": self.get_ingredients,
            "store": None,
            "price": None,
            "store_page_url": None
        }


    @staticmethod
    def manipulate_tea_name(name):
        # remove bio
        name = name.replace("Bio", "")
        return name.strip()

    @staticmethod
    def manipulate_tea_weight(weight):
        weight = weight.replace(",", ".")
        price = weight.replace("€", "")
        price = safe_conversion_float(price.strip())

        return price


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        # Inhalt pro Packung: 20 Beutel
        bag_quantity = bag_quantity.split("Inhalt pro Packung:")[-1]
        bag_quantity = bag_quantity.split()[0]
        return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return f"https:{image["src"]}"


    def manipulate_description(self, description):
        description = description.split("Inhalt pro Packung:")[0].strip()
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        if "Gewürztee" in tea_type:
            return "chai"

        elif "Cold Brew" in tea_type:
            return "cold"

        elif "Früchtetee" in tea_type:
            return "fruit"

        elif "Kräutertee" in tea_type:
            return "herbal"

        elif "Grüner Tee" in tea_type:
            return "green"

        elif "Weißer Tee" in tea_type:
            return "white"

        elif "Schwarzer Tee" in tea_type:
            return "black"


    def manipulate_ingredients(self, ingredient_text):
        # remove fair trade
        ingredient_text = ingredient_text.replace("nach Fairtrade-Standards gehandelt. Gesamtanteil", "")
        # remove Süßholz warning
        ingredient_text = ingredient_text.replace(" (Enthält Süßholz – Bei hohem Blutdruck sollte ein übermäßiger Verzehr dieses Erzeugnisses vermieden werden.)", "")
        ingredient_text = ingredient_text.split("*Aus ökologischem Anbau.")[0]
        return super().manipulate_ingredients(ingredient_text)


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product-title",
                                                self.manipulate_tea_name)
        return self.name

    @property
    def get_weight(self):

        # site was changed
        """
        price_of_four = self.scraper.get_field_text(self.html,
                                                   "span.price__current.price__current--is_discounted",
                                                   self.manipulate_tea_weight)
        """

        price = self.scraper.get_field_text(self.html,
                                                    "span.price__current",
                                                    self.manipulate_tea_weight)

        price_per_kg = self.scraper.get_field_text(self.html,
                                                   "span.unit-price__price",
                                                   self.manipulate_tea_weight)

        self.weight = float(ceil((price / price_per_kg) * 1000))

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        "div.product-description.rte.cf",
                                                        self.manipulate_bag_quantity)
        return self.bag_quantity

    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "div.img-ar.img-ar--contain img",
                                                    self.manipulate_image_url)
        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       "div.product-description.rte.cf",
                                                       self.manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                       "div.rte.cf",
                                                       self.manipulate_tea_type)
        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "span.metafield-multi_line_text_field",
                                                       self.manipulate_ingredients)
        return self.ingredients

class Cupper(Scraper):
    BASE_URL = "https://cupper-teas.de"
    PRODUCTS_TO_IGNORE = [
        "tee-adventskalender",
        "wintertee-set",
        "for-you-selection",
        "delicious-variety-bio",
        "neuheiten-set-bio",
        "topseller-set",
        "old-water-infusers-starter-set-bundle",
        "lieblinge-set-bio",
        "kraeuter-medley-set",
        "green-tea-lemon-bio",
        "green-tea-lemon-bio-kopie",
        "selection-box",
        "day-to-night-selection",
        "fruity-set-bio"]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    def get_tea_url(self, html):
        return self.get_field_url(html,"a.product-link", self.manipulate_tea_url)


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)
        if not brand_page_url or contains_substring(brand_page_url, self.PRODUCTS_TO_IGNORE):
            return None

        brand_page_url = f"{self.BASE_URL}{brand_page_url}"
        detail_html = fetch_listing_html(brand_page_url)
        product = CupperProduct(brand_page_url, detail_html, scraper)
        return product.product_dict

"""
    def run(self, scraper):
        #self.delete_before_adding_according_to_brand("cupper")
        page = 1
        while True:
            html = fetch_listing_html(f"{self.url}{page}")
            tea_elements = self.get_elements(html, "product-block.product-block")

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
    cupper_scraper = Cupper("https://cupper-teas.de/collections/all?page=", "cupper")
    cupper_scraper.run_multiple_pages("product-block.product-block", 1)