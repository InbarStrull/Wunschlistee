import re

from .conversions import safe_conversion_float

def get_and_remove_suffix(name, suffix, return_value=None):
    return remove_suffix(name, get_suffix(name, suffix, return_value))


def get_and_remove_suffixes(name, suffixes):
    for suffix in suffixes:
        name = get_and_remove_suffix(name, suffix)

    return name


def get_suffix(name, suffix, return_value=None):
    if not return_value:
        return_value = suffix

    if name.endswith(suffix):
        return return_value

    return ""


def remove_suffix(name, suffix):
    if suffix:
        name = name[:(-1) * len(suffix)]

    return name


def get_prefix(name, prefix, return_value):
    if name.endswith(prefix):
        return return_value

def contains_substring(input_string, substrings):
    contains = any(substring in input_string for substring in substrings)
    return contains


def handle_percentage_format(ingredient_text):
    # handle percentage format
    ingredient_text = ingredient_text.replace(" %", "%")    # remove space between number and %
    ingredient_text = replace_comma_with_dot(ingredient_text) # replace german decimal comma with dot
    #ingredient_text = re.sub(r'\((\d+(?:\.\d+)?)%\)', r'\1%', ingredient_text) # remove () from percentage
    # new
    if "))" in ingredient_text:
        ingredient_text = ingredient_text.replace("))", ")")
    ingredient_text = re.sub(r'\(\s*(\d+(?:\.\d+)?)%\s*\)', r'\1%', ingredient_text)
    # remove extra (, )
    return ingredient_text


def replace_comma_with_dot(text):
    text = re.sub(r'(?<=\d),(?=\d\s*)', '.', text)  # replace german decimal comma with dot
    return text


def add_space_between_digit_and_character(ingredient):
    for i, char in enumerate(ingredient):
        if char.isdigit():
            return ingredient[:i] + ' ' + ingredient[i:]
    return ingredient


def handle_percentage(ingredient):
    ingredient = ingredient.strip()
    percentage_sign = "%"
    dot = "."
    percentage_dot = f"{percentage_sign}{dot}"

    # check percentage
    # if %  or %. appears in the end
    #print("hi", ingredient)
    if ingredient[-1] == percentage_sign or ingredient[-2:] == percentage_dot:
        if ingredient[-2:] == percentage_dot:
            to_replace = percentage_dot
        else:
            to_replace = percentage_sign

        # add space between number and ingredient

        if " " not in ingredient:
            ingredient = add_space_between_digit_and_character(ingredient)

        # split ingredient into to parts from the right
        try:
            ingredient_de, percentage = ingredient.rsplit(" ", 1)

        except ValueError:
            # ingredient and percentage are not separated by a space
            # find the index of the first numeric digit and split accordingly
            match = re.search(r'\d', ingredient)
            index = match.start() if match else -1
            # split according to that index
            ingredient_de, percentage = ingredient[:index], ingredient[index:]
        # remove % or %.
        percentage = percentage.replace(to_replace, "")


    # if % appears in a different place
    elif percentage_sign in ingredient:
        percentage, ingredient_de = ingredient.split(percentage_sign)

    # no %
    else:
        ingredient_de, percentage = ingredient, None

    # convert percentage to float
    percentage = safe_conversion_float(percentage)

    return ingredient_de, percentage



def omit_asterix(text):
    # first make sure the asterix has a space after it
    text = re.sub(r'\*+(?!\s)', '* ', text)
    text = re.sub(r"\*+", "", text)
    return text


def get_first_occurrence_of_digit_reversed(text):
    for c in range(len(text) - 1, -1, -1):
        if not text[c].isdigit():
            return c

    return -1


def replace_texts(string, old_texts, new_text=""):
    for text in old_texts:
        string = string.replace(text, new_text)

    return string


def split_text(string, texts_to_split_by, index=0):
    for text in texts_to_split_by:
        string = string.split(text)[index]

    return string