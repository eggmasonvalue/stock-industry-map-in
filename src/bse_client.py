import time
from typing import Dict, List, Optional
from exchange_access import BSEClient as ExchangeBSEClient
from exchange_access import RetryProfile, build_retry
import os

class BSEClient:
    def __init__(self, download_folder="./temp_downloads", frequency="weekly"):
        os.makedirs(download_folder, exist_ok=True)
        retry_profile = "bulk" if frequency in ("weekly", "monthly") else "default"
        self._exchange = ExchangeBSEClient(download_folder=download_folder, retry_profile=retry_profile)

    def set_retry_config(self, max_attempts: int, max_wait: int):
        pass

    def _fetch_securities(self, group='A'):
        """Fetches securities with retry."""
        return self._exchange.list_securities(group=group)

    def _fetch_meta_info(self, scrip_code):
        """Fetches meta info with retry."""
        return self._exchange.equity_meta_info(scrip_code)

    def get_securities(self) -> List[Dict[str, str]]:
        """
        Fetches list of BSE securities.
        Returns a list of dicts containing 'scrip_code' and 'symbol'.
        """
        print("Fetching BSE securities list...")
        result = []

        groups = self._exchange.valid_groups()
        if not groups:
            groups = ('A',)

        for group in groups:
            # print(f"Fetching group {group}...")
            try:
                securities = self._fetch_securities(group=group)
                for sec in securities:
                    if 'SCRIP_CD' in sec and 'scrip_id' in sec:
                        result.append({
                            'scrip_code': sec['SCRIP_CD'],
                            'symbol': sec['scrip_id'],
                            'group': group
                        })
            except Exception as e:
                print(f"Error fetching BSE securities for group {group}: {e}")
                # Continue to next group

        return result

    def get_industry_info(self, scrip_code: str, symbol: Optional[str] = None) -> Optional[List[str]]:
        """
        Fetches industry info for a BSE scrip code.
        Returns [Macro, Sector, Industry, Basic Industry] or None if not found.
        Maps BSE fields:
        Sector -> Macro
        IndustryNew -> Sector
        IGroup -> Industry
        ISubGroup -> Basic Industry
        """
        if symbol and symbol.endswith('-RE'):
            return None

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
        except Exception:
            # print(f"Error fetching info for scrip {scrip_code}: {e}")
            return None
