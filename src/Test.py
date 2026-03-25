import pyotp

# Replace 'YOUR_SECRET_KEY_HERE' with your actual base32 secret
# Tip: If your secret has spaces, use .replace(" ", "")
secret = "N6337C7PWQT2B3FHYPIPIRXEPRRGDOY2"

totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"Your login code is: {current_otp}")