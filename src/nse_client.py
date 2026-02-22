import csv
import io
import time
from typing import Dict, List, Optional
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from nse import NSE
import os

class NSEClient:
    def __init__(self, download_folder="./temp_downloads"):
        os.makedirs(download_folder, exist_ok=True)
        self.nse = NSE(download_folder=download_folder)
        self.base_url = "https://www.nseindia.com/api"

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError))
    )
    def _fetch_url(self, url, params=None):
        """Fetches a URL with retries."""
        try:
            return self.nse._req(url, params=params)
        except Exception as e:
            # Re-raise to trigger tenacity retry
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
        Fetches industry info for a symbol.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        """
        url = f"{self.base_url}/NextApi/apiClient/GetQuoteApi"

        series_list = ['SM', 'ST'] if is_sme else ['EQ']

        for series in series_list:
            params = {
                "functionName": "getSymbolData",
                "marketType": "N",
                "series": series,
                "symbol": symbol
            }
            try:
                # Add a small delay to be polite
                time.sleep(0.1)

                response = self._fetch_url(url, params=params)

                if response.status_code == 200:
                    data = response.json()

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
