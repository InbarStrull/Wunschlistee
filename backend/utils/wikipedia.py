import wikipedia

def get_wikipedia_url(term, language):
    wikipedia.set_lang(language)
    try:
        page = wikipedia.page(term).url
        return page

    except wikipedia.exceptions.PageError:
        return None

    # perhaps multiple pages for desired term, take the first suggestion
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            # take the first suggestion
            page = wikipedia.page(e.options[0]).url
            return page

        except Exception:
            return None

def get_wikipedia_page_url(ingredient_data):
    if ingredient_data['name_en']:
        ingredient_data['wikipedia_url'] = get_wikipedia_url(ingredient_data['name_en'], 'en')

    #return ingredient_data