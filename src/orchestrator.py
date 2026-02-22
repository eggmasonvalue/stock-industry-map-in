import logging
import time
from typing import List, Set
from src.store import Store
from src.nse_client import NSEClient
from src.bse_client import BSEClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, store_path="industry_data.json"):
        self.store = Store(filepath=store_path)
        self.nse_client = NSEClient()
        self.bse_client = BSEClient()

    def _process_nse_securities(self, symbols: List[str], is_sme: bool):
        total = len(symbols)
        logger.info(f"Processing {total} NSE symbols (SME={is_sme})...")

        for i, symbol in enumerate(symbols):
            if symbol in self.store.data:
                # Check if data is complete (non-null/non-empty)
                # But for full refresh, store is empty.
                # For refresh, we check if missing.
                pass

            # If not in store or store has partial data?
            # The logic for refresh is: check if a. entry exists b. entry isn't null.
            # Here I assume the caller handles filtering.

            logger.info(f"[{i+1}/{total}] Fetching info for NSE: {symbol}")
            info = self.nse_client.get_industry_info(symbol, is_sme=is_sme)

            if info:
                self.store.update_stock(symbol, info)
                logger.info(f"Updated {symbol}: {info}")
            else:
                logger.warning(f"No info found for NSE: {symbol}")
                # Maybe mark as processed but empty?
                # Store doesn't support empty explicit marker, but maybe we should store None?
                # The requirement says: "check whether a. The stock has an entry in the .json b. Stock's entries isn't null."
                # So if we don't store it, next refresh will try again. This is good.

            # Save periodically?
            if (i + 1) % 50 == 0:
                self.store.save()

    def _process_bse_securities(self, securities: List[dict]):
        total = len(securities)
        logger.info(f"Processing {total} BSE securities...")

        for i, sec in enumerate(securities):
            scrip_code = sec['scrip_code']
            symbol = sec['symbol'] # We use symbol as key?
            # Wait, user example: "RELIANCE": [...]
            # BSE has scrip code and scrip ID (symbol).
            # If a stock is on both, we might overwrite?
            # NSE symbol is RELIANCE. BSE symbol is RELIANCE.
            # If they are same, we overwrite.
            # User requirement: "maps stocks to their respective industry."
            # If a stock is listed on both, industry should be same.
            # If not, last write wins.
            # We should perhaps key by symbol.

            logger.info(f"[{i+1}/{total}] Fetching info for BSE: {symbol} ({scrip_code})")
            info = self.bse_client.get_industry_info(scrip_code)

            if info:
                self.store.update_stock(symbol, info) # Using Symbol as key
                logger.info(f"Updated {symbol}: {info}")
            else:
                logger.warning(f"No info found for BSE: {symbol} ({scrip_code})")

            if (i + 1) % 50 == 0:
                self.store.save()

    def full_refresh(self):
        logger.info("Starting Full Refresh...")
        self.store.clear()

        # BSE (Process first so NSE can overwrite if present, ensuring NSE terminology precedence)
        bse_secs = self.bse_client.get_securities()
        self._process_bse_securities(bse_secs)

        # NSE Mainboard
        nse_main = self.nse_client.get_mainboard_symbols()
        self._process_nse_securities(nse_main, is_sme=False)

        # NSE SME
        nse_sme = self.nse_client.get_sme_symbols()
        self._process_nse_securities(nse_sme, is_sme=True)

        self.store.save()
        logger.info("Full Refresh Complete.")

    def refresh(self):
        logger.info("Starting Refresh...")
        self.store.load()

        # We need to fetch the list of all securities to know what to check.
        # Logic:
        # 1. Fetch current list of securities from exchanges.
        # 2. Compare with store.
        # 3. Identify targets: not in store OR store entry is null (or incomplete).

        # NSE Mainboard
        nse_main = self.nse_client.get_mainboard_symbols()
        nse_main_missing = [s for s in nse_main if s not in self.store.data or not self.store.data[s]]
        if nse_main_missing:
            logger.info(f"Found {len(nse_main_missing)} missing/incomplete NSE Mainboard symbols.")
            self._process_nse_securities(nse_main_missing, is_sme=False)

        # NSE SME
        nse_sme = self.nse_client.get_sme_symbols()
        nse_sme_missing = [s for s in nse_sme if s not in self.store.data or not self.store.data[s]]
        if nse_sme_missing:
            logger.info(f"Found {len(nse_sme_missing)} missing/incomplete NSE SME symbols.")
            self._process_nse_securities(nse_sme_missing, is_sme=True)

        # BSE
        bse_secs = self.bse_client.get_securities()
        bse_missing = [s for s in bse_secs if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]
        if bse_missing:
            logger.info(f"Found {len(bse_missing)} missing/incomplete BSE securities.")
            self._process_bse_securities(bse_missing)

        self.store.save()
        logger.info("Refresh Complete.")
