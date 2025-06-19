import re
import time

from backend.util_functions import insert_to_ingredient_data
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
from backend.utils.string_operations import replace_comma_with_dot, replace_texts, \
    handle_percentage_format, handle_percentage, contains_substring, remove_suffix, \
    get_first_occurrence_of_digit_reversed
from backend.utils.scraping import fetch_listing_html
from scraper import Scraper
from product import Product
from math import ceil

class SparProduct(Product):
    def __init__(self, store_page_url, html, scraper, store):
        super().__init__()
        self.store_page_url = store_page_url
        self.html = html
        self.scraper = scraper
        self.store = store
        self.product_dict = self.create_product_dict()

    def create_product_dict(self):
        return {
            "store_page_url": self.store_page_url,
            "store": self.store,
            "brand_page_url": self.get_brand_page_url,
            "brand": self.get_brand.lower(),
            "name": self.get_name,
            "weight": self.get_weight,
            "type": self.get_tea_type,
            "image_url": self.get_image_url,
            "bag_quantity": self.get_bag_quantity,
            "description": self.get_description,
            "ingredients": self.get_ingredients
            #"price": self.get_price
        }

    def manipulate_brand_name(self, brand_name):
        brand_name = brand_name.split("\n")[0]

        if "spar" in brand_name.lower():
            brand_name = "spar"

        elif "Teekanne" in brand_name:
            brand_name = "teekanne"

        elif "Willi Dungl" in brand_name:
            brand_name = "willi dungl"

        elif "Namastee" in brand_name:
            brand_name = "namastee"

        return brand_name.lower()


    def manipulate_tea_name(self, name):
        name = name.split("\n")[-1]

        # take the part before Teebeutel
        if " Teebeutel" in name:
            name = name.split(" Teebeutel")[0]
            # take the part before number
            name = name[:get_first_occurrence_of_digit_reversed(name)]

    def clean_name_from_weight_tea_bag_data(self, name):
        # remove weight and tea bag info from name inside parentheses
        name = re.sub(r'\([^)]*\)', '', name)

        # clean up extra spaces
        name = re.sub(r'\s+', ' ', name).strip()

        # remove lose from tea
        if name.startswith("lose ") or name.endswith(" lose"):
            name = name.replace("lose", "").strip()

        return name

    def remove_brand_decimal_comma_and_split(self, text):
        text = text.replace(self.brand, "")
        # get name and weight split by comma
        # name is all elements except the last
        # weight is the last element
        # replace decimal comma with dot
        text = replace_comma_with_dot(text)
        return text.rsplit(',', 1)


    def manipulate_tea_weight(self, weight):
        name_weight = self.remove_brand_decimal_comma_and_split(weight)[-1]
        name_weight = name_weight.replace(self.brand, "")

        mult_by = 1

        # if weight in kg multiply by 1000
        if "kg" in name_weight:
            weight_string = name_weight.strip()[:-2]
            mult_by = 1000

        elif name_weight.endswith(" Btl"):
            return

        else:
            weight_string = name_weight.strip()[:-1]

        final_weight = safe_conversion_float(weight_string) * mult_by
        return final_weight


    @staticmethod
    def manipulate_bag_quantity(bag_quantity):
        split_by = ""
        # check if price info has the term "Btl" (bag quantity)
        if "Btl" in bag_quantity:
            # get first number, for example text is <span>20 Btl (0,11 € je 1 Btl)</span>
            split_by = " Btl"

        elif " St" in bag_quantity:
            split_by = " St"

        if split_by:
            bag_quantity = bag_quantity.split(split_by)[0]
            return safe_conversion_int(bag_quantity)


    @staticmethod
    def manipulate_image_url(image):
        return image["src"]


    def manipulate_description(self, description):
        description = description.replace("Produktbeschreibung", "")
        return super().manipulate_description(description)


    def manipulate_tea_type(self, tea_type):
        # extract type from type and name text
        type_prefix = self.get_type_prefix(tea_type)
        final_type = self.get_final_type(type_prefix)

        return final_type

    def get_final_type(self, type_prefix):
        herbal = ["Früchte- & Kräutertee Bio", "Kräutertee Bio", "Kräutertee-Mischung",
                  "Früchte- & Kräutertee", "Kräuterteemischung",
                  "Kräutertee Kräutergarten", "Kräuter-Tee", "Früchte-Kräutertee",
                  "Kräutertee ", "Kräutertee"]
        fruit = ["Früchteteemischung", "Früchtetee Bio", "Früchtetee Organics",
                 "Früchtetee", "Früchte Tee", "Früchte-Gewürztee", "Wintertee"]
        black = ["Schwarzer Tee"]
        chai = ["Gewürztee Bio", "Gewürztee Chai", "Chai Tee", "gewürzt"]
        white = ["Weißer Tee"]
        green = ["Kräuter- & Grüner Tee Herbal Infusion", "Kräuter- & Grüner Tee Bio",
                 "Kräuter- & Grüner Tee", "Kräuter- & Grüne Bio", "Grüner Tee", "Matcha Tee Grün gemahlen"]
        roiboos = ["Rooibos", "Christmas Tea"]
        baby = ["Babytee"]

        if type_prefix in herbal:
            return "herbal"

        elif contains_substring(type_prefix, fruit):
            return "fruit"

        elif type_prefix in black:
            return "black"

        elif type_prefix in chai:
            return "chai"

        elif type_prefix in white:
            return "white"

        elif type_prefix in green:
            return "green"

        elif type_prefix in roiboos:
            return "roiboos"

        elif type_prefix in baby:
            return "baby"

    def get_type_prefix(self, name):
        name = self.remove_brand_decimal_comma_and_split(name)[0]

        substrings_to_return = ["Früchte-Gewürztee", "Babytee", "Früchte- & Kräutertee Bio",
                                "Früchte- & Kräutertee", "Früchte-Kräutertee",
                                "Kräutertee Bio", "Kräutertee-Mischung", "Kräuterteemischung",
                                "Kräutertee Kräutergarten", "Kräuter-Tee", "Kräutertee",
                                "Kräuter- & Grüner Tee Herbal Infusion", "Kräuter- & Grüner Tee Bio",
                                "Kräuter- & Grüner Tee", "Früchtetee Organics",
                                "Früchtetee Bio", "Früchteteemischung", "Früchtetee",
                                "Grüner Tee", "Schwarzer Tee", "Gewürztee Bio",
                                "Gewürztee Chai", "Chai Tee", "Weißer Tee", "Rooibos",
                                "Matcha Tee Grün gemahlen"]
        substrings_with_return_value = {"Kräutertee Bio-": "Kräutertee "}
        for substring in substrings_with_return_value:
            if substring in name:
                return substrings_with_return_value[substring]

        for substring in substrings_to_return:
            if substring in name:
                return substring

        return name




    def manipulate_ingredients(self, ingredient_text):
        ingredients = []
        # part of super.manipulate_ingredients()
        ingredient_text = ingredient_text.replace("*", "")
        # part of super.manipulate_ingredients()
        ingredient_text = handle_percentage_format(ingredient_text)

        # ignore the text that appears before the ingredient list
        ingredient_text = ingredient_text.split("Produktbezeichnung:")[-1]

        # remove most of the ingredient list notes
        ingredient_notes = ["aus biologischer Landwirtschaft",
                            "aus ökologischer Landwirtschaft",
                            "aus kontrolliert ökologischen Anbau.",
                            "kontrolliert ökologischer Anbau",
                            "aus ökologischem Anbau.",
                            "aus ökologischem Anbau",
                            "kontrolliert ökologisch",
                            "AUS ÖKOLOGISCHEM LANDBAU",
                            "aus kontrolliert biologischer Landwirtschaft",
                            "Aus kontrolliert biologischem Anbau",
                            "aus kontrolliert biologischem Anbau",
                            "aus biologisch-dynamischer Landwirtschaft",
                            "aus kontrolliert ökologischer Erzeugung",
                            "*aus kontrolliert biologischer Landwirtschaft 70% Rainforest Alliance-zertifiziert. Mehr dazu auf ra.org",
                            "Enthält Süßholz – Bei hohem Blutdruck sollte ein übermäßiger Verzehr dieses Erzeugnisses vermieden werden. Maté enthält natürliches Koffein. Für Kinder und Schwangere Frauen nicht empfohlen."]

        ingredient_text = replace_texts(ingredient_text, ingredient_notes)

        # handle ingredient text prefixes
        ingredient_text = self.handle_ingredient_text_list_prefix(ingredient_text)

        # split text by comma to extract ingredients
        ingredient_list = ingredient_text.split(",")

        # create each ingredient
        for i, ingredient in enumerate(ingredient_list):
            ingredient = ingredient.strip()
            if ingredient:
                ingredient_de, percentage = self.handle_each_ingredient(i, ingredient, len(ingredient_list) - 1)

                # ignore the ingredient gemahlen
                if ingredient_de and ingredient_de != "gemahlen":
                    ingredient_data = insert_to_ingredient_data(ingredient_de, percentage)
                    ingredients.append(ingredient_data)

        return ingredients

        #return super().manipulate_ingredients(ingredient_text)

    @staticmethod
    def handle_ingredient_name(ingredient_de):
        # make capital letters small if they are not at the beginning of a word
        # remove the word bio
        ingredient_de_word_list = []
        for word in ingredient_de.split():
            if word or word.lower() != "bio":
                if word[0].isupper():
                    word = word[0] + word[1:].lower()
                ingredient_de_word_list.append(word)

        ingredient_de = " ".join(ingredient_de_word_list)

        # strip ingredient
        ingredient_de = ingredient_de.strip()

        return ingredient_de


    def handle_each_ingredient(self, i, ingredient, last):
        # some ingredients have unnecessary % FairWild™.... remove it
        if "10% FairWild™" in ingredient:
            # dot and space appear before % FairWild
            ingredient = ingredient.split(". ")[0]
        ingredient_de, percentage = handle_percentage(ingredient)

        dot = "."
        # if last ingredient contains a dot, ignore the text that comes after the dot
        if i == last and dot in ingredient_de:
            ingredient_de = ingredient_de.split(dot)[0]

        ingredient_de = self.handle_ingredient_name(ingredient_de)

        return ingredient_de, percentage

    @staticmethod
    def handle_ingredient_text_list_prefix(ingredient_text):
        # Zutaten: and Enthält: can be the prefix of the ingredient list
        if "Zutaten:" in ingredient_text or "Enthält:" in ingredient_text:
            # replace Zutaten: with Enthält: for prefix unity
            ingredient_text = ingredient_text.replace("Zutaten:", "Enthält:")
            # ignore prefix and read the first line only
            ingredient_text = ingredient_text.split("Enthält:")[-1].split("\n")[0]

        # empty prefix
        else:
            ingredient_text = ingredient_text.split("\n")
            # take the last line if it is not empty
            # if empty take the second line
            # sometimes the last line is the second line. in other cases, the last line is a removed note
            ingredient_text = ingredient_text[-1] if ingredient_text[-1] else ingredient_text[1]
            # in some cases, ingredients are split by spaces or a pipe instead of a comma
            ingredient_text = ingredient_text.replace("   ", ", ")
            ingredient_text = ingredient_text.replace("|", ", ")

        # sometimes ingredient list prefix remains Zutaten after processing:
        # remove Zutaten prefix
        if len(ingredient_text) > 7:
            if ingredient_text[:7].lower() == "zutaten":
                ingredient_text = ingredient_text[7:]

        return ingredient_text

    def manipulate_price(self, price):
        # get first element
        price = price.split()[0]
        # replce comma
        price = price.replace(",", "")

        price = safe_conversion_float(price)

        return price

    @property
    def get_brand(self):
        self.brand = self.scraper.get_field_text(self.html,
                                                "h1.productDetailsName",
                                                self.manipulate_brand_name,
                                                 index=None,
                                                 separator='\n')

        return self.brand

    @property
    def get_brand_page_url(self):
        self.brand_page_url = self.store_page_url if self.get_brand == "spar" else None

        return self.brand_page_url


    @property
    def get_name(self):
        self.name = self.scraper.get_field_text(self.html,
                                                "h1.productDetailsName",
                                                self.manipulate_tea_name,
                                                 index=None,
                                                 separator='\n')

        return self.name

    @property
    def get_weight(self):
        self.weight = self.scraper.get_field_text(self.html,
                                                   'h1[data-dmid="detail-page-headline-product-title"]',
                                                   self.manipulate_tea_weight)

        return self.weight

    @property
    def get_bag_quantity(self):
        self.bag_quantity = self.scraper.get_field_text(self.html,
                                                        'div[data-dmid="price-infos"]',
                                                        self.manipulate_bag_quantity)
        return self.bag_quantity

    @property
    def get_image_url(self):
        self.image_url = self.scraper.get_field_url(self.html,
                                                    "img.pdd_to25u00",
                                                    self.manipulate_image_url)
        return self.image_url

    @property
    def get_description(self):
        self.description = self.scraper.get_field_text(self.html,
                                                       'details[data-dmid="Produktbeschreibung-container"]',
                                                       self.manipulate_description)
        return self.description

    @property
    def get_tea_type(self):
        self.tea_type = self.scraper.get_field_text(self.html,
                                                       'h1[data-dmid="detail-page-headline-product-title"]',
                                                       self.manipulate_tea_type)
        return self.tea_type

    @property
    def get_ingredients(self):
        self.ingredients = self.scraper.get_field_text(self.html,
                                                       'div[data-dmid="Zutaten-content"]',
                                                       self.manipulate_ingredients)
        return self.ingredients

    @property
    def get_price(self):
        self.price = self.scraper.get_field_text(self.html,
                                                       'span[data-dmid="price-localized"]',
                                                       self.manipulate_price)
        return self.price

