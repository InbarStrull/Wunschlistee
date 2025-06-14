import time

from selenium.webdriver.common.by import By
from backend.utils.string_operations import contains_substring
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product

class YogiTeaProduct(Product):

    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.brand = "yogi tea"
        self.html = html
        self.scraper = scraper
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
        return name


    @staticmethod
    def manipulate_tea_weight(weight):
        ninety_grams = ["Kurkuma Tee lose ⇒ YOGI TEA® Kurkuma Chai",
                        "Schoko Chai ⇒ YOGI TEA® Choco Chai | Gewürzteemischung",
                        "YOGI TEA® Classic Chai ⇒ Ayurvedische Gewürzteemischung"]

        if weight in ninety_grams:
            return float(90)


    def manipulate_bag_quantity(self):
        weight = self.weight
        if weight != float(90):
            return 17


    @staticmethod
    def manipulate_image_url(image):
        return f"{yogi_scraper.BASE_URL}{image["src"]}"


    def manipulate_tea_type(self):
        name = self.get_name
        if "Chai" in name:
            return "chai"

        elif "Rooibos" in name:
            return "rooibos"

        elif "Weißer Tee" in name:
            return "white"

        elif "Grüne" in name or "Grüntee" in name:
            return "green"

        return "herbal"


    def manipulate_ingredients(self, ingredient_text):
        # take the text until *kontrolliert ökologisch
        if "Enthält Süßholz" in ingredient_text:
            ingredient_text = ingredient_text.split("Enthält Süßholz")[0]

        else:
            ingredient_text = ingredient_text.split("*kontrolliert ökologisch")[0]

        return super().manipulate_ingredients(ingredient_text)


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product__info__title",
                                                self.manipulate_tea_name)
        return self.name


    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                  "title",
                                                  self.manipulate_tea_weight)
        return self.weight


    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.manipulate_bag_quantity()
        return self.bag_quantity


    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "img.outerGlow",
                                                    self.manipulate_image_url)

        return self.image_url


    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                           "div.product__info__description__text",
                                           self.manipulate_description)
        return self.description


    @property
    def get_tea_type(self):
        self.tea_type = self.manipulate_tea_type()
        return self.tea_type


    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "div.ingredients-slider-section__bottom__info",
                                                       self.manipulate_ingredients)

        return self.ingredients


class YogiTea(Scraper):
    BASE_URL = "https://www.yogitea.com"
    PRODUCTS_TO_IGNORE = ["finest-selection",
                          "barista-chai-classic"
    ]

    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def wait(self, driver):
        # wait for all teas to be loaded
        SCROLL_PAUSE_TIME = 10
        MAX_SCROLL_ATTEMPTS = 20

        previous_count = 0
        for _ in range(MAX_SCROLL_ATTEMPTS):
            # Scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            # Count the number of tea elements
            tea_items = driver.find_elements(By.CSS_SELECTOR, "a.product-overview__item")
            current_count = len(tea_items)

            if current_count == previous_count:
                break  # no more teas loaded
            previous_count = current_count


    def get_tea_url(self, html):
        return html['href']
        #return self.get_field_url(html,"a.product-overview__item",self.manipulate_tea_url)


    def parse_tea(self, tea_html, scraper):
        brand_page_url = f"{self.BASE_URL}{self.get_tea_url(tea_html)}"
        if not brand_page_url or contains_substring(brand_page_url, self.PRODUCTS_TO_IGNORE) or "tee-set" in brand_page_url:
            return None

        detail_html = fetch_listing_html(brand_page_url)
        product = YogiTeaProduct(brand_page_url, detail_html, scraper)
        return product.product_dict

"""
    def run(self, scraper):
        html = fetch_listing_html(self.url, self.wait)
        tea_elements = self.get_elements(html, "a.product-overview__item")

        for tea_html in tea_elements:
            tea_data = self.parse_tea(tea_html, scraper)
            if not tea_data:
                continue

            self.print_data(tea_data)
            self.add_tea_to_db(tea_data)

"""



if __name__ == "__main__":
    yogi_scraper = YogiTea("https://www.yogitea.com/de/products/yogi-tea/", "yogi tea")
    yogi_scraper.run_one_page("a.product-overview__item", yogi_scraper.wait)