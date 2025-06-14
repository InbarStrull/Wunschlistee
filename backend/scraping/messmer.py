import re

from backend.crud.tea import create_or_update_tea_by_url
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import split_text, contains_substring, replace_texts
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product


class MessmerProduct(Product):
    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        self.brand = "messmer"
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
        #name = name.replace("Bio", "")

        return name.strip()

    @staticmethod
    def manipulate_tea_weight(weight):
        # look for weight in () with g
        weight = safe_conversion_float(weight)
        weight = weight * 1000

        # weight typos
        # added this if part for 40 and 50 grams instead of 0.04 and 0.05 kg
        if weight > 1000:
            weight = weight / 1000

        elif weight > 500:
            weight = weight / 10

        return weight


    def manipulate_bag_quantity(self, bag_quantity):
        texts_to_replace = ["Pyramidenbeutel", "Beutel", "Tea Cups"]
        bag_quantity = replace_texts(bag_quantity, texts_to_replace, "Teebeutel")
        bag_quantity = bag_quantity.split(" Teebeutel")[0].strip()

        # for large boxes (4 x 25 instead of 100)
        if "x" in bag_quantity:
            number_one, number_two = bag_quantity.split(" x ")
            bag_quantity = safe_conversion_int(number_one) * safe_conversion_int(number_two)

        # in most teas, the number opens the string
        # sometimes Inhalt: can open the string
        elif "Inhalt: " in bag_quantity:
            bag_quantity = bag_quantity.replace("Inhalt: ", "")

        return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    def manipulate_description(self, description):
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        if contains_substring(tea_type, ["Cold Tea", "Eistee"]):
            return "cold"

        elif contains_substring(tea_type, ["Gewürztee", "Gewürzteemischung"]):
            return "chai"

        elif contains_substring(tea_type, ["Schwarzer Tee"]):
            return "black"

        elif "Rooibos" in tea_type:
            return "rooibos"

        elif contains_substring(tea_type, ["Kräutertee", "Kräuterteemischung"]):
            return "herbal"

        elif contains_substring(tea_type, ["Früchtetee"]):
            return "fruit"

        elif "Grüner Tee" in tea_type:
            return "green"

        elif "Weißer Tee" in tea_type:
            return "white"

    def manipulate_ingredients(self, ingredient_text):
        ingredient_text = ingredient_text.replace("Rainforrest", "Rainforest")
        ingredient_text = ingredient_text.replace(", (5%),", ",")
        # remove ingredient origin suffixes
        if "Rooibos ist Rainforest" in ingredient_text:
            ingredient_text = ingredient_text.split("Rooibos ist Rainforest")[0]

        elif "Rainforest" in ingredient_text:
            ingredient_text = re.split(r"\*?\d*\.?\d*%?\s*Rainforest", ingredient_text)[0]
            #ingredient_text = re.split(r"\*?\d*%?\s*Rainforest", ingredient_text)[0]


        texts_to_split = ["*60% und ", "Codenummer der Kontrollbehörde", "Vegan, laktosefrei und glutenfrei", "DE-ÖKO-", "Von Natur aus vegan"]
        texts_to_replace = ["Zutaten sind zu", "Maltodextrin, ", "(*100% aus kontrolliert biologischer Landwirtschaft)", "Zutaten:"]
        ingredient_text = split_text(ingredient_text, texts_to_split)
        # before change
        #ingredient_text = re.sub(r"Bio\s+", "", ingredient_text)
        # after change to prevent .Kummel that is devied from .Bio Kummel
        ingredient_text = re.sub(r"\.?\bBio\s+", "", ingredient_text)

        ingredient_text = replace_texts(ingredient_text, texts_to_replace)
        ingredient_text = ingredient_text.replace("\n", " ")
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
                                                   "span.price-unit-content",
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        "div.product-detail-ingredients-text",
                                                         self.manipulate_bag_quantity, 1)

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
                                                       super().manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                 "span.breadcrumb-title",
                                                   self.manipulate_tea_type)

        if not self.tea_type:
            self.tea_type = self.scraper.get_field_text(self.html,
                                        "div.product-detail-sub",
                                        self.manipulate_tea_type)

            if not self.tea_type:
                self.tea_type = "herbal"

        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "div.product-detail-ingredients-text",
                                                       self.manipulate_ingredients)
        return self.ingredients

class MessmerScraper(Scraper):
    BASE_URL = "https://www.messmer.at/"
    PRODUCTS_TO_IGNORE = ["leafline-teekanne-mit-deckel", "5 x ", "collection-box", "3 x ", "3x ", "5x ", "6x ", "-mix-", "paket-",
                          "12er-holzbox-","geschenkbox", "-set-", "emsa-thermoskanne", "leafline-milchgiesser"]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    def get_tea_url(self, html):
        return self.manipulate_tea_url(html)


    def get_tea_category(self, html):
        return self.get_field_url(html, "a.product-teaser__link", self.manipulate_tea_url)

    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)

        if (not brand_page_url or
                contains_substring(brand_page_url, self.PRODUCTS_TO_IGNORE)):
            return None

        detail_html = fetch_listing_html(brand_page_url)
        product = MessmerProduct(brand_page_url, detail_html, scraper)
        return product.product_dict

    def add_to_db_func(self, db, tea_data):
        create_or_update_tea_by_url(db, tea_data)


if __name__ == "__main__":
    messmer_scraper = MessmerScraper("https://www.messmer.at/alle-tees?limit=999", "messmer")
    messmer_scraper.run_one_page("a.product-image-link.is-cover")