class SparScraper(Scraper):
    BASE_URL = "https://www.interspar.at/"
    PRODUCTS_TO_IGNORE = ["adventskalender"]


    def __init__(self, url, store):
        super().__init__(brand_or_store=store, url=url)
        self.url = url  # The URL to scrape from
        self.base_url = self.BASE_URL  # Storing the base URL for later use
        self.products_to_ignore = self.PRODUCTS_TO_IGNORE  # List of products to skip
        self.products = dict()


    def get_tea_url(self, html):
        return self.get_field_url(html,"a", self.manipulate_tea_url)


    def manipulate_tea_url(self, url):
        return f"{self.BASE_URL}{url["href"]}"


    def parse_tea(self, tea_html, scraper):
        store_page_url = self.get_tea_url(tea_html)
        if not store_page_url or contains_substring(store_page_url, self.products_to_ignore):
            return None

        detail_html = fetch_listing_html(store_page_url)
        product = SparProduct(store_page_url, detail_html, scraper, self.brand_or_store)
        return product.product_dict


if __name__ == "__main__":
    spar_scraper = SparScraper("https://www.interspar.at/shop/lebensmittel/getraenke/tee/c/F7-4//?query=*&q=*&hitsPerPage=1000", "spar")
    spar_scraper.run_one_page("div.productInfo")