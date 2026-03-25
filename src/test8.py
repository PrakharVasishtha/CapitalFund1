
import difflib



starts1 = "Powerica"
starts2 = "Highness Microelectronics"
sim = difflib.SequenceMatcher(None, starts1, starts2).ratio()
print(sim)