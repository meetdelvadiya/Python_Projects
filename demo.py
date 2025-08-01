import re

# Define your keywords
action_keywords = {"create", "delete", "update", "add"}
entity_keywords = {"batch", "tablet", "cavity", "blister"}
slot_keywords = {"size", "expiry", "expiry date"}

# Chatbot state
chat_state = {
    "action": None,
    "entity": None,
    "slots": {}
}

def extract_keywords(text, keyword_set):
    words = set(re.findall(r'\w+', text.lower()))
    return words.intersection(keyword_set)

def handle_user_input(text):
    global chat_state

    # Exit condition
    if text.lower() in {"exit", "quit"}:
        return "exit"

    # Step 1: Check for known keywords
    has_valid_keywords = extract_keywords(
        text, action_keywords.union(entity_keywords).union(slot_keywords)
    )
    if not has_valid_keywords and not (chat_state["action"] and chat_state["entity"]):
        return "Please ask a valid related question!"

    # Step 2: Intent detection
    if not chat_state["action"] or not chat_state["entity"]:
        action = extract_keywords(text, action_keywords)
        entity = extract_keywords(text, entity_keywords)

        if action:
            chat_state["action"] = list(action)[0]
        if entity:
            chat_state["entity"] = list(entity)[0]

        if chat_state["action"] and chat_state["entity"]:
            return f"What is the size and what is the expiry date of the {chat_state['entity']}?"
        else:
            return "Please mention what you want to do and on what (e.g., create batch)."

    # Step 3: Slot filling
    # Slot filling
    if chat_state["action"] and chat_state["entity"]:
        # Match size (more flexible)
        size_match = re.search(r"(size|batch size)[^\d]*(\d+)", text.lower())

        # Match expiry date (accepts mm/yyyy, dd-mm-yyyy, Month yyyy, etc.)
        expiry_match = re.search(r"(expiry\s*(date)?\s*(is)?\s*)?([a-zA-Z]+\s*\d{4}|\d{1,2}[\/\-]\d{4})", text.lower())

        if size_match:
            chat_state["slots"]["size"] = size_match.group(2)
        if expiry_match:
            # Pick the actual matched date part
            chat_state["slots"]["expiry_date"] = expiry_match.group(4)

        if "size" in chat_state["slots"] and "expiry_date" in chat_state["slots"]:
            keywords = [
                chat_state["action"],
                chat_state["entity"],
                "size",
                "expiry date"
            ]
            final_data = {
                "keywords": keywords,
                "values": chat_state.copy()
            }
            # Reset for next conversation
            chat_state = {"action": None, "entity": None, "slots": {}}
            return final_data
        else:
            return "Waiting for more info: size or expiry date missing."


# 👇 Interactive Chat Loop
if __name__ == "__main__":
    print("💬 Chatbot is ready! Type your message (type 'exit' to quit).")
    while True:
        user_input = input("You: ")
        response = handle_user_input(user_input)
        if response == "exit":
            print("👋 Chatbot session ended.")
            break
        print("Bot:", response)
