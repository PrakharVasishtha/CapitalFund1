import sys
import os

sys.path.insert(0, os.path.abspath('src'))
from ipo_ExtractSubscription import get_ipo_subscription_live, get_ipo_subscription_dict

print("Testing CapitalFund1 Subscription Extractor...")

test_urls = [
    "https://www.chittorgarh.com/ipo/behari-lal-engineering-ipo/2659/",
    "https://www.chittorgarh.com/ipo/shiprocket-ipo/2450/",
    "https://www.chittorgarh.com/ipo/molbio-diagnostics-ipo/2800/"
]

for url in test_urls:
    print(f"\n--- Testing URL: {url} ---")
    sub_dict = get_ipo_subscription_dict(url)
    print("get_ipo_subscription_dict:", sub_dict)
    sub_live = get_ipo_subscription_live(url)
    print("get_ipo_subscription_live:", sub_live)
