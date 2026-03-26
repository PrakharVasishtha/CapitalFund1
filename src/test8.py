
import difflib
type_ipo ="mb"
print(type_ipo)
if type_ipo == "mb":
    category = "individual hni more than rs 2 lakh"
elif type_ipo == "sme":
    category = "retail investor"
print(category)
starts1 = "Powerica"
starts2 = "Highness Microelectronics"
sim = difflib.SequenceMatcher(None, starts1, starts2).ratio()
print(sim)