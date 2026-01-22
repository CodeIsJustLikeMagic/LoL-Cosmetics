import re

def ensure_exists(dictionary: dict, key: str|int, default_value):
    if key not in dictionary:
        dictionary[key] = default_value


def remove_date(text):
    return re.sub(r'(?:(?:19|20)\d\d)', "", text)