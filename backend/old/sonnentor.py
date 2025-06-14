from backend.util_functions import insert_to_ingredient_data
from backend.utils.translation import google_translate
from backend.utils.scraping import get_response_from_url, get_html_from_response
from backend.utils.conversions import safe_conversion_float, safe_conversion_int
import time
import re

def get_teas_from_html(html):
    return html.select("div.col-md-3.col-6")


def get_tea_store_url_page_element(tea):
    return tea.select("a.stretch-link__link")[0]


def get_name_element(html):
    name_element = html.find('h1', class_='product-information__title')
    return name_element


def get_bag_quantity_element(html):
    return html.find("div", class_="wysiwyg mt-4 product-information__contents")


def get_description_element(html):
    return html.find('div', class_="js-expandable__content expandable-block__content wysiwyg")


def get_image_element(html):
    image_div = html.find('div', class_='thumb-slider__main-item lightbox-img')
    return image_div.find('a', class_='js-lightbox__item')


def get_store_page_url(html, prefix):
    store_page_url_element = get_tea_store_url_page_element(html)
    href = store_page_url_element["href"]
    store_page_url = f"{prefix}{href}"
    return store_page_url


def get_weight_element(html):
    return html.find('div', class_='col font-default-bold')


def get_tea_type_element(html):
    return html.find_all('li', class_='breadcrumb-item')[3]


def get_ingredient_container(html):
    return html.find_all('div', class_='col-md-3 col-xl-2 col-6 page-break-avoid')


def get_price_element(html):
    return html.find('div', class_="col-auto font-default-bold text-right product-information__price")


def get_image_url(html, prefix):
    image_element = get_image_element(html)
    #image_url = get_tea_store_url_page(image_element, prefix)
    image = image_element.get('href')
    image_url = f"{prefix}{image}"
    return image_url


def get_description(html):
    description_de = get_description_element(html).get_text(strip=True)
    description_en = google_translate(description_de, 'de', 'en')
    return description_en


def get_bag_quantity(html):
    bag_quantity = get_bag_quantity_element(html)
    bag_quantity = bag_quantity.get_text(strip=True)
    if bag_quantity:
        # Inhalt: 18 Doppelkammerbeutel à 1.3 g
        # take second element
        bag_quantity = bag_quantity.split()[1]
        # convert to int

        return safe_conversion_int(bag_quantity)


def get_price(html):
    price = get_price_element(html)
    price = price.get_text(strip=True)
    price = price.replace("€", "")
    price = price.replace(",", ".")

    price = safe_conversion_float(price)
    return price


def get_name(html):
    name = get_name_element(html).get_text(strip=True)
    if name.endswith(" lose"):
        name = name[:-5]

    if name.endswith(" Kräutertee"):
        name = name[:-1 * len(" Kräutertee")]

    elif name.endswith(" Tee"):
        name = name[:-4]
    return name


def get_weight(html):
    weight_element = get_weight_element(html)
    # text structure Doppelkammerbeutel 23,4 g
    weight = weight_element.get_text(strip=True).split()[-2]
    # replace comma with dot
    weight = weight.replace(",", ".")
    # convert to float

    weight = safe_conversion_float(weight)
    return weight



def get_tea_type(html, name):
    tea_type = get_tea_type_element(html).get_text(strip=True)

    match tea_type:
        case "Kräuter Mischungen":
            return "herbal"

        case "Kräuter Pur":
            return "herbal"

        case "Kalte Tees":
            return "iced tea"

        case "Früchtetees":
            return "fruit"

        case "Ingwer, Rooibos & Kurkuma":
            if "Rooibos".lower() in name.lower():
                return "rooibos"
            else:
                return "herbal"

        case "Chai & Gewürztees":
            return "chai"

        case "Schwarzer, Grüner & Weißer Tee":
            if "Schwarztee" in name:
                return "black"
            print(tea_type)

        case "Wohlfühl Tees":
            return "herbal"

        case "Kindertees Bio-Bengelchen":
            return "baby"

        case "Großgebinde":
            # TODO how to determine type
            print(tea_type)

        case _:
            return


