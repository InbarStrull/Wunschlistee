from backend.utils.translation import google_translate
from backend.utils.string_operations import omit_asterix, handle_percentage_format, handle_percentage
from backend.util_functions import insert_to_ingredient_data


class Product:

    def __init__(self):
        self.brand = None
        self.brand_page_url = None
        self.store = None
        self.store_page_url = None
        self.name = None
        self.weight = None
        self.bag_quantity = None
        self.image_url = None
        self.description = None
        self.tea_type = None
        self.ingredients = None

    def manipulate_description(self, description, source_lang='de', target_lang='en'):
        description_en = google_translate(description, source_lang, target_lang)

        return description_en.strip()

    def manipulate_ingredients(self, ingredient_text, lang="de"):
        ingredient_text = omit_asterix(ingredient_text)
        ingredient_text = handle_percentage_format(ingredient_text)

        ingredients = []
        for ingredient in ingredient_text.split(","):
            try:
                ingredient_de, percentage = handle_percentage(ingredient)

                # remove .
                if ingredient_de[-1] == ".":
                    ingredient_de = ingredient_de[:-1]

                # remove ()
                if ingredient_de[0] == "(" and ingredient_de[-1] == ")":
                    ingredient_de = ingredient_de[1:-1]
                ingredient_data = insert_to_ingredient_data(ingredient_de.strip(), percentage, lang)
                ingredients.append(ingredient_data)

            except Exception as e:
                print(str(e))
                print(ingredient)

        return ingredients

    def get_name(self): raise NotImplementedError
    def get_description(self): raise NotImplementedError
    def get_weight(self): raise NotImplementedError
    def get_bag_quantity(self): raise NotImplementedError
    def get_image_url(self): raise NotImplementedError
    def get_tea_type(self): raise NotImplementedError
    def get_ingredients(self): raise NotImplementedError
