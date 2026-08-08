from allotment_fetch import fetch_allotment_holdings
import openpyxl
import time
from Base import get_vix
from ipo_ExtractGMP import get_ipo_gmp
from ipo_ExtractReview import has_dicey_word
from ipo_ExtractSubscription import get_ipo_subscription_live
from datetime import date


def excel_holdings(usr_id: str):
    """
    Scans the user's sheet in allotted_holdings.xlsx for rows where
    special_session_status == 5 (per readme.md: "empty" / not yet fetched)
    and fills in GMP / subscription / review / VIX data for those rows.

    NOTE: previously this referenced undefined `row` and `type1` variables
    and would raise NameError as soon as it was called. Fixed to use the
    loop variable `k`, which is what the surrounding code clearly intended.
    """
    print("excel_holdings", usr_id)
    path = '../allotted_holdings.xlsx'
    wb = openpyxl.load_workbook(path)
    ws = wb[str(usr_id)]

    for k in range(1, 20):
        status_cell = ws.cell(k, 7).value
        if status_cell is None:
            continue

        spl_session_status = int(status_cell)
        if spl_session_status != 5:
            continue

        url2 = ws.cell(k, 1).value
        name1 = ws.cell(k, 2).value
        print(name1)

        if name1 is None:
            print("name is empty in sheet at:", k)
            continue

        try:
            gmp = get_ipo_gmp(name1)
        except Exception as e:
            print(f"excel_holdings: GMP fetch failed at row {k}: {e}")
            gmp = 0

        try:
            sub = get_ipo_subscription_live(url2)
            if sub is None:
                sub = [0, 0, 0, 0]
        except Exception as e:
            print(f"excel_holdings: subscription fetch failed at row {k}: {e}")
            sub = [0, 0, 0, 0]

        try:
            review = int(has_dicey_word(url2))
        except Exception as e:
            print(f"excel_holdings: review fetch failed at row {k}: {e}")
            review = 1

        AI = get_vix()

        ws.cell(k, 28, gmp)
        ws.cell(k, 23, review)
        ws.cell(k, 24, sub[0])
        ws.cell(k, 25, sub[1])
        ws.cell(k, 26, sub[2])
        ws.cell(k, 35, AI)

        try:
            wb.save(path)
            print(f"excel_holdings: Successfully updated details for row {k}")
        except PermissionError:
            print(f"excel_holdings Error: Permission denied. Please ensure '{path}' is closed.")
        except Exception as e:
            print(f"excel_holdings An error occurred while saving the file: {e}")

    wb.close()


def allotment_update():
    holdings = fetch_allotment_holdings()