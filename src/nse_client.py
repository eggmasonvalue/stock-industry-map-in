import csv
import io
import time
from typing import Dict, List, Optional
import requests
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type
from nse import NSE
import os

class NSEClient:
    def __init__(self, download_folder="./temp_downloads"):
        os.makedirs(download_folder, exist_ok=True)
        self.nse = NSE(download_folder=download_folder)
        self.base_url = "https://www.nseindia.com/api"
        # Default retry settings (weekly)
        self.max_attempts = 15
        self.max_wait = 90

    def set_retry_config(self, max_attempts: int, max_wait: int):
        self.max_attempts = max_attempts
        self.max_wait = max_wait

    def _fetch_url(self, url, params=None):
        """Fetches a URL with retries."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
            reraise=True
        )
        try:
            return retryer(self.nse._req, url, params=params)
        except Exception as e:
            raise e

    def _fetch_symbol_data_with_retry(self, symbol, series):
        """Fetches symbol data with retries using fetch_symbol_data."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
            reraise=True
        )
        try:
            # fetch_symbol_data might raise exceptions which are retryable
            return retryer(self.nse.fetch_symbol_data, symbol, series)
        except Exception as e:
            raise e

    def get_mainboard_symbols(self) -> List[str]:
        """Fetches Mainboard symbols from CSV."""
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        print(f"Fetching Mainboard CSV from {url}...")
        try:
            response = self._fetch_url(url)
            if response.status_code == 200:
                csv_content = response.content.decode('utf-8')
                reader = csv.DictReader(io.StringIO(csv_content))
                symbols = [row['SYMBOL'] for row in reader]
                return symbols
            else:
                print(f"Failed to fetch Mainboard CSV: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching Mainboard CSV: {e}")
            return []

    def get_sme_symbols(self) -> List[str]:
        """Fetches SME symbols from CSV."""
        url = "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"
        print(f"Fetching SME CSV from {url}...")
        try:
            response = self._fetch_url(url)
            if response.status_code == 200:
                csv_content = response.content.decode('utf-8')
                reader = csv.DictReader(io.StringIO(csv_content))
                symbols = [row['SYMBOL'] for row in reader]
                return symbols
            else:
                print(f"Failed to fetch SME CSV: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching SME CSV: {e}")
            return []

    def get_industry_info(self, symbol: str, is_sme: bool = False) -> Optional[List[str]]:
        """
        Fetches industry info for a symbol using fetch_symbol_data.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        """
        series_list = ['SM', 'ST'] if is_sme else ['EQ']

        for series in series_list:
            try:
                # Add a small delay to be polite
                time.sleep(0.1)

                data = self._fetch_symbol_data_with_retry(symbol, series)

                if data:
                    # Check if valid data
                    if 'equityResponse' in data and len(data['equityResponse']) > 0:
                        sec_info = data['equityResponse'][0].get('secInfo', {})

                        # Extract fields
                        macro = sec_info.get('macro')
                        sector = sec_info.get('sector')
                        industry_info = sec_info.get('industryInfo')
                        basic_industry = sec_info.get('basicIndustry')

                        # Check if any field is populated
                        if any([macro, sector, industry_info, basic_industry]):
                            return [
                                macro or "-",
                                sector or "-",
                                industry_info or "-",
                                basic_industry or "-"
                            ]
            except Exception as e:
                # Log error but continue to next series/symbol
                # print(f"Error fetching info for {symbol} ({series}): {e}")
                pass

        return None
