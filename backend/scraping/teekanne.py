import re

from backend.crud.tea import create_or_update_tea_by_url, get_tea_by_brand_url, print_changes_in_tea
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import contains_substring, replace_texts, remove_suffix
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product

class TeekanneProduct(Product):
    def __init__(self, brand_page_url, html, scraper):
        super().__init__()
        self.brand_page_url = brand_page_url
        self.html = html
        self.scraper = scraper
        #self.brand = "teekanne"
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

    def manipulate_brand_name(self, brand):
        if brand == "Sir Winston Tea":
            return "sir winston"

        elif "Willi Dungl" in brand:
            return "willi dungl"

        elif "NamasTee" in brand:
            return "namastee"


    def manipulate_tea_name(self, name):
        # remove ORGANICS BIO
        to_replace = ["Organics BIO"]
        # remove bio
        if self.get_brand in ["namastee", "willi dungl"]:
            to_replace.extend(["BIO", "Bio", "NamasTee"])
            name = replace_texts(name, to_replace)

        to_replace.extend(["Loser Tee", ", Fairtrade & RFA", "Fairtrade", "RFA"])

        name = replace_texts(name, to_replace)

        # handle bio
        name = name.replace("BIO", "Bio")

        # Bio is not part of the name on the package of the organics series or the luxury cup series
        substrings = ["Selected. ", "Luxury Cup"]
        if "/organics-" in self.brand_page_url or contains_substring(name, substrings + ["Taste of Winter", "Highland Darjeeling"]):
            name = name.replace("Bio", "")
            name = replace_texts(name, substrings)

        # remove weight
        name = re.sub(r'\(\d+(?:,\d+)?\s*g\)',"", name)

        name = name.strip()

        # replace bio
        if name.endswith(" Bio"):
            name = remove_suffix(name, " Bio")
            name = f"Bio {name}"

        return name

    @staticmethod
    def manipulate_tea_weight(weight):
        # look for weight in () with g
        match = re.search(r'\((\d+(?:,\d+)?)\s*g\)', weight)
        if match:
            # replace comma with dot
            weight_str = match.group(1).replace(",", ".")
            weight = safe_conversion_float(weight_str)

        return weight


    def manipulate_bag_quantity(self, bag_quantity):
        # if tea bag quantity appears in info
        replace = ["Kannenportionen", "Pyramidenbeutel", "Luxury Cups", "Beutel", "Luxury Bags"]

        for item in replace:
            bag_quantity = bag_quantity.replace(item, "Doppelkammerbeutel")

        if "Doppelkammerbeutel" in bag_quantity:
            # take the number that appears before Doppelkammerbeutel
            bag_quantity = bag_quantity.split("Doppelkammerbeutel")[0].strip()
            return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    def manipulate_description(self, description):
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        if "Eistee" in tea_type:
            return "cold"

        elif contains_substring(tea_type, ["Gewürztee", "Gewürzteemischung"]):
            return "chai"

        elif contains_substring(tea_type, ["Schwarzer Tee", "Schwarzteemischung", "Earl Grey"]):
            return "black"

        elif contains_substring(tea_type, ["Kräuterteemischung", "Kräutertee"]):
            return "herbal"

        elif contains_substring(tea_type, ["Früchteteemischung", "Früchtetee"]):
            return "fruit"

        elif "Grüner Tee" in tea_type:
            return "green"

        elif "Weißer Tee" in tea_type:
            return "white"

        elif contains_substring(tea_type, ["Rooibos Tee", "Rotbuschtee"]):
            return "rooibos"

    def manipulate_ingredients(self, ingredient_text):
        # remove ingredient origin suffixes
        if "Rainforest" in ingredient_text:
            ingredient_text = re.split(r"\*?\d*%?\s*Rainforest", ingredient_text)[0]


        elif "Alle Zutaten" in ingredient_text:
            ingredient_text = ingredient_text.split("Alle Zutaten")[0]

        elif "aus kontrolliert" in ingredient_text:
            ingredient_text = ingredient_text.replace("(*100% ", "")
            ingredient_text = ingredient_text.split("aus kontrolliert")[0]

        ingredient_text = ingredient_text.replace("*100% Bio", "")
        ingredient_text = ingredient_text.replace("*Süßblatt=Steviablatt. Nicht zu verwechseln mit Steviolglycosiden, die in einem technischen Verfahren aus dem Süßblatt gewonnen werden.", "")

        pattern = r"(Das|Die) in diesem Produkt"
        ingredient_text = re.split(pattern, ingredient_text)[0].strip()

        ingredient_text = ingredient_text.split("Melatoningranulat")[0]
        ingredient_text = ingredient_text.split("Achten Sie auf eine abwechslungsreiche, ausgewogene")[0]

        if "\\" in ingredient_text:
            ingredient_text = ingredient_text.split("\\")[0]
        return super().manipulate_ingredients(ingredient_text)

    @property
    def get_brand(self):
        self.brand = self.scraper.get_field_text(self.html,
                                                       "div.badge__text",
                                                       self.manipulate_brand_name)

        if not self.brand:
            self.brand = self.scraper.get_field_text(self.html,
                                                        "div.columned-content__text-container--top",
                                                        self.manipulate_brand_name)

            if not self.brand:
                self.brand = "teekanne"

        return self.brand


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.product-hero__name",
                                                self.manipulate_tea_name)
        return self.name

    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                   "h1.product-hero__name",
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        potential_elements = self.scraper.get_elements(self.html,
                                                        "div.info-list__value")

        # find a detail element that mentions tea bag quantity
        for elem in potential_elements:
            self.bag_quantity = self.manipulate_bag_quantity(elem.get_text(strip=True))
            if self.bag_quantity:
                break

        return self.bag_quantity

    @property
    def get_image_url(self):
        try:
            self.image_url = self.scraper.get_field_url(self.html,
                                                        "img.product-hero__image.lazyloaded",
                                                        self.manipulate_image_url)

        except TypeError as e:
            self.image_url = self.scraper.get_field_url(self.html,
                                                        "img.product-hero__slider-image.lazyloaded",
                                                        self.manipulate_image_url)
        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       "div.product-hero__description",
                                                       super().manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        if "cold & fresh" in self.get_name:
            self.tea_type = "cold"

        else:
            self.tea_type = self.scraper.get_field_text(self.html,
                                        "div.badge__text",
                                        self.manipulate_tea_type)

            if not self.tea_type:
                self.tea_type = self.scraper.get_field_text(self.html,
                                                            "div.info-list__value",
                                                            self.manipulate_tea_type)

                # eventually, if nothing was found, tag as herbal
                if not self.tea_type:
                    self.tea_type = "herbal"


        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       "p.product-hero__details-content",
                                                       self.manipulate_ingredients)
        return self.ingredients

