import pyotp

# Replace 'YOUR_SECRET_KEY_HERE' with your actual base32 secret
# Tip: If your secret has spaces, use .replace(" ", "")
secret = "DOIIMB2PTIIOCKDQ4ILOCPVF44YJ7QBU"

totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"Your login code is: {current_otp}")