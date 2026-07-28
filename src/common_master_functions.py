import openpyxl
from tqdm import tqdm
import Base
from common_foundation import *
from ipo_excel_3pm import update_row_3pm
from ipo_ExtractReview import has_dicey_word
from ipo_scraper import get_latest_ipos
from ipo_excel_manager import ExcelManager
from ipo_cleanfetcheddata import clean_ipo_data
from IpoDataExtractor import ChittorgarhIPOExtractor, IPOData
from ipo_ExtractGMP import get_ipo_gmp
from ipo_ExtractSubscription import get_ipo_subscription_dict



def latest_ipo_entry():
    print("*************************************-----------latest_ipo_entry----------************************************")
    print("##############################################################################################################")
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
        data_available = Base.is_data_available(url3)
        #print("data_available",data_available)
        if type1 == "SME":
            row = row_sme
        else:
            row = row_mb
        if not ex.exists(type1, name1) and data_available:
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
    try:
        send_email_with_excel()
    except Exception as e:
        print("Cant send General.xls")

def update_3pm():
    print(
        "*************************************-----------update_3pm----------************************************")
    print(
        "##############################################################################################################")
    path = '../General.xlsx'
    wb = openpyxl.load_workbook(path)
    sme_ws = wb['IPOSME']
    main_ws = wb['IPOMB']
    #print(sme_ws)
    row_sme = Base.get_last_row_sme()
    row_mb = Base.get_last_row_mb()
    wb.close()
    #print(row_sme, row_mb)
    for k in range(row_sme-11,row_sme+1):
        #print(k)
        try:
            update_row_3pm(k,"SME")
        except Exception as e:
            print(e)
    for k in range(row_mb-4, row_mb+1):
        #print(k)
        try:
            update_row_3pm(k,"MB")
        except Exception as e:
            print(e)
    try:
        send_email_with_excel()
    except Exception as e:
        print("Cant send General.xls")


#latest_ipo_entry()
#update_3pm()