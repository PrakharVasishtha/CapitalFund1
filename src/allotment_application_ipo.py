from datetime import date
import openpyxl

from Base import get_last_row_sme, get_last_row_mb, get_excel_path
from allotment_kotak_ipo_apply import apply_to_ipo, apply_to_ipo_all_users
from logger_setup import get_logger

logger = get_logger(__name__)


def IPO_to_apply():
    logger.info("--------IPO_to_apply: Scanning closing IPOs-------")
    IPO_sme_1 = []
    IPO_sme_2 = []
    IPO_sme_3 = []
    IPO_mb_1 = []
    IPO_mb_2 = []
    IPO_mb_3 = []

    row_sme = get_last_row_sme() - 1
    row_mb = get_last_row_mb() - 1


    path = get_excel_path()
    wb = openpyxl.load_workbook(path, data_only=True)
    sme_ws = wb['IPOSME']
    main_ws = wb['IPOMB']

    for i in range(0, 9):
        rw = row_sme - i
        apply = sme_ws.cell(rw, 42).value
        name = sme_ws.cell(rw, 2).value
        name = name[:15]
        if apply == 1:
            close_date = sme_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_sme_1.append(name)

        if apply == 2:
            close_date = sme_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_sme_2.append(name)
        
        if apply == 3:
            close_date = sme_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_sme_3.append(name)

    for i in range(0, 9):
        rw = row_mb - i
        apply = main_ws.cell(rw, 42).value
        name = main_ws.cell(rw, 2).value
        name = name[:15]
        if apply == 1:
            close_date = main_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_mb_1.append(name)

        if apply == 2:
            close_date = main_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_mb_2.append(name)
        
        if apply == 3:
            close_date = main_ws.cell(rw, 40).value
            today = date.today().day
            if today == close_date:
                IPO_mb_3.append(name)
    return IPO_mb_3, IPO_sme_3, IPO_mb_2, IPO_sme_2, IPO_mb_1, IPO_sme_1


def ipo_application():
    logger.info("-----------ipo_application: Executing scheduled IPO applications----------")
    all_ipos = IPO_to_apply()
    IPO_mb_3 = all_ipos[0]
    IPO_sme_3 = all_ipos[1]
    IPO_mb_2 = all_ipos[2]
    IPO_sme_2 = all_ipos[3]
    IPO_sme_1 = all_ipos[4]
    IPO_mb_1 = all_ipos[5]

    logger.info(f"Applying for IPOs: MB3={IPO_mb_3}, SME3={IPO_sme_3}, MB2={IPO_mb_2}, SME2={IPO_sme_2}, MB1={IPO_mb_1}, SME1={IPO_sme_1}")
    for ipo in IPO_mb_3:
        logger.info(f"Processing Priority 3 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB3 IPO {ipo}: {e}")

    for ipo in IPO_sme_3:
        logger.info(f"Processing Priority 3 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME3 IPO {ipo}: {e}")
    
    for ipo in IPO_mb_2:
        logger.info(f"Processing Priority 2 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB2 IPO {ipo}: {e}")
        
    for ipo in IPO_sme_2:
        logger.info(f"Processing Priority 2 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME2 IPO {ipo}: {e}")

    for ipo in IPO_mb_1:
        logger.info(f"Processing Priority 1 Mainboard IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="mb")
        except Exception as e:
            logger.exception(f"Error applying to MB1 IPO {ipo}: {e}")

    for ipo in IPO_sme_1:
        logger.info(f"Processing Priority 1 SME IPO: {ipo}")
        try:
            apply_to_ipo_all_users(ipo_name=ipo, type_ipo="sme")
        except Exception as e:
            logger.exception(f"Error applying to SME1 IPO {ipo}: {e}")