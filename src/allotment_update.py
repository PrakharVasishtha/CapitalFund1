from allotment_fetch import fetch_allotment_holdings
import openpyxl
import time
from Base import get_vix
from ipo_ExtractGMP import get_ipo_gmp
from ipo_ExtractReview import has_dicey_word
from ipo_ExtractSubscription import get_ipo_subscription_live
from datetime import date
from common_foundation import *


def excel_holdings(usr_id: int,security_symbol: str, issue_price: int, total_shares: int, lot_size: int):
        print("excel_holdings", row, type1)
        path = '../allotted_holdings.xlsx'
        wb = openpyxl.load_workbook(path)
        ws = wb[usr_id]
        for k in range(1,20):
            spl_session_status = int(ws.cell(k, 7).value)
            if spl_session_status == 5:
                url2 = ws.cell(row, 1).value
                name1 = ws.cell(row, 2).value
                print(name1)
                if name1 != None:
                    #
                    url1 = ws.cell(row, 3).value

                    gmp = get_ipo_gmp(name1)
                    print(gmp)
                    sub = get_ipo_subscription_live(url2)
                    print(sub)
                    review = int(has_dicey_word(url2))
                    AI = get_vix()
                    ws.cell(row, 28, gmp)
                    ws.cell(row, 23, review)
                    ws.cell(row, 24, sub[0])
                    ws.cell(row, 25, sub[1])
                    ws.cell(row, 26, sub[2])
                    ws.cell(row, 35, AI)
                else:
                    print("name is empty in sheet at:",row)
                try:
                    wb.save(path)
                    print(f"excel_holdings Successfully updated details for row {row}")
                except PermissionError:
                    print(f"excel_holdings Error: Permission denied. Please ensure '{path}' is closed.")
                except Exception as e:
                    print(f"excel_holdings An error occurred while saving the file: {e}")
            else:
                #print("Closing not today")
                x=0
            k = k + 1
        wb.close()



def allotment_update():
    holdings = fetch_allotment_holdings()
    for 
    excel_holdings()
    # symbol, issue_price, total_shares, lot_size
    
    