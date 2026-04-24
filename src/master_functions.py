import openpyxl
import Base
from excel_3pm import update_row_3pm
from ExtractReview import has_dicey_word
from scraper import get_latest_ipos
from excel_manager import ExcelManager
from cleanfetcheddata import clean_ipo_data
from IpoDataExtractor import ChittorgarhIPOExtractor, IPOData
from ExtractGMP import get_ipo_gmp
from ExtractSubscription import get_ipo_subscription_dict



def latest_ipo_entry():
    print("-----------latest_ipo_entry----------")
    sc = get_latest_ipos()[::-1]
    #print("latest_ipos",sc)
    row_sme=Base.get_last_row_sme()
    row_mb=Base.get_last_row_mb()
    for ipo in sc:
        ex = ExcelManager()
        type1 = ipo['category']
        name1 = ipo['name']
        url3 = ipo['url']
        industry_score = ipo['industry_score']
        print("type1",type1,"name1",name1,"url3",url3)
        data_available = Base.is_data_available(url3)
        print("data_available",data_available)
        if type1 == "SME":
            row = row_sme
        else:
            row = row_mb
        if not ex.exists(type1, name1) and data_available:
            ex.append(ipo,row)
            url2 = ipo['url']
            print(url2)
            extractor = ChittorgarhIPOExtractor()
            data1 = extractor.extract(url2)
            data2 = clean_ipo_data(data1)
            ex.write_details(row, data2, type1)

            try:
                gmp=get_ipo_gmp(name1)
            except Exception as e:
                print(e)
                gmp=0
            try:
                sub=get_ipo_subscription_dict(url2)
            except Exception as e:
                print(e)
                sub = ["20","20","10","10"]
            review=has_dicey_word(url2)

            ex.write_details_GSR(row, gmp, sub, review, type1,industry_score)
            print("---------write_formula----------")
            if type1 == "SME":
                row_sme = row_sme + 1
            else:
                row_mb= row_mb + 1

def update_3pm():
    print("-----------update_3pm----------")
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


def master_saler():
    print("-----------saler start----------")
    path = '../share_data.xlsx'
    wb = openpyxl.load_workbook(path)
    sme_ws = wb['IPOSME']
    print("------------saler end-------------")

latest_ipo_entry()
#update_3pm()
#master_saler()