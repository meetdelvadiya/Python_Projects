import re
from difflib import get_close_matches
from datetime import datetime, timedelta
import calendar

valid_keywords = ["create", "delete", "update", "batch", "tablet", "cavity", "blister", "size", "expiry date"]
synonym_map = {
    "generate": "create", "make": "create", "start": "create",
    "remove": "delete", "drop": "delete", "change": "update"
}
greetings = {"hi", "hello", "hey"}

def normalize_month_year(text):
    months = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    months.update({m[:3].lower(): i for m, i in months.items()})
    now = datetime.now()
    year = now.year
    tokens = re.findall(r'\w+', text.lower())
    for token in tokens:
        if token in months:
            month = months[token]
            if month <= now.month:
                year += 1
            return f"{month:02d}/{year}"
        if re.match(r'\d{1,2}/\d{2,4}', token):
            return token
        if token == "today":
            return datetime.now().strftime("%m/%Y")
    return None

def default_expiry_date():
    today = datetime.today()
    next_month = today.replace(day=1) + timedelta(days=32)
    return next_month.strftime("%m/%Y")

def fuzzy_keyword_extraction(text):
    tokens = re.findall(r'\w+', text.lower())
    extracted = set()
    for token in tokens:
        if token in greetings:
            return ["greeting"]
        canonical = synonym_map.get(token, token)
        match = get_close_matches(canonical, valid_keywords, n=1, cutoff=0.8)
        if match:
            extracted.add(match[0])
    return list(extracted)

def extract_batch_name(text):
    match = re.search(r"batch(?: name)?(?: is|=)?\s*([a-zA-Z0-9_-]+)", text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_size(text):
    match = re.search(r"size(?: is|=)?\s*(\d{2,})", text, re.IGNORECASE)
    return int(match.group(1)) if match else (
        int(text) if text.strip().isdigit() else None
    )

def extract_expiry_date(text):
    match = re.search(r"expiry date(?: is|=)?\s*([a-zA-Z0-9/ ]+)", text, re.IGNORECASE)
    if match:
        return normalize_month_year(match.group(1))
    return normalize_month_year(text)

def is_valid_question(text):
    tokens = re.findall(r'\w+', text.lower())
    return any(token in set(valid_keywords + list(synonym_map.keys()) + list(greetings)) for token in tokens)

def parse_inline_input(text):
    parts = [p.strip() for p in re.split(r'[,\n]+', text)]
    result = {"batch_name": None, "size": None, "expiry_date": None}
    for p in parts:
        if not result["batch_name"]:
            result["batch_name"] = extract_batch_name(p) or (p if not extract_size(p) and not extract_expiry_date(p) else None)
        if not result["size"]:
            result["size"] = extract_size(p)
        if not result["expiry_date"]:
            result["expiry_date"] = extract_expiry_date(p)
    return result

# === Main Chat Loop ===
if __name__ == "__main__":
    print("💬 Smart Chatbot with Value Assignment — type 'exit' to quit\n")

    awaiting_info = False
    pending_slots = {"batch_name": None, "size": None, "expiry_date": None}
    last_action = None

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Bye!")
            break

        # Handle greetings
        if user_input.lower() in greetings:
            print("Bot: Hi! How can I help you today?")
            continue

        # When awaiting more data
        if awaiting_info:
            if user_input.lower() == "default":
                pending_slots = {
                    "batch_name": "default_batch",
                    "size": 100000,
                    "expiry_date": default_expiry_date()
                }
            else:
                parsed = parse_inline_input(user_input)
                for k in pending_slots:
                    if not pending_slots[k] and parsed.get(k):
                        pending_slots[k] = parsed[k]

            # Final check
            missing = [k.replace("_", " ") for k, v in pending_slots.items() if v is None]
            if missing:
                print(f"Bot: Please provide: {', '.join(missing)}")
                continue
            else:
                print("Bot:")
                print("  ➤ Extracted keywords →", [last_action, "batch"])
                print("  ➤ Extracted values   →", pending_slots)
                pending_slots = {"batch_name": None, "size": None, "expiry_date": None}
                awaiting_info = False
                continue

        # Start of new request
        if not is_valid_question(user_input):
            print("Bot: Please ask a valid related question!")
            continue

        keywords = fuzzy_keyword_extraction(user_input)

        if "greeting" in keywords:
            print("Bot: Hi! How can I help you today?")
            continue

        if "batch" not in keywords:
            print("Bot: Please mention a batch operation (e.g., create batch).")
            continue

        if "create" in keywords:
            last_action = "create"
            parsed = parse_inline_input(user_input)
            for k in pending_slots:
                pending_slots[k] = parsed.get(k)

            missing = [k.replace("_", " ") for k, v in pending_slots.items() if v is None]
            if missing:
                print(f"Bot: What is the {', '.join(missing)}?")
                awaiting_info = True
                continue
            else:
                print("Bot:")
                print("  ➤ Extracted keywords →", keywords)
                print("  ➤ Extracted values   →", pending_slots)
                pending_slots = {"batch_name": None, "size": None, "expiry_date": None}
                continue

        elif "delete" in keywords:
            name = extract_batch_name(user_input)
            if name:
                print("Bot:")
                print("  ➤ Extracted keywords →", keywords)
                print(f"  ➤ Extracted values   → {{'batch_name': '{name}'}}")
            else:
                print("Bot: Please provide the batch name to delete.")
            continue

        else:
            print("Bot: Currently only supports 'create' or 'delete' batch.")
