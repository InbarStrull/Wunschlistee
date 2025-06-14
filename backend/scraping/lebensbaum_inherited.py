import re

from backend.old.dm import handle_percentage_format
from backend.utils.string_operations import remove_suffix, get_suffix, safe_conversion_float, contains_substring, \
    handle_percentage, split_text
from backend.utils.scraping import get_response_from_url, get_html_from_response
from scraper import Scraper
from product import Product

class LebensbaumProduct(Product):

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
            "ingredients": self.get_ingredients
        }


    @staticmethod
    def manipulate_tea_name(name):
        # split by lose/ loser Tee and take the text that appears before it
        name = name.split(", lose")[0]
        """
        name = remove_suffix(name, get_suffix(name, ", loser Tee, 100g"))
        name = remove_suffix(name, get_suffix(name, ", loser Tee 250g"))
        name = remove_suffix(name, get_suffix(name, ", loser Tee, 50g"))
        name = remove_suffix(name, get_suffix(name, ", loser Tee, 100 g"))
        name = remove_suffix(name, get_suffix(name, ", loser Tee, 1kg"))
        name = remove_suffix(name, get_suffix(name, ", loser Tee"))
        name = remove_suffix(name, get_suffix(name, ", lose"))
        """
        suffixes_to_remove = [", Teebeutel", "®", "75 g"]
        for suffix in suffixes_to_remove:
            name = remove_suffix(name, get_suffix(name, suffix))
        #name = name.replace("®", "")
        return name.strip()


    @staticmethod
    def manipulate_tea_weight(weight):
        # 60 Gramm for example, take first element
        weight = weight.split()[0]

        weight = safe_conversion_float(weight)
        return weight


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        bag_quantity = re.search(r'(\d+)\s*x', bag_quantity)
        return int(bag_quantity.group(1)) if bag_quantity else None


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    @staticmethod
    def manipulate_tea_type(tea_type):
        cold = ["Kaltaufguss", "zum kalt"]
        herbal = ["Kräuter-Früchteteemischung",
                  "Früchte-Kräuterteemischung",
                  "Kräuterteemischung",
                  "Kräutertee"]
        black = ["Schwarztee"]
        green = ["Grüntee", "Grüner Tee"]
        fruit = ["Früchtetee", "Früchteteemischung", "Apfeltee"]
        rooibos = ["Rooibostee"]
        chai = ["Gewürzteemischung", "Chai"]
        white = ["Oolong", "Weisser Tee"]
        mate = ["Matetee"]

        if contains_substring(tea_type, cold):
            return "cold"

        elif contains_substring(tea_type, green):
            return "green"

        elif contains_substring(tea_type, herbal):
            return "herbal"

        elif contains_substring(tea_type, black):
            return "black"

        elif contains_substring(tea_type, fruit):
            return "fruit"

        elif contains_substring(tea_type, rooibos):
            return "rooibos"

        elif contains_substring(tea_type, chai):
            return "chai"

        elif contains_substring(tea_type, white):
            return "white"

        elif contains_substring(tea_type, mate):
            return "mate"

        # herbal needs to be before fruits
        # because fruit tea type can be a substring of a herbal tea type
        else:
            return "herbal"


    def manipulate_ingredients(self, ingredient_text):
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
                                           "p.product-detail-subline",
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
                                                       "div.element-description__description.element-description__description--top",
                                                        self.manipulate_description)
        return self.description


    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                           "p.product-detail-overline",
                                           self.manipulate_tea_type)
        return self.tea_type


    @property
    def get_ingredients(self):
        element = self.scraper.get_element(self.html, '#ingredient-list')  # use base method
        if not element:
            return []

        notice = self.scraper.get_element(self.html, "div.element-ingredients__notice")
        if notice:
            notice.extract()

        ingredient_text = element.get_text(strip=True)

        self.ingredients = self.manipulate_ingredients(ingredient_text)
        return self.ingredients


class Lebensbaum(Scraper):
    BASE_URL = "https://www.lebensbaum.com"
    PRODUCTS_TO_IGNORE = [
        f"{BASE_URL}/p/papier-teefilter-gr.-4-100-stueck",
        f"{BASE_URL}/p/papier-teefilter-gr.-2-100-stueck",
        f"{BASE_URL}/p/teenetze-gr.-2-9-cm",
        f"{BASE_URL}/p/zeit-zum-ausprobieren-mischbox-teebeutel"
    ]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def get_tea_url(self, html):
        return self.get_field_url(html, "a.product-name", self.manipulate_tea_url)


    @staticmethod
    def fetch_listing_html(url):
        driver = get_response_from_url(url, "")
        response = driver.page_source
        html = get_html_from_response(response)
        driver.quit()
        return html


    def parse_tea(self, tea_html, scraper):
        brand_page_url = self.get_tea_url(tea_html)
        if not brand_page_url or brand_page_url in self.PRODUCTS_TO_IGNORE or "tee-set" in brand_page_url:
            return None

        detail_html = self.fetch_listing_html(brand_page_url)
        product = LebensbaumProduct(brand_page_url, detail_html, scraper, self.brand_or_store)
        return product.product_dict

"""
    def run(self, scraper):
        html = self.fetch_listing_html(self.url)
        tea_elements = self.get_elements(html, "div.card-body.card-body-standard")

        for tea_html in tea_elements:
            tea_data = self.parse_tea(tea_html, scraper)
            if not tea_data:
                continue

            self.print_data(tea_data)
            self.add_tea_to_db(tea_data)

"""

if __name__ == "__main__":
    lebensbaum_scraper = Lebensbaum("https://www.lebensbaum.com/c/tee?order=topseller&limit=1000", "lebensbaum")
    lebensbaum_scraper.run_one_page("div.card-body.card-body-standard")