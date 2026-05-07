import pyotp

#prakharnbbb b
secret = "PBV4X4QEADYZ6WSK3ADQ5JN5AJVOIA36"
#sonam
secret = "E7MRCB3DEEMRYATLZHV6BQSI37VL5CYT"


totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"Your login code is: {current_otp}")