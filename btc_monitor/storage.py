"""
Signal storage - JSON file persistence
"""

import json
import os
from typing import List, Dict


class SignalStorage:
    """Simple JSON storage for trading signals"""

    def __init__(self, symbol: str = None, filepath: str = None):
        """
        Initialize storage

        Args:
            symbol: Trading symbol (e.g., BTCUSDT) - will create symbol-specific file
            filepath: Path to JSON log file (overrides symbol-based naming)
        """
        if filepath:
            self.filepath = filepath
        elif symbol:
            self.filepath = f'signals_{symbol}.json'
        else:
            self.filepath = 'signals_log.json'

    def save_signal(self, signal: Dict) -> bool:
        """
        Save a trading signal to log file

        Args:
            signal: Dictionary containing signal data

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Load existing logs
            logs = self.load_all()

            # Add new signal
            logs.append(signal)

            # Save to file
            with open(self.filepath, 'w') as f:
                json.dump(logs, f, indent=2, default=str)

            print(f"💾 Signal saved to {self.filepath}")
            return True

        except Exception as e:
            print(f"❌ Error saving signal: {e}")
            return False

    def load_all(self) -> List[Dict]:
        """
        Load all signals from log file

        Returns:
            List of signal dictionaries
        """
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading signals: {e}")
            return []

    def get_latest(self, n: int = 10) -> List[Dict]:
        """
        Get the latest N signals

        Args:
            n: Number of signals to retrieve

        Returns:
            List of latest signal dictionaries
        """
        logs = self.load_all()
        return logs[-n:] if logs else []
