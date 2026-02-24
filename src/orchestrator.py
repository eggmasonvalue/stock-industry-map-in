import logging
import time
from typing import List, Set, Dict
from src.store import Store
from src.nse_client import NSEClient
from src.bse_client import BSEClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, store_path="out/industry_data.json", frequency="weekly"):
        self.store = Store(filepath=store_path)
        self.nse_client = NSEClient()
        self.bse_client = BSEClient()
        self._configure_retries(frequency)

    def _configure_retries(self, frequency):
        settings = {
            "daily": {"max_attempts": 5, "max_wait": 30},
            "weekly": {"max_attempts": 15, "max_wait": 90},
            "monthly": {"max_attempts": 30, "max_wait": 180}
        }
        config = settings.get(frequency, settings["weekly"])
        logger.info(f"Configuring retries for {frequency}: {config}")
        self.nse_client.set_retry_config(**config)
        self.bse_client.set_retry_config(**config)

    def _process_nse_securities(self, securities: List[Dict[str, str]]):
        """
        Process a list of NSE securities.
        Each item is a dict: {'symbol': '...', 'series': '...'}
        """
        total = len(securities)
        logger.info(f"Processing {total} NSE symbols...")

        for i, item in enumerate(securities):
            symbol = item['symbol']
            series = item['series']

            if symbol in self.store.data and self.store.data[symbol]:
                # Already processed
                continue

            logger.info(f"[{i+1}/{total}] Fetching info for NSE: {symbol} ({series})")
            info = self.nse_client.get_industry_info(symbol, series=series)

            if info:
                self.store.update_stock(symbol, info)
                logger.info(f"Updated {symbol}: {info}")
            else:
                logger.warning(f"No info found for NSE: {symbol} ({series})")

            if (i + 1) % 50 == 0:
                self.store.save()

    def _process_bse_securities(self, securities: List[dict]):
        total = len(securities)
        logger.info(f"Processing {total} BSE securities...")

        for i, sec in enumerate(securities):
            scrip_code = sec['scrip_code']
            symbol = sec['symbol']

            if symbol in self.store.data and self.store.data[symbol]:
                continue

            logger.info(f"[{i+1}/{total}] Fetching info for BSE: {symbol} ({scrip_code})")
            info = self.bse_client.get_industry_info(scrip_code, symbol=symbol)

            if info:
                self.store.update_stock(symbol, info)
                logger.info(f"Updated {symbol}: {info}")
            else:
                logger.warning(f"No info found for BSE: {symbol} ({scrip_code})")

            if (i + 1) % 50 == 0:
                self.store.save()

    def full_refresh(self):
        logger.info("Starting Full Refresh...")
        self.store.clear()

        # BSE (Process first)
        bse_secs = self.bse_client.get_securities()
        self._process_bse_securities(bse_secs)

        # NSE Mainboard
        # Optimization: process only if NOT already in store (populated by BSE)
        nse_main = self.nse_client.get_mainboard_symbols()
        # nse_main is list of {'symbol': ..., 'series': ...}
        nse_main_missing = [s for s in nse_main if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]

        if nse_main_missing:
            logger.info(f"Found {len(nse_main_missing)} missing/incomplete NSE Mainboard symbols (after BSE processing).")
            self._process_nse_securities(nse_main_missing)
        else:
            logger.info("All NSE Mainboard symbols already covered by BSE data.")

        # NSE SME
        nse_sme = self.nse_client.get_sme_symbols()
        nse_sme_missing = [s for s in nse_sme if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]

        if nse_sme_missing:
            logger.info(f"Found {len(nse_sme_missing)} missing/incomplete NSE SME symbols (after BSE processing).")
            self._process_nse_securities(nse_sme_missing)
        else:
             logger.info("All NSE SME symbols already covered by BSE data.")

        self.store.save()
        logger.info("Full Refresh Complete.")

    def refresh(self):
        logger.info("Starting Refresh...")
        self.store.load()

        # NSE Mainboard
        nse_main = self.nse_client.get_mainboard_symbols()
        nse_main_missing = [s for s in nse_main if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]
        if nse_main_missing:
            logger.info(f"Found {len(nse_main_missing)} missing/incomplete NSE Mainboard symbols.")
            self._process_nse_securities(nse_main_missing)

        # NSE SME
        nse_sme = self.nse_client.get_sme_symbols()
        nse_sme_missing = [s for s in nse_sme if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]
        if nse_sme_missing:
            logger.info(f"Found {len(nse_sme_missing)} missing/incomplete NSE SME symbols.")
            self._process_nse_securities(nse_sme_missing)

        # BSE
        bse_secs = self.bse_client.get_securities()
        bse_missing = [s for s in bse_secs if s['symbol'] not in self.store.data or not self.store.data[s['symbol']]]
        if bse_missing:
            logger.info(f"Found {len(bse_missing)} missing/incomplete BSE securities.")
            self._process_bse_securities(bse_missing)

        self.store.save()
        logger.info("Refresh Complete.")
