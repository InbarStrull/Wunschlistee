import re
import time
from backend.utils.string_operations import (remove_suffix, get_suffix,
                                             contains_substring,
                                             get_first_occurrence_of_digit_reversed)
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product

class ShotiMaaProduct(Product):

    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        self.product_dict = self.create_product_dict()


    def create_product_dict(self):
        return {
            "brand": self.get_brand,
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
    def manipulate_brand_name(name):
        if get_suffix(name, "Shoti Maa"):
            return "shoti maa"

        elif get_suffix(name, "Hari Tea"):
            return "hari tea"


    @staticmethod
    def manipulate_tea_name(name):
        # name text is duplicated
        name = name[:len(name)//2]
        name = name.replace("–", "-")
        name = remove_suffix(name, get_suffix(name, "- Shoti Maa"))
        name = remove_suffix(name, get_suffix(name, "- Hari Tea"))

        # remove bio and  -
        name = name.replace("-", "")
        name = name.replace("Bio", "")
        name = name.replace("BIO", "")

        return re.sub(r' +', ' ', name).strip()


    @staticmethod
    def manipulate_tea_weight(weight):
        # blabla 16 Teebeutel – 32 g for example
        # weight appears after "Teebeutel – "
        if not weight:
            return None

        if "Teebeutel–" in weight:
            weight = weight.replace("Teebeutel–", "Teebeutel –")

        delimiters = ["Teebeutel – ", "sachets de thé – ", "Teebeutel x "]
        actual_delimeter = ""
        for delim in delimiters:
            if delim in weight:
                weight = weight.split(delim)[1]
                actual_delimeter = delim
                break

        # get the number
        # support both 16 Tea bags– 32 g and 10 Teebeutel x 2 g – 20 g
        if actual_delimeter == "Teebeutel x ":
            #10 Teebeutel x 2 g – 20 g
            # it should always be 20
            weight = 20
            #weight = weight.split(" g")[2]
            #weight = weight.strip()[get_first_occurrence_of_digit_reversed(weight) + 1:]

        else:
            weight = weight.split()[0]

        weight = safe_conversion_float(weight)
        return weight


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        if bag_quantity:
            # take the number that comes before "Teebeutel – "

            bag_quantity = (bag_quantity.
                            split("Teebeutel" if "Teebeutel" in bag_quantity else "sachets de thé")[0].
                            strip())

            # last row
            bag_quantity = bag_quantity.strip()[get_first_occurrence_of_digit_reversed(bag_quantity) + 1:]
            return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return f"https:{image["src"]}"


    def manipulate_description(self, description):
        lang = 'de'
        if "Ingredients:" in description:
            description = description.replace("Ingredients:", "Zutaten:")

        elif "Ingrédients:" in description:
            description = description.replace("Ingrédients:", "Zutaten:")
            lang = 'fr'

        description = description.split("Zutaten:")[0]
        return super().manipulate_description(description, lang)


    def manipulate_ingredients(self, ingredient_text):
        lang = "de"
        if "Ingredients:" in ingredient_text:
            ingredient_text = ingredient_text.replace("Ingredients:", "Zutaten:")

        if "ORGANIC" in ingredient_text:
            ingredient_text = ingredient_text.replace("ORGANIC", "BIOLOGISCH")
            lang = "en"

        if "Ingrédients:" in ingredient_text:
            ingredient_text = ingredient_text.replace("Ingrédients:", "Zutaten:")
            ingredient_text = ingredient_text.replace("BIOLOGIQUE", "BIOLOGISCH")
            lang = "fr"

        # split according to Zutaten\n: and take the first line
        ingredient_text = ingredient_text.split("Zutaten:")[1]

        # ignore what appears after BIOLOGISCH
        ingredient_text = ingredient_text.replace("=BIOLOGISCH", "= BIOLOGISCH")
        ingredient_text = ingredient_text.split("* = BIOLOGISCH")[0]

        return super().manipulate_ingredients(ingredient_text, lang)


    @property
    def get_brand(self):
        self.brand = self.scraper.get_field_text(self.html, "div.product__title",
                                           self.manipulate_brand_name)
        return self.brand


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                           "div.product__title",
                                           self.manipulate_tea_name)
        return self.name


    @property
    def get_weight(self):
        self.weight = (self.scraper.get_field_text(self.html,
                                            "div.product__description.rte.quick-add-hidden",
                                            self.manipulate_tea_weight) or
                (self.scraper.get_field_text(self.html,
                                             "div.site-content",
                                            self.manipulate_tea_weight)))
        return self.weight


    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                            "div.product__description.rte.quick-add-hidden",
                                            self.manipulate_bag_quantity)

        if not self.bag_quantity:
            self.bag_quantity = self.scraper.get_field_text(self.html,
                                                 "div.site-content",
                                                self.manipulate_bag_quantity)

        return self.bag_quantity


    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                          "img.image-magnify-lightbox",
                                          self.manipulate_image_url)
        return self.image_url


    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                           "div.product__description.rte.quick-add-hidden",
                                           self.manipulate_description)
        return self.description


    @property
    def get_tea_type(self):
        self.tea_type = "herbal"
        return self.tea_type


    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                           "div.product__description.rte.quick-add-hidden",
                                           self.manipulate_ingredients)
        return self.ingredients


class ShotiMaa(Scraper):
    BASE_URL = "https://haritea.com"
    PRODUCTS_TO_IGNORE = [
        "balance-your-day",
        "golden-shield-gift-box-with-12-organic-herbal-and-spice-teas-shoti-maa",
        "magic-box",
        "secret-box",
        "buddha-box",
        "daybreak-black-tea-leaf-organic-loose-tea-hari-tea",
        "still-green-pure-green-tea-organic-loose-tea-hari-tea"
    ]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    def get_tea_url(self, html):
        return self.get_field_url(html,"a.full-unstyled-link", self.manipulate_tea_url)


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)
        if not brand_page_url or contains_substring(brand_page_url, self.PRODUCTS_TO_IGNORE):
            return None

        brand_page_url = f"{self.BASE_URL}{brand_page_url}"
        detail_html = fetch_listing_html(brand_page_url)
        product = ShotiMaaProduct(brand_page_url, detail_html, scraper)
        return product.product_dict

"""
    def run(self, scraper):
        page = 1
        while True:
            html = fetch_listing_html(f"{self.url}{page}")
            tea_elements = self.get_elements(html, "li.grid__item")
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
    shoti_scraper = ShotiMaa("https://haritea.com/de/collections/shop?page=", "shoti maa")
    shoti_scraper.run_multiple_pages("li.grid__item" ,1)