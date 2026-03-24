from kiteconnect import KiteConnect

# Replace with your credentials
api_key = "your_api_key"
access_token = "your_access_token"

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

try:
    margins = kite.margins()

    # Available cash balance
    available_cash = margins["equity"]["available"]["cash"]

    # Utilised margin
    utilised = margins["equity"]["utilised"]["debits"]

    # Opening balance
    opening_balance = margins["equity"]["available"]["opening_balance"]

    print("Available Cash:", available_cash)
    print("Utilised Margin:", utilised)
    print("Opening Balance:", opening_balance)

    # Approx withdrawable balance (basic calculation)
    withdrawable = available_cash - utilised
    print("Approx Withdrawable Balance:", withdrawable)

except Exception as e:
    print("Error:", e)