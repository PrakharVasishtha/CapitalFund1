import openpyxl
import difflib
from typing import Dict, Any

class Formula:
    def __init__(self):
        wa=1

    # SME Formulas
    def snr_sme(self, sqib, sni):

        # AA = if(Q2<50,if(R2>(2.3*Q2),0,1),1)
        try:
            if sqib < 50:
                if sni > (2.3 * sqib):
                    AA = 0
                else:
                    AA = 1
            else:
                AA = 1
        except:
            AA = 0
        return AA

    def gmp_effect_sme(self, gmp):
        try:
            AC = 1 if gmp > 6 else 0
        except:
            AC = 0
        return AC

    def pre_sub_aggregate_sme(self, G, P, peaftr, anchor, tiyoy):
        try:
            AG1 = (.7 if G > 51 else 0) + (.7 if G > 33 else 0) + (.7 if G > 0 else 0) + 0
            AG2 = (1 if P < 14.56 else 0) + (1 if peaftr < 34 else 0) + (1 if anchor > 0 else 0) + (1 if tiyoy > 10.56 else 0) + 0
            AG = AG1 + AG2
        except:
            AG = 0
        return AG

    def post_sub_aggregate_sme(self, AG, sqib, sni, AA, AC):
        try:
            AH = AG + (1 if sqib > 1.34 else 0) + (1 if sni > 1.34 else 0) + AA + AC
        except:
            AH = 0
        return AH

    def total_sme(self, AG, AH):
        AI = AG + (1.4 * AH)
        return AI

    # MB Formula

    def snr_mb(self, sqib, sni):
        # AA = =if(AND(O63<33,P63>O63),if(P63>(1.1*O63),0,1),1)
        if sqib < 33:
            if sni > (1.1 * sqib):
                AA = 0
            else:
                AA = 1
        else:
            AA = 1
        return AA

    def gmp_effect_mb(self, gmp):
        if gmp != 0:
            AC = (1 if gmp > 9 else 0) + (gmp / 3)
        else:
            AC = 0
        return AC

    def pre_sub_aggregate_mb(self, G, P, peaftr, pryoy, tiyoy, nwyoy):
        AG1 = (1.2 if G >= 0 else 0) + (.9 if G > 13 else 0) + 0
        AG2 = (.7 if P < 0 else 0) + (1 if P < 6.5 else 0) + (1 if P < 23 else 0) + 0
        AG3 = (1 if peaftr < 89 else 0) + (1 if pryoy > 19 else 0) + (1 if tiyoy > 13 else 0) + (1 if nwyoy > 25 else 0) + 0
        AG = AG1 + AG2 + AG3
        return AG

    def post_sub_aggregate_mb(self, AG, sqib, sni, sri, AA, AC):
        AH = AG + (1 if AG > 6 else 0) + (1 if sqib > 16 else 0) + (1 if sni > 10 else 0) + (
            1 if sri > 1.34 else 0) + AA + AC
        return AH

    def total_mb(self, AG, AH):
        AI = (AG * 2.5) + AH
        return AI

#formula().write_formula_mb(69, "MB")