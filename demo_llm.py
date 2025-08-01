import re
from datetime import datetime, timedelta

# Synonym map
ACTION_SYNONYMS = {
    "create": ["create", "generate", "make"],
    "delete": ["delete", "remove", "erase"],
    "update": ["update", "modify", "change"]
}

MONTH_MAP = {
    "jan": "01", "january": "01", "feb": "02", "february": "02",
    "mar": "03", "march": "03", "apr": "04", "april": "04",
    "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
    "aug": "08", "august": "08", "sep": "09", "september": "09",
    "oct": "10", "october": "10", "nov": "11", "november": "11",
    "dec": "12", "december": "12"
}

DEFAULTS = {
    "batch_name": "default_batch",
    "size": 100000,
    "expiry_date": (datetime.now().replace(day=1) + timedelta(days=32)).strftime("%m/%Y")
}

context = {
    "intent": None,
    "keywords": [],
    "values": {}
}

def normalize_action(text):
    for key, synonyms in ACTION_SYNONYMS.items():
        if any(word in text.lower() for word in synonyms):
            return key
    return None

def extract_keywords(text):
    for key, synonyms in ACTION_SYNONYMS.items():
        if any(word in text.lower() for word in synonyms):
            return [key, "batch"]
    return []

def extract_expiry_date(text):
    text = text.lower()
    for k, v in MONTH_MAP.items():
        if k in text:
            year_match = re.search(r"(\d{4})", text)
            if year_match:
                return f"{v}/{year_match.group(1)}"

    date_match = re.search(r"\b(0?[1-9]|1[0-2])[\/\-](\d{4})\b", text)
    if date_match:
        month = date_match.group(1).zfill(2)
        year = date_match.group(2)
        return f"{month}/{year}"

    if "today" in text:
        now = datetime.now()
        return f"{now.month:02d}/{now.year}"

    return None

def extract_size(text):
    all_numbers = re.findall(r"\b\d{2,11}\b", text)
    years = [str(y) for y in range(1900, 2101)]
    for num in all_numbers:
        if num not in years:
            return int(num)
    return None

def extract_batch_name(text):
    candidates = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text)
    reserved = set(["create", "generate", "batch", "delete", "update", "size", "expiry", "date", "default"])
    for c in candidates:
        if c.lower() not in reserved and not re.match(r"^\d{3,6}$", c):
            return c
    return None

def assign_defaults_if_requested(text):
    if "default" in text.lower():
        return DEFAULTS.copy()
    return {}

def parse_user_input(text):
    values = {}
    defaults = assign_defaults_if_requested(text)
    if defaults:
        return defaults

    expiry = extract_expiry_date(text)
    if expiry:
        values["expiry_date"] = expiry

    size = extract_size(text)
    if size:
        values["size"] = size

    name = extract_batch_name(text)
    if name:
        values["batch_name"] = name

    return {k: v for k, v in values.items() if v is not None}

def get_missing_fields(required, filled):
    return [field for field in required if field not in filled]

def respond_to_user(user_input):
    global context

    action = normalize_action(user_input)
    if action:
        context["intent"] = action
        context["keywords"] = extract_keywords(user_input)
        context["values"] = parse_user_input(user_input)

        missing = get_missing_fields(["batch_name", "size", "expiry_date"], context["values"])
        if missing:
            return f"What is the {', '.join(missing)}?"
        else:
            return show_result()

    if context["intent"]:
        more_values = parse_user_input(user_input)
        context["values"].update(more_values)

        missing = get_missing_fields(["batch_name", "size", "expiry_date"], context["values"])
        if missing:
            return f"Please provide: {', '.join(missing)}"
        else:
            return show_result()

    if user_input.lower() in ["hi", "hello"]:
        return "Hello! How can I help you with the batch operations?"

    return "Please ask a valid related question!"

def show_result():
    result = f"  \u27a4 Extracted keywords \u2192 {context['keywords']}\n"
    result += f"  \u27a4 Extracted values   \u2192 {context['values']}"
    context["intent"] = None
    context["keywords"] = []
    context["values"] = {}
    return result

if __name__ == "__main__":
    print("\U0001F4AC Smart Batch Bot Ready (type 'exit' to quit)")
    while True:
        user = input("You: ").strip()
        if user.lower() == "exit":
            print("\U0001F44B Goodbye!")
            break
        reply = respond_to_user(user)
        print("Bot:", reply)