from bs4 import BeautifulSoup
from docutils.parsers.rst.directives import percentage
from backend.utils.translation import google_translate
from backend.utils.string_operations import handle_percentage_format, handle_percentage, replace_comma_with_dot
from backend.util_functions import insert_to_ingredient_data
from backend.utils.scraping import get_response_from_url, get_html_from_response, get_tea_store_url_page
from backend.utils.conversions import safe_conversion_float
import time
import re


def get_data_dmid_from_html(soup, name):
    return soup.select(f'[data-dmid={name}]')


def get_teas_from_html(soup):
    return get_data_dmid_from_html(soup, 'product-tile-container')


def get_price_element(soup):
    return get_data_dmid_from_html(soup, 'price-localized')[0]


def get_product_headline(soup):
    return get_data_dmid_from_html(soup, 'detail-page-headline-product-title')[0]


def get_detail_image(soup):
    image_container = get_data_dmid_from_html(soup, 'image-container')[0]
    return get_data_dmid_from_html(image_container, 'detail-image')[0]


def get_product_description(soup):
    return get_data_dmid_from_html(soup, "Produktbeschreibung-container")[0]


def get_price_infos(soup):
    return get_data_dmid_from_html(soup, 'price-infos')[0]


def get_ingredient_container(soup):
    return get_data_dmid_from_html(soup, "Zutaten-container")[0]


def remove_unnecessary_text_from_ingredient_text(ingredient_text):
    # remove asterix
    ingredient_text = ingredient_text.replace("*", "")

    # remove most of the ingredient list notes
    ingredient_notes = ["aus biologischer Landwirtschaft",
                        "aus ökologischer Landwirtschaft",
                        "kontrolliert ökologischer Anbau",
                        "aus ökologischem Anbau",
                        "kontrolliert ökologisch",
                        "AUS ÖKOLOGISCHEM LANDBAU",
                        "aus kontrolliert biologischer Landwirtschaft",
                        "Aus kontrolliert biologischem Anbau",
                        "aus kontrolliert biologischem Anbau",
                        "aus biologisch-dynamischer Landwirtschaft",
                        "aus kontrolliert ökologischer Erzeugung"]

    for note in ingredient_notes:
        ingredient_text = ingredient_text.replace(note, "")

    return ingredient_text


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


def preprocess_ingredient_text(ingredient_text):
    # handle percentage format
    ingredient_text = handle_percentage_format(ingredient_text)

    # ignore the text that appears before the ingredient list
    ingredient_text = ingredient_text.split("Produktbezeichnung:")[-1]

    # remove asterix and most of the ingredient list notes
    ingredient_text = remove_unnecessary_text_from_ingredient_text(ingredient_text)

    # handle ingredient text prefixes
    ingredient_text = handle_ingredient_text_list_prefix(ingredient_text)

    # strip
    ingredient_text = ingredient_text.strip()

    return ingredient_text


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

def handle_each_ingredient(i, ingredient, last):
    # some ingredients have unnecessary % FairWild™.... remove it
    if "10% FairWild™" in ingredient:
        # dot and space appear before % FairWild
        ingredient = ingredient.split(". ")[0]
    ingredient_de, percentage = handle_percentage(ingredient)

    dot = "."
    # if last ingredient contains a dot, ignore the text that comes after the dot
    if i == last and dot in ingredient_de:
        ingredient_de = ingredient_de.split(dot)[0]


    ingredient_de = handle_ingredient_name(ingredient_de)

    return ingredient_de, percentage


def get_ingredients(soup):
    ingredients = []
    ingredient_info = get_ingredient_container(soup)
    ingredient_text = ingredient_info.get_text(strip=True)

    # remove unnecessary text from ingredient text
    ingredient_text = preprocess_ingredient_text(ingredient_text)

    # split text by comma to extract ingredients
    ingredient_list = ingredient_text.split(",")

    # create each ingredient
    for i, ingredient in enumerate(ingredient_list):
        ingredient = ingredient.strip()
        if ingredient:
            ingredient_de, percentage = handle_each_ingredient(i, ingredient, len(ingredient_list) - 1)

            # ignore the ingredient gemahlen
            if ingredient_de and ingredient_de != "gemahlen":
                ingredient_data = insert_to_ingredient_data(ingredient_de, percentage)
                ingredients.append(ingredient_data)

    return ingredients


def get_price(soup):
    price_element = get_price_element(soup)
    # price for example 10,25 €
    price_text = price_element.get_text(strip=True)
    # get first element
    price = price_text.split()[0]
    # replce comma
    price = price.replace(",", "")

    price = safe_conversion_float(price)
    return price


