def safe_conversion_float(text):
    if text:
        try:
            text = float(text)
            return text

        except (ValueError, AttributeError) as e:
            print(str(e))


def safe_conversion_int(text):
    if text:
        try:
            text = int(text)
            return text

        except (ValueError, AttributeError) as e:
            print(str(e))