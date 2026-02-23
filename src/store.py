import json
import os
from typing import Dict, List, Any

# JSON Structure:
# {
#   "metadata": ["Macro", "Sector", "Industry", "Basic Industry"],
#   "data": {
#     "SYMBOL": ["Macro Value", "Sector Value", "Industry Value", "Basic Industry Value"]
#   }
# }

class Store:
    def __init__(self, filepath: str = "out/industry_data.json"):
        self.filepath = filepath
        self.metadata = ["Macro", "Sector", "Industry", "Basic Industry"]
        self.data: Dict[str, List[str]] = {}

    def load(self):
        """Loads data from the JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # Validate structure
                    if "metadata" in content and "data" in content:
                        self.metadata = content["metadata"]
                        self.data = content["data"]
                    else:
                        print(f"Warning: Invalid JSON structure in {self.filepath}. Starting fresh.")
                        self.data = {}
            except json.JSONDecodeError:
                print(f"Warning: Failed to decode JSON from {self.filepath}. Starting fresh.")
                self.data = {}
        else:
            print(f"Info: {self.filepath} not found. Starting fresh.")
            self.data = {}

    def save(self):
        """Saves data to the JSON file."""
        content = {
            "metadata": self.metadata,
            "data": self.data
        }

        # Ensure directory exists
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as e:
                print(f"Error creating directory {directory}: {e}")
                return

        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"Saved data to {self.filepath}")

    def update_stock(self, symbol: str, info: List[str]):
        """Updates industry info for a stock."""
        if len(info) != 4:
            print(f"Warning: Invalid info length for {symbol}. Expected 4, got {len(info)}.")
            return
        self.data[symbol] = info

    def get_stock(self, symbol: str) -> List[str]:
        """Returns industry info for a stock, or None if not found."""
        return self.data.get(symbol)

    def clear(self):
        """Clears all data."""
        self.data = {}
