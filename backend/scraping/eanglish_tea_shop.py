import time

from backend.crud.tea import delete_tea_according_to_brand
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.scraping import fetch_listing_html
from backend.utils.string_operations import contains_substring, split_text, replace_texts
from scraper import Scraper
from product import Product
from backend.database import SessionLocal


class ETSProduct(Product):
    def __init__(self, brand_page_url, html, scraper, brand):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        self.brand = brand
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
        # remove ETS -
        name = name.replace("ETS - ", "")
        # add Pyramiden
        pyramiden = " Pyramiden" if "Pyramiden" in name else ""
        # there is Naturland BIO and just BIO
        texts_to_split = ["Naturland", "BIO", "koffeinfreier"]
        name = split_text(name, [f", {text}" for text in texts_to_split])
        name = f"{name}{pyramiden}"

        texts_to_replace = ['"', "'"]
        name = replace_texts(name, texts_to_replace)

        return name.strip()

    @staticmethod
    def manipulate_tea_weight(weight):
        # replace comma with dot
        weight = weight.replace(",", ".")
        # remove g
        weight = weight.split("g")[0]

        weight = safe_conversion_float(weight.strip())

        return weight


    def manipulate_bag_quantity(self, bag_quantity):
        if "beutel" in bag_quantity.lower():
            # tea bag quantity appears at the end
            bag_quantity = bag_quantity.split(",")[-1]
            # remove bag type
            bag_quantity = split_text(bag_quantity, ["Pyramiden-Beutel", "Teebeutel"])
            # strip
            bag_quantity = bag_quantity.strip()

            return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        small_image = image["src"]
        large_image = small_image.replace("/xs/", "/lg/")
        return large_image


    def manipulate_description(self, description):
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        if "Rooibos" in self.get_name:
            return "rooibos"

        if "Chai" in self.get_name:
            return "chai"

        if "Gewürze für Gin" in tea_type:
            if "Apfel" in self.get_name:
                return "fruit"

        if "Grüner Tee" in tea_type or "Grüner Tee" in self.get_name:
            return "green"

        if "Kräutertee" in tea_type:
            return "herbal"

        if "Schwarzer Tee" in tea_type:
            return "black"

        if "Weißer Tee" in tea_type:
            return "white"

        if "Früchtetee" in tea_type:
            return "fruit"

        if "Cold Brew & Eistee" in tea_type:
            return "cold"

        if contains_substring(tea_type, ["Gewürze", "Weihnachten", "Wintertee"]):
            return "chai"

    def manipulate_ingredients(self, ingredient_text):
        # suffix standardization:
        texts_to_split = ["(Alle Zutaten aus kontrolliert biologischem Anbau",
                          "Alle Zutaten aus kontrolliert biologischem Anbau",
                          "(*= aus kontrolli",
                          "(* = aus kontrollier",
                          "* = aus kontrolliert",
                          "aus kontrolliert biologischem Anbau",
                          "(Alle Zutagen"]

        # take text between prefix (Zutaten:) and suffix
        ingredient_text = split_text(ingredient_text, texts_to_split)

        ingredient_text = ingredient_text.split("Zutaten:")[-1]
        ingredient_text = ingredient_text.strip()
        # remove dot
        if ingredient_text[-1] == ".":
            ingredient_text = ingredient_text[:-1]

        return super().manipulate_ingredients(ingredient_text)


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product-title.h2",
                                                self.manipulate_tea_name)
        return self.name

    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                   "td.attr-value",
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        "h1.product-title.h2",
                                                         self.manipulate_bag_quantity)

        return self.bag_quantity

    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "img.product-image.img-fluid",
                                                    self.manipulate_image_url)

        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       "div.shortdesc",
                                                       super().manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                 "li.product-category.word-break",
                                                 self.manipulate_tea_type)

        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "#tab-description",
                                                       self.manipulate_ingredients)
        return self.ingredients

class ETSScraper(Scraper):
    BASE_URL = "https://www.ets-tee.de/"
    PRODUCTS_TO_IGNORE = ["oh-tannenbaum-tee-dekoration",
                          "for-you-tee-geschenk",
                          "frohe-weihnachten-tee-weihnachtskarte",
                          "advent",
                          "kollektion",
                          "poesie"]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip
        self.brand = brand


    def get_tea_url(self, html):
        return self.manipulate_tea_url(html)


    def get_tea_category(self, html):
        return self.get_field_url(html, "a.product-teaser__link", self.manipulate_tea_url)

    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)

        if not brand_page_url or contains_substring(brand_page_url.lower(), self.products_to_ignore):
            return

        detail_html = fetch_listing_html(brand_page_url)
        product = ETSProduct(brand_page_url, detail_html, scraper, self.brand)
        return product.product_dict

"""
    def run(self, scraper):
        page = 1
        while page  < 3:
            html = fetch_listing_html(f"{self.url}{page}")
            tea_elements = self.get_elements(html, "div.productbox-images.list-gallery a")

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
    ets_scraper = ETSScraper("https://www.ets-tee.de/English-Tea-Shop?pf=2_11&af=100&seite=", "english tea shop")
    ets_scraper.run_multiple_pages("div.productbox-images.list-gallery a", 1, 3)