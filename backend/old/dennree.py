from backend.util_functions import create_ingredient_data, insert_to_ingredient_data
from backend.utils.string_operations import remove_suffix, get_suffix, handle_percentage, handle_percentage_format
from backend.utils.conversions import safe_conversion_int, safe_conversion_float
from backend.utils.translation import google_translate
from backend.utils.scraping import get_response_from_url_without_driver, get_html_from_response

def get_name_type_element(tea):
    return tea.select_one('p')


def get_brand_page_url_element(tea):
    print(tea)
    return tea.select_one('a')


def get_tea_image_element(tea):
    img_tag = tea.find('div', class_='productImage').find('img')
    return img_tag


def get_tea_info(tea):
    core_info = tea.find('div', class_="row coreInfo")
    return core_info.find('div', class_="col-md-6")


def get_description_element(core_info):
    return core_info.select('p')[1]


def get_quantity_element(core_info):
    return core_info.select('p')[2]


def get_ingredient_element(core_info):
    return core_info.select('p')[4]


def get_brand_page_url(tea, prefix):
    #tea_brand_page_url = get_brand_page_url_element(tea)
    tea_brand_page_url = tea['href']
    return f"{prefix}{tea_brand_page_url}"


def get_name(name_and_type, type_suffix, tea_type):
    name = remove_name_suffix(name_and_type, type_suffix, tea_type)
    if not name:
        name = type_suffix

    return name.strip()


def get_description(info):
    description_element = get_description_element(info)
    description_de = description_element.get_text(strip=True)
    description_en = google_translate(description_de,'de', 'en')
    return description_en


def get_quantity(info):
    # x Blt or x g
    # take first element
    quantity_element = get_quantity_element(info)
    quantity_text = quantity_element.get_text(strip=True)
    quantity = quantity_text.split()[0]

    quantity = safe_conversion_float(quantity)
    return quantity


def is_grams(info):
    # if false than tea bags
    quantity_element = get_quantity_element(info)
    quantity_text = quantity_element.get_text(strip=True)
    unit = quantity_text.split()[1]

    return unit == "g"


def get_weight_suffix(name_and_type):
    # only 500 g appears in name
    if name_and_type.endswith(", 500 g"):
        return ", 500 g"

    return ""


def get_lose_suffix(name_and_type):
    return get_suffix(name_and_type, ", lose")


def get_type(type_suffix):
    #herbal = ["Kräuter-Gewürztee", "Kräutertee", "tee"]
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


def remove_name_suffix(name, type_suffix, tea_type):
    # dm gives teas name with the type of the tee as a prefix
    # for the tea named Krautertee and Früchteteemischung
    if not name and type_suffix and tea_type:
        return type_suffix

    if tea_type == "roiboos":
        return remove_suffix(name, "tee")

    else:
        return remove_suffix(name, type_suffix)


def remove_weight_suffix(name):
    weight_suffix = get_weight_suffix(name)
    return remove_suffix(name, weight_suffix)


def remove_lose_suffix(name):
    lose_suffix = get_lose_suffix(name)
    return remove_suffix(name, lose_suffix)


def get_type_suffix(name_type):
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


def get_tea_image_url(tea):
    image_element = get_tea_image_element(tea)
    image_url = image_element['src']
    return image_url


def get_bag_quantity(info):
    grams = is_grams(info)
    if not grams:
        bag_quantity = get_quantity(info)
        bag_quantity = safe_conversion_int(bag_quantity)
        return bag_quantity


def get_weight(info):
    grams = is_grams(info)
    if grams:
        weight = get_quantity(info)
        return weight


def get_ingredients(info):
    ingredients_element = get_ingredient_element(info)
    ingredient_text = ingredients_element.get_text(strip=True)

    # remove asterix
    ingredient_text = ingredient_text.replace("*", "")
    ingredient_text = handle_percentage_format(ingredient_text)
    ingredients = []

    for ingredient in ingredient_text.split(","):
        ingredient_de, percentage = handle_percentage(ingredient)
        ingredient_data = insert_to_ingredient_data(ingredient_de, percentage)
        ingredients.append(ingredient_data)
    return ingredients


def populate_db():
    URL_PREFIX = "https://www.dennree.de/productreload?id=118&category=257&pid=390&offset=0&count=100"
    tea_url_prefix = "https://www.dennree.de"
    response = get_response_from_url_without_driver(URL_PREFIX)
    html = get_html_from_response(response)
    teas = html.select('div.teaser a')

    for tea in teas:
        tea_data = dict()
        brand = "dennree"

        tea_data["brand"] = brand

        name_type = get_name_type_element(tea).get_text(strip=True)
        #weight_suffix = get_weight_suffix(name_type)
        #lose_suffix = get_lose_suffix(name_type)
        name_type = remove_weight_suffix(remove_lose_suffix(name_type))
        type_suffix = get_type_suffix(name_type)
        tea_type = get_type(type_suffix)
        name = get_name(name_type, type_suffix, tea_type)

        brand_page_url = get_brand_page_url(tea, tea_url_prefix)

        tea_data["name"] = name
        tea_data["type"] = "rooibos" if "rooibos" in name.lower() else tea_type
        tea_data["brand_page_url"] = brand_page_url

        brand_page = get_response_from_url_without_driver(brand_page_url)
        brand_page_html = get_html_from_response(brand_page)
        image_url = get_tea_image_url(brand_page_html)
        tea_data["image_url"] = image_url

        info = get_tea_info(brand_page_html)
        weight = get_weight(info)
        bag_quantity = get_bag_quantity(info)
        description = get_description(info)
        ingredients = get_ingredients(info)


        tea_data["weight"] = weight
        tea_data["bag_quantity"] = bag_quantity
        tea_data["description"] = description
        tea_data["ingredients"] = ingredients

        print(f"\n{name}")
        for key in tea_data:
            print(key, tea_data[key])


if __name__ == "__main__":
    populate_db()
