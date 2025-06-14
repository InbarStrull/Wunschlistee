from deep_translator import GoogleTranslator
import difflib
from openai import OpenAI
import os
from transformers import pipeline
import requests
from backend.utils.string_operations import contains_substring, get_suffix, remove_suffix

API_KEY = os.getenv("OPENAI_API_KEY")
CLIENT = OpenAI(api_key=API_KEY)

LANGS = ['iw', 'en', 'de'] # supporting hebrew, english, german
LANG_DICT = {'iw': 'Hebrew', 'en': 'English', 'de': 'German'}

# known ingredients for translation refernce
INGREDIENT_CONTEXT_DE = [
    "Grüner Tee", "Schwarzer Tee", "Kamille", "Melisse", "Zitronenverbene", "Süßholz",
    "Pfefferminze", "Hagebutte", "Fenchel", "Anis", "Zimt", "Ingwer", "Kurkuma",
    "Kardamom", "Nelken", "Brennnessel", "Lemongras", "Lavendel"
]

INGREDIENT_CONTEXT_EN = [
    "green tea", "black tea", "chamomile", "lemon balm", "lemon verbena", "licorice root",
    "peppermint", "rosehip", "fennel", "anise", "cinnamon", "ginger", "turmeric",
    "cardamom", "cloves", "nettle", "lemongrass", "lavender"
]

INGREDIENT_CONTEXT_HE = [
    "תה ירוק", "תה שחור", "קמומיל", "מליסה", "לואיזה", "שורש ליקוריץ",
    "נענע", "ורדים", "שומר", "אניס", "קינמון", "ג'ינג'ר", "כורכום",
    "הל", "ציפורן", "סרפד", "לימונית", "לבנדר"
]

INGREDIENT_CONTEXT_DICT = {"en": INGREDIENT_CONTEXT_EN, "iw": INGREDIENT_CONTEXT_HE}

def google_translate(text_source, source_language, target_language):
    return GoogleTranslator(source=source_language, target=target_language).translate(text=text_source)


def translate_with_context(text_source, source_language, target_language):
    # add the current text to the list
    temp_list = INGREDIENT_CONTEXT_DE + [text_source]
    context_string = ", ".join(temp_list)

    # translate the full list
    full_translation = google_translate(context_string, source_language, target_language)

    # get the translation of the source text (last element)
    translated_items = [item.strip() for item in full_translation.split(",")]

    return translated_items[-1] if translated_items else ""


# find the closest to context translation
def disambiguate_translation(translated_text, context):
    best_match = difflib.get_close_matches(translated_text, INGREDIENT_CONTEXT_DE, n=1, cutoff=0.6)
    return best_match[0] if best_match else translated_text  # fallback to raw if no match


def get_name_translation(ingredient_data, ingredient, language):
    #ingredient_data["en"] = llm_translation(ingredient, "en", "de")
    #ingredient_data["iw"] = llm_translation(ingredient, "iw", "en")
    for lang in LANGS:
        if lang == language:
            ingredient_data[f"name_{lang}"] = ingredient
            continue

        #ingredient_data[f"name_{lang}"] = translate_with_context(ingredient, language, lang)
        #ingredient_data[f"name_{lang}"] = llm_translation(ingredient, lang, language)
        ingredient_data[f"name_{lang}"] = google_translate(ingredient, language, lang)
        #ingredient_data[f"name_{lang}"] = my_memory_api_translation(ingredient, lang, language)
        #ingredient_data[f"name_{lang}"] = disambiguate_translation(ingredient_data[f"name_{lang}"], INGREDIENT_CONTEXT_DICT[lang])
        #ingredient_data[f"name_{lang}"] = prompt_translation(ingredient, LANG_DICT[lang])
        # if translation fails, add name as None
        #try:
            #ingredient_data[f"name_{lang}"] = google_translate(ingredient, language, lang)

        #except Exception:
            #ingredient_data[f"name_{lang}"] = ""


    return ingredient_data


def translate_from_ingredient_dict(ingredient_dict, language='de'):
    ingredient_list_source = list(ingredient_dict.keys())
    ingredient_text_source = (", ").join(ingredient_list_source)
    for lang in LANGS:
        if lang != language:
            translated_text = google_translate(ingredient_text_source,language, lang)
            ingredient_list_target = translated_text.split(", ")
            # add translations to ingredient data
            for ingredient_target, ingredient_source in zip(ingredient_list_target, ingredient_list_source):
                ingredient_dict[ingredient_source][lang] = ingredient_target

    ingredient_list = list(ingredient_dict.values())
    return ingredient_list


def prompt_translation(ingredient, target_language, source_language='German'):
    prompt = f"Translate this tea ingredient from {source_language} to {target_language}: '{ingredient}'. Only return the Hebrew translation."

    response = CLIENT.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a translation assistant."},
            {"role": "user", "content": prompt}
        ]
    )


    return response.choices[0].message.content


def llm_translation(ingredient, target_language, source_language='de'):
    translator = pipeline("translation", model=f"Helsinki-NLP/opus-mt-{source_language}-{target_language}")
    result = translator(ingredient, max_length=100)
    return result


def my_memory_api_translation(text_source, target_language, source_language='de',):
    source_text_without_tee_prefix = ["blüten", "schalen", "blätter"]
    if not contains_substring(text_source, source_text_without_tee_prefix) and target_language == "he":
        # works better with Tee suffix
        text_source = f"{text_source} Tee"

    # my memory translation request
    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text_source,
        "langpair": f"{source_language}|{target_language}"
    }

    # response
    response = requests.get(url, params=params)
    data = response.json()

    # get translation
    try:
        raw_translation = data["responseData"]["translatedText"]

    except KeyError:
        return None

    # process translation
    return extract_translation_from_response(raw_translation)

def extract_translation_from_response(translation):
    # ? appears when the translation is not accurate, we don't care
    translation = translation.replace("?", "")

    # remove תה suffix or leave text as it is
    return remove_suffix(translation, get_suffix(translation, " תה"))