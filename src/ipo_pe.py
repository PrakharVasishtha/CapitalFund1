from ipo_base_pe import get_pe, get_peers_pe


def effect_pe_sme(url):
    pe=get_pe(url)
    peers_pe = get_peers_pe(url)
    pre_pe = pe[0]
    po_pe = pe[1]
    # 1. Calculate Initial Limit
    limit = po_pe * 1.34
    if pre_pe > limit:
        pre_pe_limited = limit
    else:
        pre_pe_limited = pre_pe

    # 2. Check if Peers array has fewer than 2 elements
    if len(peers_pe) < 3:
        return -(.5)  # E = 0, Break

    # 3. Create PeersLimited array (clamping each peer to the limit)
    # Note: Usually "Limited" implies min(value, limit)
    peers_limited = [min(p, limit) for p in peers_pe]

    # 4. Create 'All' list: PeersLimited + PrePELimited
    all_values = peers_limited + [pre_pe_limited]

    # 5. Find Lowest Two values
    all_values.sort()
    lowest_two = all_values[:2]
    pel1, pel2 = lowest_two[0], lowest_two[1]

    # 6. Calculate Average of the lowest two
    pel_avg = (pel1 + pel2) / 2

    # 7. Calculate PELA Limit
    pela_limit = pel_avg * 0.93

    # 8. Final Conditional Logic for E
    if po_pe > pela_limit:
        e = -1
    else:
        e = 1
    return e

def effect_pe_mb(url):
    pe=get_pe(url)
    #print(pe)
    peers_pe = get_peers_pe(url)
    #print(peers_pe)
    pre_pe = pe[0]
    po_pe = pe[1]
    if pre_pe > 250 or po_pe > 250:
        return (-.6)
    # 1. Calculate Initial Limit
    gen_upper_limit = po_pe * 1.34
    gen_lower_limit = po_pe / 1.2
    pe_upper_limit = po_pe * 1.4
    if pre_pe > pe_upper_limit:
        pre_pe_limited = pe_upper_limit
    else:
        pre_pe_limited = pre_pe

    # 2. Check if Peers array has fewer than 2 elements
    if len(peers_pe) < 1:
        return -(.3)  # E = 0, Break

    # 3. Create PeersLimited array (clamping each peer to the limit)
    # Note: Usually "Limited" implies min(value, limit)
    peers_upper_limited = [min(p, gen_upper_limit) for p in peers_pe]
    peers_limited = [max(p, gen_lower_limit) for p in peers_upper_limited]
    # 4. Create 'All' list: PeersLimited + PrePELimited
    all_values = peers_limited

    # 5. Find Lowest Two values
    all_values.sort()
    lowest_two = all_values[:2]
    
    three_values  = lowest_two + [pre_pe_limited]
    pel1, pel2, pel3 = three_values[0], three_values[1], three_values[2]
    # 6. Calculate Average of the lowest two
    pel_avg = (pel1 + pel2 + pel3) / 3
    
    # 7. Calculate PELA Limit
    pela_limit = pel_avg * 0.98
    #print(pela_limit)
    # 8. Final Conditional Logic for E
    if po_pe > pela_limit:
        e = -.9
    else:
        e = .7
    return e


# --- Example Usage ---
#url = "https://www.chittorgarh.com/ipo/kiaasa-retail-ipo/2417/"
#url = "https://www.chittorgarh.com/ipo/central-mine-planning-design-institute-ipo/2456/"
#url = "https://www.chittorgarh.com/ipo/shayona-engineering-ipo/2173/"
#url = "https://www.chittorgarh.com/ipo/apsis-aerocom-ipo/2752/"
#url = "https://www.chittorgarh.com/ipo/glottis-ipo/1998/"
#url = "https://www.chittorgarh.com/ipo/fujiyama-power-systems-ipo/2025/"
#url = "https://www.chittorgarh.com/ipo/pine-labs-ipo/2487/"

#result = effect_pe_mb(url)
#result = effect_pe_sme(url)
#print(f"The calculated E value is: {result}")
