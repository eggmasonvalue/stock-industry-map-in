import csv
import io
import time
from typing import Dict, List, Optional
from exchange_access import NSEClient as ExchangeNSEClient
from exchange_access import RetryProfile, build_retry
import os

class NSEClient:
    def __init__(self, download_folder="./temp_downloads", frequency="weekly"):
        os.makedirs(download_folder, exist_ok=True)
        server_mode = os.environ.get('GITHUB_ACTIONS') == 'true'
        if server_mode:
            print("Running in server mode (GitHub Actions detected). Using httpx/http2.")

        retry_profile = "bulk" if frequency in ("weekly", "monthly") else "default"
        self._exchange = ExchangeNSEClient(download_folder=download_folder, server=server_mode, retry_profile=retry_profile)
        self.base_url = "https://www.nseindia.com/api"

    def set_retry_config(self, max_attempts: int, max_wait: int):
        pass

    def _fetch_url(self, url, params=None):
        """Fetches a URL with retries."""
        return self._exchange.request(url, params=params)

    def _fetch_detailed_scrip_data_with_retry(self, symbol: str, series: str, market_type: str = "N"):
        """Fetches detailed scrip data with retries and optional market type."""
        return self._exchange.get_detailed_scrip_data(
            symbol, series, market_type=market_type
        )

    def get_mainboard_symbols(self) -> List[Dict[str, str]]:
        """Fetches Mainboard symbols and series from CSV."""
        url = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
        print(f"Fetching Mainboard CSV from {url}...")
        try:
            response = self._fetch_url(url)
            if response.status_code == 200:
                csv_content = response.content.decode('utf-8')
                # Sometimes headers have leading/trailing spaces, strip them
                lines = csv_content.splitlines()
                if lines:
                    headers = [h.strip() for h in lines[0].split(',')]
                    # Reconstruct with clean headers
                    cleaned_content = ','.join(headers) + '\n' + '\n'.join(lines[1:])
                    reader = csv.DictReader(io.StringIO(cleaned_content))

                    symbols = []
                    for row in reader:
                        symbol = row.get('SYMBOL')
                        series = row.get('SERIES')
                        if symbol and series:
                            symbols.append({'symbol': symbol.strip(), 'series': series.strip()})
                    return symbols
            else:
                print(f"Failed to fetch Mainboard CSV: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching Mainboard CSV: {e}")
            return []

    def get_sme_symbols(self) -> List[Dict[str, str]]:
        """Fetches SME symbols and series from CSV."""
        url = "https://nsearchives.nseindia.com/emerge/corporates/content/SME_EQUITY_L.csv"
        print(f"Fetching SME CSV from {url}...")
        try:
            response = self._fetch_url(url)
            if response.status_code == 200:
                csv_content = response.content.decode('utf-8')
                lines = csv_content.splitlines()
                if lines:
                    headers = [h.strip() for h in lines[0].split(',')]
                    cleaned_content = ','.join(headers) + '\n' + '\n'.join(lines[1:])
                    reader = csv.DictReader(io.StringIO(cleaned_content))

                    symbols = []
                    for row in reader:
                        symbol = row.get('SYMBOL')
                        series = row.get('SERIES')
                        if symbol and series:
                            symbols.append({'symbol': symbol.strip(), 'series': series.strip()})
                    return symbols
            else:
                print(f"Failed to fetch SME CSV: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching SME CSV: {e}")
            return []

    def get_industry_info(self, symbol: str, series: str) -> Optional[List[str]]:
        """
        Fetches industry info for a symbol using getDetailedScripData.
        Requires the correct series (e.g., 'EQ', 'BE', 'SM', 'ST').
        Tries marketType="N" first, then "G" if data is missing.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        """
        if symbol.endswith('-RE'):
            return None

        def extract_info(data):
            # Check if valid data
            if 'equityResponse' in data and len(data['equityResponse']) > 0:
                sec_info = data['equityResponse'][0].get('secInfo')

                # Check if secInfo is None (which happens for marketType mismatch)
                if not sec_info:
                    return None

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
            # Try Normal Market first (N)
            data = self._fetch_detailed_scrip_data_with_retry(symbol, series, market_type="N")
            info = extract_info(data)

            if info:
                return info

            # If failed (None), try Periodic Call Auction Market (G)
            # print(f"Retrying {symbol} ({series}) with marketType='G'...")
            data_g = self._fetch_detailed_scrip_data_with_retry(symbol, series, market_type="G")
            return extract_info(data_g)

        except Exception:
            # Log error but continue
            # print(f"Error fetching info for {symbol}: {e}")
            pass

        return None