class TeekanneScraper(Scraper):
    BASE_URL = "https://www.teekanne.at/"
    CATEGORIES_TO_IGNORE = [
        "Zubehör",
        "Gastro & Büro",
        "Fruchtsaft",
        "Rohkostriegel",
        "Eistee",
        "Tee-Pakete",
        "5 CUPS",
        "Bio-Bonbons",
        "Ländertees",
        "Gastronomie & Foodservice"]
    PRODUCTS_TO_IGNORE = ["Mix & Match", "Geschenkbox", "Adventkalender", "Sortimentsbox"]


    def __init__(self, url, brand):
        super().__init__(brand_or_store=brand, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip


    def get_tea_url(self, html):
        return self.get_field_url(html,"a.product-teaser__link", self.manipulate_tea_url)


    def get_tea_category(self, html):
        return self.get_field_url(html, "a.product-teaser__link", self.manipulate_tea_url)
    @staticmethod
    def manipulate_tea_url(url):
        return url["href"]


    def parse_tea(self, tea_html, scraper):
        category = self.get_element_text(tea_html, "div.product-teaser__category")
        product_name = self.get_element_text(tea_html, "div.product-teaser__name")
        brand_page_url = self.get_tea_url(tea_html)

        if (not brand_page_url or
                category in self.CATEGORIES_TO_IGNORE or
                contains_substring(product_name, self.PRODUCTS_TO_IGNORE)):
            return None

        detail_html = fetch_listing_html(brand_page_url)
        product = TeekanneProduct(brand_page_url, detail_html, scraper)
        return product.product_dict


    def add_to_db_func(self, db, tea_data):
        tea = get_tea_by_brand_url(db, tea_data["brand_page_url"])
        if tea:
            print_changes_in_tea(db, tea.id, tea_data)

        else:
            print("before: It's a new tea!")


if __name__ == "__main__":
    teekanne_scraper = TeekanneScraper("https://www.teekanne.at/shop/de-at/", "teekanne")
    teekanne_scraper.run_one_page("div.product-teaser.product-teaser--mobile-small")