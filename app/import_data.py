import json
from schemas import TransactionIn


def load_transactions(path: str = "fake_data.json") -> list[TransactionIn]:
    with open(path, "r") as f:
        data = json.load(f)
    return [TransactionIn(**item) for item in data]
