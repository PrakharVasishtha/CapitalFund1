def categorize_ipo_industry(company_name: str) -> str:
    """
    Enhanced categorization of IPO companies by industry sector.
    Now with significantly improved coverage for IT & Software companies
    including mobile app development, IT consultancy, Android/iOS apps, etc.
    """
    if not company_name:
        return "Others"

    name = company_name.lower().strip()

    # ==================== IT & SOFTWARE (Enhanced) ====================
    it_keywords = [
        # Core IT & Software
        'software', 'infotech', 'it services', 'technologies', 'tech ', 'digital',
        'cloud', 'saas', 'data ', 'analytics', 'ai ', 'artificial intelligence',
        'cyber','soft','mobile app', 'app development', 'android', 'ios', 'flutter', 'react native','techno',
        'mobile solution', 'app solution','app','solution','soft','consultancy', 'consulting', 'it consultant', 'systems', 'solutions',
        'custom software', 'web development', 'application development','software development', 'digital transformation', 'it services','bpo', 'ites', 'erp', 'crm'
    ]

    if any(keyword in name for keyword in it_keywords):
        return "IT & Software"

    # ==================== Other Categories (unchanged + minor tweaks) ====================
    elif any(word in name for word in ['retail', 'supermarket', 'ecommerce', 'e-commerce', 'fashion', 'apparel', 'fmcg']):
        return "Retail"

    elif any(word in name for word in ['construction', 'civil', 'infrastructure', 'real estate', 'builder', 'developer', 'epc', 'road', 'bridge']):
        return "Construction & Infrastructure"

    elif any(word in name for word in ['pharma', 'pharmaceutical', 'biotech', 'drug', 'medicine', 'healthcare', 'hospital', 'medical', 'lifescience']):
        return "Pharmaceuticals & Healthcare"

    elif any(word in name for word in ['bank', 'finance', 'financial', 'nbfc', 'insurance', 'fintech', 'lending', 'asset management']):
        return "Financial Services"

    elif any(word in name for word in ['manufacturing', 'auto', 'automobile', 'vehicle', 'component', 'engineering', 'machine', 'heavy', 'defence', 'defense']):
        return "Manufacturing & Engineering"

    elif any(word in name for word in ['chemical', 'pesticide', 'agrochem', 'fertilizer', 'paint']):
        return "Chemicals"

    elif any(word in name for word in ['power', 'energy', 'renewable', 'solar', 'wind', 'electricity']):
        return "Power & Energy"

    elif any(word in name for word in ['logistics', 'transport', 'shipping', 'cargo', 'warehouse']):
        return "Logistics & Transportation"

    elif any(word in name for word in ['textile', 'garment', 'fabric', 'yarn', 'jewellery', 'jewelry']):
        return "Textiles & Jewellery"

    elif any(word in name for word in ['food', 'beverage', 'agro', 'agriculture', 'dairy', 'sugar', 'edible oil']):
        return "Food & Agro"

    elif any(word in name for word in ['telecom', 'telecommunication', 'mobile network', 'communication']):
        return "Telecom"

    elif any(word in name for word in ['media', 'entertainment', 'advertising', 'film', 'broadcasting']):
        return "Media & Entertainment"

    elif any(word in name for word in ['steel', 'iron', 'metal', 'mining', 'cement']):
        return "Metals & Mining"

    else:
        return "Others"


def get_industry_score(industry: str) -> float:
    """
    Returns a score between 0.0 and 1.0 based on the industry's current
    IPO attractiveness, growth potential, and recent performance in India (2025-2026).

    Higher score = Higher investor interest / better expected listing & post-listing performance.
    """
    if not industry:
        return 0.4

    ind = industry.lower().strip()

    # High momentum sectors (0.80 - 0.95)
    if any(x in ind for x in ['financial', 'bank', 'fintech', 'insurance', 'nbfc']):
        return 1  # Strongest fundraising and consistent performer

    elif any(x in ind for x in ['it & software', 'it ', 'software', 'digital', 'tech', 'saas', 'ai']):
        return 0.65  # Very strong due to AI, cloud, digital transformation

    elif any(x in ind for x in ['power & energy', 'renewable', 'solar', 'wind', 'energy']):
        return 1  # Green energy push + policy support

    elif any(x in ind for x in ['construction & infrastructure', 'infrastructure', 'epc', 'road']):
        return 1  # Capex cycle and government spending

    elif any(x in ind for x in ['pharmaceuticals & healthcare', 'pharma', 'healthcare', 'biotech', 'medical']):
        return 1  # Steady performer with export + domestic demand

    # Medium-High sectors (0.65 - 0.78)
    elif any(x in ind for x in
             ['manufacturing & engineering', 'manufacturing', 'defence', 'defense', 'auto', 'capital goods']):
        return 1  # PLI scheme and "Make in India" boost

    elif any(x in ind for x in ['chemicals', 'speciality chemical']):
        return 1

    elif any(x in ind for x in ['logistics & transportation', 'logistics', 'transport', 'warehouse']):
        return 1

    # Medium sectors (0.50 - 0.65)
    elif any(x in ind for x in ['food & agro', 'food', 'agro', 'agriculture', 'dairy']):
        return 1

    elif any(x in ind for x in ['telecom', 'communication']):
        return 1

    elif any(x in ind for x in ['jewellery']):
        return 1.

    elif any(x in ind for x in ['media & entertainment','textiles & jewellery','textile']):
        return 1

    elif any(x in ind for x in ['metals & mining', 'steel', 'cement']):
        return 1

    # Retail is volatile → medium
    elif 'retail' in ind:
        return 0.98

    # Default for "Others"
    else:
        return 1.00



#print(categorize_ipo_industry("Clear Secured Services"))