"""
config.py
=========
Central configuration and business constants for CapitalFund1.

Single source of truth for:
- IPO fund reserve thresholds
- Listing day loss/UC thresholds
- SMWS trading parameters
- Lifecycle status code constants
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# Capital & Fund Routing Constants
# ==============================================================================
# Standard reserve required per SME IPO application (₹)
SME_IPO_FUND_RESERVE: float = float(os.getenv("SME_IPO_FUND_RESERVE", 280000.0))

# Standard reserve required per Mainboard sNII/Retail IPO application (₹)
MB_IPO_FUND_RESERVE: float = float(os.getenv("MB_IPO_FUND_RESERVE", 209000.0))

# Minimum order sizing for SMWS ETF purchases (₹)
MIN_ETF_ORDER_AMOUNT: float = float(os.getenv("MIN_ETF_ORDER_AMOUNT", 2000.0))

# Zerodha 2-Lakh instant fund withdrawal ceiling (₹)
INSTANT_WITHDRAWAL_LIMIT: float = float(os.getenv("INSTANT_WITHDRAWAL_LIMIT", 200000.0))

# HNI category cutoff threshold (₹)
HNI_MINIMUM_THRESHOLD: float = float(os.getenv("HNI_MINIMUM_THRESHOLD", 200001.0))

# ==============================================================================
# Listing Day Strategy Thresholds
# ==============================================================================
# Mainboard pre-open cancellation loss threshold (%):
# If IEP indicates listing loss > 11.9%, cancel pre-open LC sell order
MAINBOARD_LOSS_CANCEL_THRESHOLD_PCT: float = float(os.getenv("MB_LOSS_THRESHOLD", 11.9))

# SME pre-open cancellation discount threshold (%):
# If IEP indicates listing at a discount (< 0%), cancel pre-open LC sell order
SME_DISCOUNT_CANCEL_THRESHOLD_PCT: float = float(os.getenv("SME_DISCOUNT_THRESHOLD", 0.0))

# Regular session Buyer/Seller depth demand threshold (%)
# If Buyer Ratio >= 60%, monitor for Upper Circuit (UC) for 30 minutes
BUYER_SELLER_HIGH_DEMAND_RATIO: float = float(os.getenv("BUYER_RATIO_HIGH_DEMAND", 60.0))

# ==============================================================================
# SMWS Systematic ETF Strategy Constants
# ==============================================================================
SMWS_DEFAULT_SECURITIES: list[str] = ["NIFTYIETF", "TATAGOLD", "TATSILV"]
SMWS_SHEET_GID: int = int(os.getenv("SMWS_SHEET_GID", 614695683))

# ==============================================================================
# Allotment Lifecycle Status Codes (allotted_holdings.xlsx / SQLite)
# ==============================================================================
class SpecialSessionStatus:
    NOT_STARTED = 0          # Default / idle
    LC_ORDER_PLACED = 1      # 09:00 AM Lower Circuit sell order placed on Kite
    SOLD = 2                 # Order executed in pre-open opening cross
    CANCELED = 3             # Order canceled at 09:32 AM; handed over to regular session
    NEWLY_ALLOTTED = 5       # Newly discovered allotment in portfolio

class RegularSessionStatus:
    NOT_STARTED = 0          # Not started or sold in special session
    ELIGIBLE = 1             # Special session canceled; eligible for regular session sell
    SOLD_OR_GTT_PLACED = 2   # Stepped GTT exit orders placed on Kite
    NOT_SOLD = 3             # Market closed without fulfillment
    HELD_AT_UC = 5           # Buyer ratio >= 60% and locked at Upper Circuit
