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


"""
    def manipulate_ingredients(self, ingredient_text, lang="de"):

        ingredient_text = omit_asterix(ingredient_text)
        ingredient_text = handle_percentage_format(ingredient_text)

        ingredients = dict()
        for ingredient in ingredient_text.split(","):
            try:
                ingredient_de, percentage = handle_percentage(ingredient)

                # remove .
                if ingredient_de[-1] == ".":
                    ingredient_de = ingredient_de[:-1]

                # remove ()
                if ingredient_de[0] == "(" and ingredient_de[-1] == ")":
                    ingredient_de = ingredient_de[1:-1]
                #ingredient_data = insert_to_ingredient_data(ingredient_de.strip(), percentage, lang)
                ingredient_data = {"de": ingredient_de, "percentage": percentage}
                ingredients[ingredient_de] = ingredient_data

            except Exception as e:
                print(str(e))
                print(ingredient)

        ingredient_list = translate_from_ingredient_dict(ingredients)


        return ingredient_list
"""


{'exception_code': None, 'matches': [{'create-date': '2025-05-22 14:03:18', 'created-by': 'MT!', 'id': 0, 'last-update-date': '2025-05-22 14:03:18', 'last-updated-by': 'MT!', 'match': 0.85, 'model': 'neural', 'penalty': None, 'quality': 70, 'reference': 'Machine Translation.', 'segment': 'Brennnesselblätter', 'source': 'he-IL', 'subject': False, 'target': 'de-DE', 'translation': 'Brennnesselblätter', 'usage-count': 2}], 'mtLangSupported': None, 'quotaFinished': False, 'responderId': None, 'responseData': {'match': 0.85, 'translatedText': 'Brennnesselblätter'}, 'responseDetails': '', 'responseStatus': 200}
