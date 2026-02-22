import time
from typing import Dict, List, Optional
import requests
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type
from bse import BSE
import os

class BSEClient:
    def __init__(self, download_folder="./temp_downloads"):
        os.makedirs(download_folder, exist_ok=True)
        self.bse = BSE(download_folder=download_folder)
        # Default retry settings (weekly)
        self.max_attempts = 15
        self.max_wait = 90

    def set_retry_config(self, max_attempts: int, max_wait: int):
        self.max_attempts = max_attempts
        self.max_wait = max_wait

    def _fetch_securities(self):
        """Fetches securities with retry."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
            reraise=True
        )
        try:
            return retryer(self.bse.listSecurities)
        except Exception as e:
            raise e

    def _fetch_meta_info(self, scrip_code):
        """Fetches meta info with retry."""
        retryer = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(multiplier=1, min=2, max=self.max_wait),
            retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
            reraise=True
        )
        try:
            return retryer(self.bse.equityMetaInfo, scrip_code)
        except Exception as e:
            raise e

    def get_securities(self) -> List[Dict[str, str]]:
        """
        Fetches list of BSE securities.
        Returns a list of dicts containing 'scrip_code' and 'symbol'.
        """
        print("Fetching BSE securities list...")
        try:
            securities = self._fetch_securities()
            result = []
            for sec in securities:
                if 'SCRIP_CD' in sec and 'scrip_id' in sec:
                    result.append({
                        'scrip_code': sec['SCRIP_CD'],
                        'symbol': sec['scrip_id']
                    })
            return result
        except Exception as e:
            print(f"Error fetching BSE securities: {e}")
            return []

    def get_industry_info(self, scrip_code: str) -> Optional[List[str]]:
        """
        Fetches industry info for a BSE scrip code.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        Maps BSE fields:
        Sector -> Macro
        IndustryNew -> Sector
        IGroup -> Industry
        ISubGroup -> Basic Industry
        """
        try:
            # Add a small delay
            time.sleep(0.1)

            meta_info = self._fetch_meta_info(scrip_code)

            if meta_info:
                sector = meta_info.get('Sector')
                industry_new = meta_info.get('IndustryNew')
                igroup = meta_info.get('IGroup')
                isubgroup = meta_info.get('ISubGroup')

                # Check if any field is populated
                if any([sector, industry_new, igroup, isubgroup]):
                    return [
                        sector or "-",
                        industry_new or "-",
                        igroup or "-",
                        isubgroup or "-"
                    ]
            return None
        except Exception as e:
            # print(f"Error fetching info for scrip {scrip_code}: {e}")
            return None
