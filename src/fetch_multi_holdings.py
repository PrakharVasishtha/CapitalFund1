# Multi-User Holdings Fetcher for Dhan Broker
# Uses dhanhq official SDK: pip install dhanhq
# Optional: pandas for tabular output (pip install pandas openpyxl)

from trading_base import *
import pprint
import pandas as pd
from dhanhq import DhanContext, dhanhq

# Path to your secure JSON file (add to .gitignore!)
CREDENTIALS_FILE = "credentials.json"



# SECURITY NOTES:
# - NEVER commit this file to GitHub (add "credentials.json" to .gitignore)
# - Access tokens expire in 24 hours → renew daily and update the file
# - For automation, implement token renewal (see previous /RenewToken code) and auto-update JSON




def fetch_holdings_for_user(name: str, client_id: str, access_token: str) -> pd.DataFrame:
    """Fetch holdings for a single user and return as DataFrame."""
    print(f"\nFetching holdings for: {name} ({client_id})")

    dhan_context = DhanContext(client_id, access_token)
    dhan = dhanhq(dhan_context)

    response = dhan.get_holdings()

    # Handle response (direct list in latest v2)
    if isinstance(response, dict):
        holdings = response.get("data", response.get("holdings", []))
    else:
        holdings = response or []

    if not holdings:
        print(f"No holdings found for {name}.")
        return pd.DataFrame()  # Empty DF

    print(f"Found {len(holdings)} holdings for {name}")

    # Convert to DataFrame
    df = pd.DataFrame(holdings)

    # Add user column for combined view
    if not df.empty:
        df.insert(0, "User", name)

    # Optional: Select/reorder useful columns
    useful_cols = ['User', 'tradingSymbol', 'isin', 'totalQty', 'dpQty', 't1Qty',
                   'availableQty', 'collateralQty', 'avgCostPrice']
    df = df[[col for col in useful_cols if col in df.columns]]

    # Pretty print
    print(df.to_string(index=False))

    return df


def main():
    users = load_credentials(CREDENTIALS_FILE)

    if not users:
        print("No users loaded. Exiting.")
        return

    all_holdings_dfs = []

    for user in users:
        name = user.get("name", "Unknown")
        client_id = user.get("client_id")
        access_token = user.get("access_token")

        if not client_id or not access_token:
            print(f"Skipping {name}: Missing client_id or access_token")
            continue

        df = fetch_holdings_for_user(name, client_id, access_token)
        if not df.empty:
            all_holdings_dfs.append(df)

    # Combined view: All users' holdings in one DataFrame
    if all_holdings_dfs:
        combined_df = pd.concat(all_holdings_dfs, ignore_index=True)
        print("\n" + "=" * 80)
        print("COMBINED HOLDINGS ACROSS ALL USERS")
        print("=" * 80)
        print(combined_df.to_string(index=False))

        # Save to files
        combined_df.to_excel("all_users_holdings.xlsx", index=False)
        combined_df.to_csv("all_users_holdings.csv", index=False)
        print("\nSaved combined holdings to 'all_users_holdings.xlsx' and '.csv'")

        # Optional: Save individual user files
        for user_df in all_holdings_dfs:
            user_name = user_df["User"].iloc[0] if not user_df.empty else "unknown"
            filename = f"holdings_{user_name}.xlsx"
            user_df.to_excel(filename, index=False)
            print(f"Saved {user_name} holdings to '{filename}'")


if __name__ == "__main__":
    main()