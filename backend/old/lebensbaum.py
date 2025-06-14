from backend.utils import (handle_percentage_format,
                           get_response_from_url,
                           get_html_from_response,
                           remove_suffix,
                           get_suffix,
                           insert_to_ingredient_data,
                            safe_conversion_float,
                           google_translate,
                            handle_percentage,
                           contains_substring)
import re

def get_teas_from_html(html):
    return html.select("div.card-body.card-body-standard")


def get_tea_url_element(html):
    return html.select_one("a.product-name")


def get_name_element(html):
    return html.select_one("h1.product-detail-name")


def get_weight_element(html):
    return html.select_one("span.price-unit-content")


def get_bag_quantity_element(html):
    return html.select_one("p.product-detail-subline")


def get_image_url_element(html):
    return html.select_one("img.img-fluid.gallery-slider-image.magnifier-image.js-magnifier-image")


def get_description_element(html):
    return html.select_one("div.element-description__description.element-description__description--top")


def get_tea_type_element(html):
    return html.select_one("p.product-detail-overline")


def get_ingredient_element(html):
    return html.select_one('#ingredient-list')


def get_ingredients(html):
    ingredient_element = get_ingredient_element(html)
    notice = ingredient_element.select_one("div.element-ingredients__notice")
    if notice:
        notice.extract()

    ingredient_text = ingredient_element.get_text(strip=True)

    # remove asterix
    ingredient_text = re.sub(r"\*+", "", ingredient_text)
    ingredient_text = handle_percentage_format(ingredient_text)
    ingredients = []

    for ingredient in ingredient_text.split(","):
        ingredient_de, percentage = handle_percentage(ingredient)
        ingredient_data = insert_to_ingredient_data(ingredient_de, percentage)
        ingredients.append(ingredient_data)
    return ingredients


def get_tea_type(html):
    tea_type_element = get_tea_type_element(html)
    tea_type = tea_type_element.get_text(strip=True)
    cold = ["Kaltaufguss"]
    herbal = ["Kräuter-Früchteteemischung",
              "Früchte-Kräuterteemischung",
              "Kräuterteemischung",
              "Kräutertee"]
    black = ["Schwarztee"]
    green = ["Grüntee", "Grüner Tee"]
    fruit = ["Früchtetee", "Früchteteemischung", "Apfeltee"]
    rooibos = ["Rooibostee"]
    chai = ["Gewürzteemischung", "Chai"]
    white = ["Oolong"]
    mate = ["Matetee"]

    if contains_substring(tea_type, cold):
        return  "cold"

    elif contains_substring(tea_type, herbal):
        return "herbal"

    elif contains_substring(tea_type, black):
        return "black"

    elif contains_substring(tea_type, green):
        return "green"

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


def get_description(html):
    description_element = get_description_element(html)
    description_de = description_element.get_text(strip=True)
    description_en = google_translate(description_de, 'de', 'en')

    return description_en.strip()


def get_image_url(html):
    image_element = get_image_url_element(html)
    image = image_element["src"]
    return image


def get_bag_quantity(html):
    bag_quantity_element = get_bag_quantity_element(html)
    bag_quantity_text = bag_quantity_element.get_text(strip=True)
    bag_quantity = re.search(r'(\d+)\s*x', bag_quantity_text)
    return int(bag_quantity.group(1)) if bag_quantity else None


def get_weight(html):
    weight_element = get_weight_element(html)
    weight_text = weight_element.get_text(strip=True)
    # 60 Gramm for example, take first element
    weight = weight_text.split()[0]

    weight = safe_conversion_float(weight)
    return weight


def get_name(html):
    name_element = get_name_element(html)
    name = name_element.get_text(strip=True)
    name = remove_suffix(name, get_suffix(name, ", loser Tee"))
    name = remove_suffix(name, get_suffix(name, ", Teebeutel"))

    return name.strip()


def get_tea_url(html):
    tea_url_element = get_tea_url_element(html)
    tea_url = tea_url_element['href']
    return tea_url


def populate_db():

    URL_PREFIX = "https://www.lebensbaum.com/c/tee?order=topseller&limit=1000"

    driver = get_response_from_url(URL_PREFIX, "")
    response = driver.page_source
    html = get_html_from_response(response)
    driver.quit()
    # get all tea of current page, or break if no more teas are left
    teas = get_teas_from_html(html)
    for tea in teas:
        tea_data = dict()

        # get tea store page url
        products_to_ignore = ["https://www.lebensbaum.com/p/papier-teefilter-gr.-4-100-stueck",
                              "https://www.lebensbaum.com/p/papier-teefilter-gr.-2-100-stueck",
                              "https://www.lebensbaum.com/p/teenetze-gr.-2-9-cm",
                              "https://www.lebensbaum.com/p/zeit-zum-ausprobieren-mischbox-teebeutel"]
        brand_page_url = get_tea_url(tea)
        if brand_page_url in products_to_ignore or "tee-set" in brand_page_url:
            continue

        tea_data["brand_page_url"] = brand_page_url

        # get tea store page url html
        driver = get_response_from_url(brand_page_url, "")
        response = driver.page_source
        tea_store_page_html = get_html_from_response(response)
        driver.quit()
        #print(tea_store_page_html)

        # get the first h1
        # get brand from <a>
        brand = "lebensbaum"

        # need product-information__title js-toc__title font-black my-2 and get its text
        name = get_name(tea_store_page_html)
        # need col font-default-bold
        weight = get_weight(tea_store_page_html)
        # bag quantity data wysiwyg mt-4 product-information__contents
        bag_quantity = get_bag_quantity(tea_store_page_html)

        tea_data["brand"] = brand
        tea_data["name"] = name
        tea_data["weight"] = weight
        tea_data["bag_quantity"] = bag_quantity

        #get image url
        image_url = get_image_url(tea_store_page_html)
        tea_data["image_url"] = image_url

        # get description
        description = get_description(tea_store_page_html)
        tea_data["description"] = description

        tea_type = get_tea_type(tea_store_page_html)
        tea_data["type"] = tea_type

        # get ingredients
        ingredients = get_ingredients(tea_store_page_html)
        tea_data["ingredients"] = ingredients

        print(f"\n{name}")
        for key in tea_data:
            print(key, tea_data[key])




if __name__ == "__main__":
    populate_db()