def get_description(soup):
    to_remove = "Produktbeschreibung"
    product_description = get_product_description(soup)
    description_text = product_description.get_text(strip=True)
    description_de = description_text.replace(to_remove, "")
    description_en = google_translate(description_de, 'de', 'en')
    return description_en


def get_bag_quantity(soup):
    price_infos = get_price_infos(soup)
    price_infos_text = price_infos.get_text(strip=True)
    # check if price info has the term "Btl" (bag quantity)
    if "Btl" in price_infos_text:
        # get first number, for example text is <span>20 Btl (0,11 € je 1 Btl)</span>
        return int(price_infos_text.split(" Btl")[0])
    if " St" in price_infos_text:
        return int(price_infos_text.split(" St")[0])


def get_image_url(tea_store_page_html):
    image_detail = get_detail_image(tea_store_page_html)
    image_url = image_detail['src']
    return image_url


def get_brand_name_weight(headline):
    return headline.get_text(strip=True)


def get_brand(headline):
    brand = headline.find("a")
    return brand.text.strip()


def get_name_weight(headline, brand):
    brand_name_weight = get_brand_name_weight(headline)
    name_weight = brand_name_weight.replace(brand, "")
    # return name weight split by comma
    # name is all elements except the last
    # weight is the last element
    # replace decimal comma with dot
    name_weight = replace_comma_with_dot(name_weight)
    return name_weight.rsplit(',', 1)


def get_type(type_prefix):
    herbal = ["Kräutertee Bio", "Kräutertee ", "Kräutertee Bio-", "Kräutertee-Mischung","Früchte- & Kräutertee Bio", "Früchte- & Kräutertee", "Kräuterteemischung", "Kräutertee Kräutergarten", "Kräuter-Tee", "Kräutertee", "Früchte-Kräutertee"]
    fruit = ["Früchtetee", "Früchteteemischung", "Früchtetee Bio", "Früchtetee Organics"]
    black = ["Schwarzer Tee"]
    chai = ["Gewürztee Bio", "Gewürztee Chai", "Chai Tee"]
    white = ["Weißer Tee"]
    green = ["Grüner Tee", "Kräuter- & Grüner Tee", "Kräuter- & Grüne Bio", "Kräuter- & Grüner Tee Herbal Infusion", "Kräuter- & Grüner Tee Bio"]
    roiboos = ["Rooibos"]
    baby = ["Babytee"]

    if type_prefix in herbal:
        return "herbal"

    elif type_prefix in fruit:
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

    else:
        return None


def get_type_prefix(headline, brand):
    name = get_name_weight(headline, brand)[0]

    if "Babytee" in name:
        return "Babytee"

    elif "Früchte- & Kräutertee Bio" in name:
        return "Früchte- & Kräutertee Bio"

    elif "Früchte- & Kräutertee" in name:
        return "Früchte- & Kräutertee"

    elif "Früchte-Kräutertee" in name:
        return "Früchte-Kräutertee"

    # for Kräutertee Bio-Fenchel-Anis-Kümmel
    elif "Kräutertee Bio-" in name:
        return "Kräutertee "

    elif "Kräutertee Bio" in name:
        return "Kräutertee Bio"

    elif "Kräutertee-Mischung" in name:
        return "Kräutertee-Mischung"

    elif "Kräuterteemischung" in name:
        return "Kräuterteemischung"

    elif "Kräutertee Kräutergarten" in name:
        return "Kräutertee Kräutergarten"

    elif "Kräuter-Tee" in name:
        return "Kräuter-Tee"

    elif "Kräutertee" in name:
        return "Kräutertee"

    elif "Kräuter- & Grüner Tee Herbal Infusion" in name:
        return "Kräuter- & Grüner Tee Herbal Infusion"

    elif "Kräuter- & Grüner Tee Bio" in name:
        return "Kräuter- & Grüner Tee Bio"

    elif "Kräuter- & Grüner Tee" in name:
        return "Kräuter- & Grüner Tee"

    elif "Früchtetee Organics" in name:
        return "Früchtetee Organics"

    elif "Früchtetee Bio" in name:
        return "Früchtetee Bio"

    elif "Früchteteemischung" in name:
        return "Früchteteemischung"

    elif "Früchtetee" in name:
        return "Früchtetee"

    elif "Grüner Tee" in name:
        return "Grüner Tee"

    elif "Schwarzer Tee" in name:
        return "Schwarzer Tee"

    elif "Gewürztee Bio" in name:
        return "Gewürztee Bio"

    elif "Gewürztee Chai" in name:
        return "Gewürztee Chai"

    elif "Chai Tee" in name:
        return "Chai Tee"

    elif "Weißer Tee" in name:
        return "Weißer Tee"

    elif "Rooibos" in name:
        return "Rooibos"

    else:
        return None


