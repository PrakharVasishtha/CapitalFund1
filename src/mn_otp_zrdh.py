import pyotp

#prakhar
secret = "PBV4X4QEADYZ6WSK3ADQ5JN5AJVOIA36"
totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"prakhar login code is: {current_otp}")
#sonam
secret = "E7MRCB3DEEMRYATLZHV6BQSI37VL5CYT"
totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"sonam login code is: {current_otp}")