def get_ingredients(html):
    ingredient_container = get_ingredient_container(html)
    ingredients = []
    for ingredient in ingredient_container:
        ingredient_text = ingredient.get_text(strip=True)

        if "%" in ingredient_text:
            ingredient_text = ingredient_text.replace(",", ".")
            # appears in ()
            match = re.search(r'\((\d+(?:\.\d+)?)%\)', ingredient_text)
            # replace comma
            ingredient_text = re.sub(r'\s*\(\d+(?:\.\d+)?%\)', '', ingredient_text).strip()
            percentage = safe_conversion_float(match.group(1))

        else:
            percentage = None

        if ingredient_text.endswith(" bio"):
            ingredient_text = ingredient_text[:-4]

        ingredient_data = insert_to_ingredient_data(ingredient_text, percentage)
        ingredients.append(ingredient_data)

    return ingredients


def populate_db():
    """
    data to add:
    Tea model:
    name
    image_url
    brand
    brand_page_url
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
    URL_PREFIX = "https://www.sonnentor.com/de-at/onlineshop/tee?page="
    tea_url_prefix = "https://www.sonnentor.com"
    page = 1

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
            products_to_ignore = ["https://www.sonnentor.com/de-at/onlineshop/tee/kraeuter-pur/kleine-kraeuterfibel",
                                  "https://www.sonnentor.com/de-at/onlineshop/geschenke/themenboxen/rein-in-den-fruehling-2025-themenbox-bio",
                                  "https://www.sonnentor.com/de-at/onlineshop/zubehoer-wissen/zubehoer/teesiebloeffel-mit-logo",
                                  "https://www.sonnentor.com/de-at/onlineshop/geschenke/geschenksets/teezeit-geschenkkarton-31-5x28-5x10-5-cm-bio2",
                                  "https://www.sonnentor.com/de-at/onlineshop/geschenke/ostern/frohe-ostern-geschenkset-14-5x13x6-cm-bio"]
            store_page_url = get_store_page_url(tea, tea_url_prefix)
            if store_page_url in products_to_ignore:
                continue

            tea_data["store_page_url"] = store_page_url

            # get tea store page url html
            driver = get_response_from_url(store_page_url, "")
            response = driver.page_source
            tea_store_page_html = get_html_from_response(response)
            driver.quit()
            #print(tea_store_page_html)

            # get the first h1
            # get brand from <a>
            brand = "sonnentor"
            store = brand
            tea_data["brand_page_url"] = store_page_url

            # need product-information__title js-toc__title font-black my-2 and get its text
            name = get_name(tea_store_page_html)
            # need col font-default-bold
            weight = get_weight(tea_store_page_html)
            # bag quantity data wysiwyg mt-4 product-information__contents
            bag_quantity = get_bag_quantity(tea_store_page_html)

            tea_data["brand"] = brand
            tea_data["store"] = store
            tea_data["name"] = name
            tea_data["weight"] = weight
            tea_data["bag_quantity"] = bag_quantity

            #get image url
            image_url = get_image_url(tea_store_page_html, tea_url_prefix)
            tea_data["image_url"] = image_url

            # get description
            description = get_description(tea_store_page_html)
            tea_data["description"] = description

            tea_type = get_tea_type(tea_store_page_html, name)
            tea_data["type"] = tea_type

            # get ingredients
            ingredients = get_ingredients(tea_store_page_html)
            tea_data["ingredients"] = ingredients

            # get price
            price = get_price(tea_store_page_html)
            tea_data["price"] = price

            print(f"\n{name}")
            for key in tea_data:
                if key == "ingredients":
                    for elem in tea_data[key]:
                        print(elem)
                else:
                    print(key, tea_data[key])

            time.sleep(1)
        page += 1


if __name__ == "__main__":
    populate_db()