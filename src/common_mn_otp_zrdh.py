import pyotp

#prakhar
secret = "PBV4X4QEADYZ6WSK3ADQ5JN5AJVOIA36"
totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"prakhar login code is: {current_otp}")
#sonam
secret = "GCZYYRS5QTL53P4KM76O3HD7Z7RCTISZ"
totp = pyotp.TOTP(secret)
current_otp = totp.now()

print(f"sonam login code is: {current_otp}")