def get_name(headline, brand):
    name = get_name_weight(headline, brand)[0]
    # remove weight and tea bag info from name inside parentheses
    name = re.sub(r'\([^)]*\)', '', name)

    # clean up extra spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # remove lose from tea
    if name.startswith("lose ") or name.endswith(" lose"):
        name = name.replace("lose", "").strip()

    return name
    #return " ".join(name_weight.split(',')[:-1])


def remove_name_prefix(name, type_prefix, tea_type):
    # dm gives teas name with the type of the tee as a prefix
    # for the tea named Krautertee and Früchteteemischung
    if not name and type_prefix and tea_type:
        return type_prefix

    if tea_type == "herbal" or tea_type == "fruit" or tea_type == "green":
        return name[len(type_prefix):]

    elif tea_type == "chai":
        if type_prefix == "Gewürztee Bio":
            return name[len(type_prefix):]
        else:
            return f"Chai{name[len(type_prefix):]}"

    else:
        return name


def get_weight(headline, brand):
    name_weight = get_name_weight(headline, brand)[-1]
    #weight_with_g = name_weight.split(',')[-1]
    #weight_string = weight_with_g.strip()[:-1]
    mult_by = 1

    # if weight in kg multiply by 1000
    if "kg" in name_weight:
        weight_string = name_weight.strip()[:-2]
        mult_by = 1000

    else:
        weight_string = name_weight.strip()[:-1]

    weight = safe_conversion_float(weight_string * mult_by)
    return weight


def populate_db():
    """
    data to add:
    Tea model:
    name
    image_url
    brand
    brand_page_url- only if brand is dmBio
    weight
    bag_quantity
    description
    type

    TeaIngredient model:
    ingredients with percentage

    TeaPrice
    price
    store_page_url
    store

    :return:
    """
    URL_PREFIX = "https://www.dm.at/ernaehrung/kaffee-tee-kakao/tee?allCategories.id0=042202&pageSize0=30&sort0=editorial_relevance&currentPage0="
    page = 0

    while True:
        driver = get_response_from_url(URL_PREFIX, page)
        response = driver.page_source
        html = get_html_from_response(response)
        driver.quit()
        # get all tea of current page, or break if no more teas are left
        teas = get_teas_from_html(html)
        if not teas:
            break

        for tea in teas:
            tea_data = dict()

            # get tea store page url
            store_page_url = get_tea_store_url_page(tea, "https://www.dm.at")
            tea_data["store_page_url"] = store_page_url
            #print(store_page_url)
            tea_data["store"] = "dm"
            # get tea store page url html
            driver = get_response_from_url(store_page_url, "")
            response = driver.page_source
            tea_store_page_html = get_html_from_response(response)
            driver.quit()

            # get product headline
            product_headline = get_product_headline(tea_store_page_html)

            # get the first h1
            # get brand from <a>
            brand = get_brand(product_headline)

            # if brand is dmbio, store_page_url is also its brand_page_url
            tea_data["brand_page_url"] = store_page_url

            # get name and weight from h1 text
            # get type from name
            type_prefix = get_type_prefix(product_headline, brand)
            tea_type = get_type(type_prefix)
            name = remove_name_prefix(get_name(product_headline, brand), type_prefix, tea_type).strip()
            weight = get_weight(product_headline, brand)

            tea_data["brand"] = brand.lower()
            tea_data["name"] = name
            tea_data["weight"] = weight
            tea_data["type"] = tea_type

            #get image url
            image_url = get_image_url(tea_store_page_html)
            tea_data["image_url"] = image_url

            # get bag quantity if exists
            bag_quantity = get_bag_quantity(tea_store_page_html)
            tea_data["bag_quantity"] = bag_quantity

            # get description
            description = get_description(tea_store_page_html)
            tea_data["description"] = description

            # get ingredients
            ingredients = get_ingredients(tea_store_page_html)
            tea_data["ingredients"] = ingredients

            price = get_price(tea_store_page_html)
            tea_data["price"] = price

            print(f"\n{name}")
            for key in tea_data:
                print(key, tea_data[key])
            time.sleep(1)
        page += 1





if __name__ == "__main__":
    populate_db()


