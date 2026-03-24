# Updated File: dhan_api.py
# (Simplified — we no longer need instrument master lookup because holdings already provide securityId and exchangeSegment)
from dhanhq import DhanContext, dhanhq
import requests
import json

BASE_URL = "https://api.dhan.co/"

def load_credentials(file_path: str) -> list:
    """Load user credentials from JSON file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("users", [])
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Create it with the correct structure.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {file_path}.")
        return []

def get_withdrawable_balance(client_id,access_token):
    dhan_context = DhanContext(client_id, access_token)
    dhan = dhanhq(dhan_context)
    # Fetch all fund and margin limits
    funds = dhan.get_fund_limits()
    withdrawable = 0
    if funds.get('status') == 'success':
        data = funds.get('data', {})
        withdrawable = data.get('withdrawableBalance', 0.0)
        print(f"Withdrawable Balance: {withdrawable}")
        return withdrawable
    else:
        print("Error fetching funds:", funds.get('remarks'))
        return withdrawable


def withdraw(fund_to_withdraw, client_id, access_token):
    print("Withdrawing...")



#print(get_withdrawable_balance(client_id,access_token))