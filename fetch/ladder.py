import os
import time
import re
import requests
from dotenv import load_dotenv

load_dotenv()

REGION_MAP = {
    "BR1": "americas", "LA1": "americas", "LA2": "americas", "NA1": "americas",
    "OC1": "sea", "PH2": "sea", "SG2": "sea", "TH2": "sea", "TW2": "sea", "VN2": "sea",
    "JP1": "asia", "KR": "asia", 
    "EUN1": "europe", "EUW1": "europe", "RU": "europe", "TR1": "europe",
}

DEFAULT_PLATFORM = "EUW1"
DEFAULT_REGION = REGION_MAP[DEFAULT_PLATFORM]
DEFAULT_QUEUE = 420  

def get_api_key_from_env():
    """
    Retrieve and validate the Riot API key from environment variables.
    """
    api_key = os.getenv("RIOT_API_KEY")

    if not api_key or not api_key.startswith("RGAPI-"):
        raise Exception("Valid RIOT_API_KEY not found in .env")

    return api_key.strip()

RIOT_API_KEY = get_api_key_from_env()
riot_session = requests.Session()
riot_session.headers.update({"X-Riot-Token": RIOT_API_KEY})


class SimpleTokenBucket:
    """
    A simple token bucket rate limiter that allows maximum requests within a timeframe.
    """
    def __init__(self, max_requests, refill_seconds):
        self.max_requests = max_requests
        self.tokens = max_requests
        self.refill_seconds = refill_seconds
        self.last_checked = time.time()

    def try_get_token(self, num=1):
        """
        It will attempt to consume a token and refill tokens over time.
        """
        now = time.time()
        elapsed = now - self.last_checked
        refill_amount = elapsed * (self.max_requests / self.refill_seconds)
        self.tokens = min(self.max_requests, self.tokens + refill_amount)
        self.last_checked = now
        if self.tokens >= num:
            self.tokens -= num
            return True
        return False


ten_sec_bucket = SimpleTokenBucket(18, 10.0)
two_min_bucket = SimpleTokenBucket(90, 120.0)


def wait_for_rate_limit():
    """
    It waits until there is room in both rate limit buckets.
    """
    while not (ten_sec_bucket.try_get_token() and two_min_bucket.try_get_token()):
        time.sleep(0.1)


def riot_get_with_rate_limit(url, params=None):
    """
    It makes a GET request to the Riot API while minding rate limits and automatically retries after 429 (rate limit exceeded).
    """
    wait_for_rate_limit()
    response = riot_session.get(url, params=params, timeout=20)

    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "2"))
        time.sleep(retry_after)
        return riot_get_with_rate_limit(url, params)

    if response.status_code >= 400:
        print(response.text)
        response.raise_for_status()

    return response.json()

def get_summoner_info_by_name(summoner_name, platform=DEFAULT_PLATFORM):
    """
    Retrieve a player summoner information with their in-game name.
    """
    safe_name = requests.utils.quote(summoner_name)
    url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{safe_name}"
    return riot_get_with_rate_limit(url)


def get_matchlist_by_puuid(puuid, start=0, count=100, region=DEFAULT_REGION, queue=DEFAULT_QUEUE):
    """
    Fetch a list of match IDs for a given player PUUID.
    """
    url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
    params = {"start": start, "count": count, "queue": queue}
    return riot_get_with_rate_limit(url, params=params)
