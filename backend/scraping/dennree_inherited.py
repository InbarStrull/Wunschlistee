from backend.database import engine
from backend.models import Base
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.scraping import get_response_from_url, get_html_from_response, get_response_from_url_without_driver
from backend.utils.string_operations import get_suffix, remove_suffix, replace_texts
from scraper import Scraper
from product import Product

class DennreeProduct(Product):

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
            "name": self.get_name,
            "type": self.get_tea_type,
            "brand_page_url": self.brand_page_url,
            "image_url": self.get_image_url,
            "weight": self.get_weight,
            "bag_quantity": self.get_bag_quantity,
            "description": self.get_description,
            "ingredients": self.get_ingredients,
            "store": None,
            "price": None,
            "store_page_url": None
        }


    def manipulate_tea_name(self, name):
        name_without_lose_and_weight_suffix = self.remove_suffixes_from_tea_type(name)
        type_suffix = self.get_type_suffix(name_without_lose_and_weight_suffix)
        tea_type = self.get_tea_type_from_suffix(type_suffix)

        name = self.remove_name_suffix(name_without_lose_and_weight_suffix, type_suffix, tea_type)
        if not name:
            name = type_suffix

        return name.strip()


    def remove_name_suffix(self, name, type_suffix, tea_type):
        # dennree gives teas name with the type of the tee as a prefix

        # for the tea named Krautertee and Früchteteemischung
        if not name and type_suffix and tea_type:
            return type_suffix

        if tea_type == "roiboos":
            return remove_suffix(name, "tee")

        else:
            return remove_suffix(name, type_suffix)

    @staticmethod
    def manipulate_tea_weight(weight):
        quantity, grams = weight.split()

        if grams == "g":
            return safe_conversion_float(quantity)


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        quantity, grams = bag_quantity.split()
        if grams != "g":
            return safe_conversion_int(quantity)


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    def manipulate_tea_type(self, tea_type):
        if "Rooibos" in tea_type:
            return "rooibos"

        tea_type_without_lose_and_weight_suffix = self.remove_suffixes_from_tea_type(tea_type)
        type_suffix = self.get_type_suffix(tea_type_without_lose_and_weight_suffix)
        final_type = self.get_tea_type_from_suffix(type_suffix)

        return final_type

    @staticmethod
    def remove_suffixes_from_tea_type(tea_type):
        # remove lose suffix from name (if tea has no tea bags)
        lose_suffix = get_suffix(tea_type, ", lose")
        tea_type_without_lose_suffix = remove_suffix(tea_type, lose_suffix)

        # remove weight suffix from name (if tea's weight is mentioned)
        weight_suffix = get_suffix(tea_type_without_lose_suffix, ", 500 g")
        tea_type_without_lose_and_weight_suffix = remove_suffix(tea_type_without_lose_suffix, weight_suffix)

        return tea_type_without_lose_and_weight_suffix

    def get_tea_type_from_suffix(self, type_suffix):
        # herbal = ["Kräuter-Gewürztee", "Kräutertee", "tee"]
        fruit = ["Früchtetee"]
        black = ["Schwarztee"]
        chai = ["Gewürztee"]
        green = ["Grüntee"]
        rooibos = ["Rooibostee"]

        if type_suffix in fruit:
            return "fruit"

        elif type_suffix in black:
            return "black"

        elif type_suffix in chai:
            return "chai"

        elif type_suffix in green:
            return "green"

        elif type_suffix in rooibos:
            return "rooibos"

        else:
            return "herbal"


    def get_type_suffix(self, name_type):
        suffixes = ["Früchtetee",
                    "Grüntee",
                    "Schwarztee",
                    "Kräuter-Gewürztee",
                    "Kräutertee",
                    "Gewürztee",
                    "Rooibostee",
                    "tee"]

        for suffix in suffixes:
            tea_type = get_suffix(name_type, suffix, suffix)
            if tea_type:
                return tea_type

        return ""

    def manipulate_ingredients(self, ingredient_text):
        texts_to_replace = ["11zur Aromatisierung, nicht im Endprodukt enthalten", "¹¹zur Aromatisierung, nicht im Endprodukt enthalten"]
        ingredient_text = replace_texts(ingredient_text, texts_to_replace)
        return super().manipulate_ingredients(ingredient_text)

    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                           ".tx_mmsproducts_product h1",
                                           self.manipulate_tea_name)
        return self.name


    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                           ".row.coreInfo .col-md-6 p",
                                           self.manipulate_tea_weight, 2)
        return self.weight


    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                           ".row.coreInfo .col-md-6 p",
                                           self.manipulate_bag_quantity, 2)
        return self.bag_quantity


    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                          ".productImage img",
                                        self.manipulate_image_url)
        return self.image_url


    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       ".row.coreInfo .col-md-6 p",
                                                        super().manipulate_description, 1)
        return self.description


    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                           ".tx_mmsproducts_product h1",
                                           self.manipulate_tea_type)
        return self.tea_type


    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       ".row.coreInfo .col-md-6 p",
                                                        self.manipulate_ingredients, 4)

        return self.ingredients


class DennreeScraper(Scraper):
    BASE_URL = "https://www.dennree.de"

    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.brand = brand


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def get_tea_url(self, html):
        return html["href"]
        #return self.get_field_url(html, "a", self.manipulate_tea_url)


    @staticmethod
    def fetch_listing_html(url):
        """
        driver = get_response_from_url(url, "")
        response = driver.page_source
        html = get_html_from_response(response)
        driver.quit()
        return html
        :param url:
        :return:
        """
        response = get_response_from_url_without_driver(url)
        html = get_html_from_response(response)
        return html


    def parse_tea(self, tea_html, scraper):
        brand_page_url = f"{self.base_url}{self.get_tea_url(tea_html)}"
        if not brand_page_url:
            return None

        detail_html = self.fetch_listing_html(brand_page_url)
        product = DennreeProduct(brand_page_url, detail_html, scraper, self.brand)
        return product.product_dict

"""
    def run(self, scraper):
        #Base.metadata.drop_all(bind=engine)
        #Base.metadata.create_all(bind=engine)
        html = self.fetch_listing_html(self.url)
        tea_elements = self.get_elements(html, 'div.teaser a')

        for tea_html in tea_elements:
            tea_data = self.parse_tea(tea_html, scraper)
            if not tea_data:
                continue

            #print(f"\n{tea_data['name']}")
            #for k, v in tea_data.items():
                #print(k, v)
            self.print_data(tea_data)
            self.add_tea_to_db(tea_data)
"""


if __name__ == "__main__":
    dennree_scraper = DennreeScraper("https://www.dennree.de/productreload?id=118&category=257&pid=390&offset=0&count=100", "dennree")
    dennree_scraper.run('div.teaser a')