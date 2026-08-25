import time
import openpyxl
from tqdm import tqdm
import Base
from common_foundation import send_email_with_excel
from ipo_excel_3pm import update_row_3pm
from ipo_ExtractReview import has_dicey_word
from ipo_scraper import get_latest_ipos
from ipo_excel_manager import ExcelManager
from ipo_cleanfetcheddata import clean_ipo_data
from IpoDataExtractor import ChittorgarhIPOExtractor, IPOData
from ipo_ExtractGMP import get_ipo_gmp
from ipo_ExtractSubscription import get_ipo_subscription_dict



def latest_ipo_entry():
    print("-----------latest_ipo_entry---------")
    print("##############################################")
    sc = get_latest_ipos()[::-1]
    #print("latest_ipos",sc)
    row_sme=Base.get_last_row_sme()
    row_mb=Base.get_last_row_mb()
    #for ipo in sc:
    for ipo in tqdm(sc, desc="Processing IPO Entries", unit="ipo"):
        time.sleep(2)
        ex = ExcelManager()
        type1 = ipo['category']
        name1 = ipo['name']
        url3 = ipo['url']
        industry_score = ipo['industry_score']
        #print("type1",type1,"name1",name1,"url3",url3)
        if type1 == "SME":
            row = row_sme
        else:
            row = row_mb
        if not ex.exists(type1, name1) and Base.is_data_available(url3):
            try:
                ex.append(ipo,row)
                url2 = ipo['url']
                #print(name1)
                extractor = ChittorgarhIPOExtractor()
                data1 = extractor.extract(url2)
                data2 = clean_ipo_data(data1)
                ex.write_details(row, data2, type1)

                try:
                    time.sleep(.5)
                    gmp=get_ipo_gmp(name1)
                except Exception as e:
                    print(e)
                    gmp=0
                try:
                    time.sleep(.5)
                    sub=get_ipo_subscription_dict(url2)
                except Exception as e:
                    print(e)
                    sub = ["2","2","1","1.5"]
                time.sleep(.5)
                review=has_dicey_word(url2)
                time.sleep(.5)
                ex.write_details_GSR(row, gmp, sub, review, type1,industry_score)
                #print("---------write_formula----------")
                if type1 == "SME":
                    row_sme = row_sme + 1
                else:
                    row_mb= row_mb + 1
            except Exception as item_err:
                print(f"Error processing IPO {name1}: {item_err}")
    try:
        send_email_with_excel(mail_subject="latest_ipo_entry",mail_content="latest_ipo_entry",path_of_file='General.xlsx')
    except Exception as e:
        print("Cant send General.xls")

def dynamic_data_update():
    print(
        "-----------dynamic_data_update----------")
    print(
        "####################################")
    path = Base.get_excel_path()
    wb = Base.safe_load_workbook(path)
    sme_ws = wb['IPOSME']
    main_ws = wb['IPOMB']
    #print(sme_ws)
    row_sme = Base.get_last_row_sme()
    row_mb = Base.get_last_row_mb()
    wb.close()
    start_sme = max(2, row_sme - 25)
    for k in range(start_sme, row_sme + 1):
        try:
            update_row_3pm(k, "SME")
        except Exception as e:
            print(f"Error updating row {k} SME: {e}")

    start_mb = max(2, row_mb - 25)
    for k in range(start_mb, row_mb + 1):
        try:
            update_row_3pm(k, "MB")
        except Exception as e:
            print(f"Error updating row {k} MB: {e}")
    try:
        send_email_with_excel(mail_subject="IPO Data Updated",mail_content="IPO Data Updated",path_of_file='General.xlsx')
    except Exception as e:
        print("Cant send General.xls")

if __name__ == "__main__":
    latest_ipo_entry()
    dynamic_data_update()