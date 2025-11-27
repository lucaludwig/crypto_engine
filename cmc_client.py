"""CoinMarketCap API Client"""
import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class CoinMarketCapClient:
    """Client for interacting with CoinMarketCap API"""

    BASE_URL = "https://pro-api.coinmarketcap.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the CoinMarketCap client

        Args:
            api_key: CoinMarketCap API key. If not provided, reads from CMC_API_KEY env var
        """
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        if not self.api_key:
            raise ValueError("CoinMarketCap API key is required. Set CMC_API_KEY environment variable.")

        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

    def get_latest_listings(self, limit: int = 200, convert: str = "USD") -> List[Dict]:
        """Get latest cryptocurrency listings

        Args:
            limit: Number of cryptocurrencies to return (max 5000)
            convert: Currency to convert prices to

        Returns:
            List of cryptocurrency data dictionaries
        """
        url = f"{self.BASE_URL}/cryptocurrency/listings/latest"
        params = {
            'limit': limit,
            'convert': convert,
            'sort': 'market_cap'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from CoinMarketCap: {e}")
            return []

    def get_quotes(self, symbols: List[str], convert: str = "USD") -> Dict:
        """Get latest quotes for specific cryptocurrencies

        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC', 'ETH'])
            convert: Currency to convert prices to

        Returns:
            Dictionary mapping symbols to their quote data
        """
        url = f"{self.BASE_URL}/cryptocurrency/quotes/latest"
        params = {
            'symbol': ','.join(symbols),
            'convert': convert
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('data', {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching quotes: {e}")
            return {}
