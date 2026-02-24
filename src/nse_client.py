import csv
import io
import time
from typing import Dict, List, Optional
import requests
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_exception
from nse import NSE
import os
import httpx

class NSEClient:
    def __init__(self, download_folder="./temp_downloads"):
        os.makedirs(download_folder, exist_ok=True)
        # Auto-detect server mode (GitHub Actions)
        server_mode = os.environ.get('GITHUB_ACTIONS') == 'true'
        if server_mode:
            print("Running in server mode (GitHub Actions detected). Using httpx/http2.")

        self.nse = NSE(download_folder=download_folder, server=server_mode)
        self.base_url = "https://www.nseindia.com/api"
        # Default retry settings (weekly)
        self.max_attempts = 15
        self.max_wait = 90

    def set_retry_config(self, max_attempts: int, max_wait: int):
        self.max_attempts = max_attempts
        self.max_wait = max_wait

    def _is_retryable_exception(self, exception):
        """
        Checks if an exception is retryable based on strict criteria.

        Retry ONLY if:
        1. Exception is TimeoutError.
        2. Exception is ConnectionError AND status code is 429, 503, 408, 502, or 504.
        """
        if isinstance(exception, TimeoutError):
            return True

        if isinstance(exception, ConnectionError):
            msg = str(exception)
            # Retry on specific status codes
            if any(code in msg for code in ["429", "503", "408", "502", "504"]):
                return True
            # Explicitly fail on others (400, 401, 403, 404, 500, etc.)
            return False

        return False

    def _fetch_url(self, url, params=None):
        """Fetches a URL with retries."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception(self._is_retryable_exception),
            reraise=True
        )
        try:
            return retryer(self.nse._req, url, params=params)
        except Exception as e:
            raise e

    def _fetch_symbol_data_fallback(self, symbol, series_list):
        """
        Fetches symbol data with retries, trying a list of series in order.
        If a series returns 404, moves to the next one.
        If a retryable error occurs (after retries), it raises the exception.
        """
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception(self._is_retryable_exception),
            reraise=True
        )

        for series in series_list:
            try:
                # getDetailedScripData might raise exceptions which are retryable
                return retryer(self.nse.getDetailedScripData, symbol, series)
            except ConnectionError as e:
                # If 404, try next series
                if "404" in str(e):
                    continue
                # If other ConnectionError (and retries exhausted), raise it
                raise e
            except Exception as e:
                # Raise other exceptions
                raise e

        # If we exhausted all series and they all were 404
        raise ConnectionError(f"404 Client Error: Not Found for all series: {series_list} for symbol {symbol}")

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
        Fetches industry info for a symbol using getDetailedScripData.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        """
        if symbol.endswith('-RE'):
            return None

        def extract_info(data):
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
            return None

        # Add a small delay to be polite
        time.sleep(0.1)

        try:
            if is_sme:
                # Try SME series
                data = self._fetch_symbol_data_fallback(symbol, ['SM', 'ST', 'SZ'])
                return extract_info(data)
            else:
                # Try Mainboard series
                data = self._fetch_symbol_data_fallback(symbol, ['EQ', 'BE', 'BZ'])
                return extract_info(data)
        except Exception:
            # Log error but continue
            # print(f"Error fetching info for {symbol}: {e}")
            pass

        return None
