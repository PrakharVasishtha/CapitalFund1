


def calculate_pe_value(po_pe, pre_pe, peers):
    """
    Applies the logic from the provided equations.

    Args:
        pope (float): Input variable POPE
        pre_pe_limited (float): Input variable Pre-PE Limited
        peers (list): Array of peer values [P1, P2, P3, P4, P5]
    """

    # 1. Calculate Initial Limit
    limit = po_pe * 1.34
    if pre_pe > limit:
        pre_pe_limited = limit
    else:
        pre_pe_limited = pre_pe

    # 2. Check if Peers array has fewer than 2 elements
    if len(peers) < 2:
        return -(.5)  # E = 0, Break

    # 3. Create PeersLimited array (clamping each peer to the limit)
    # Note: Usually "Limited" implies min(value, limit)
    peers_limited = [min(p, limit) for p in peers]

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


# --- Example Usage ---
pope_val = 14.22
pre_pe_val = 11.88
peers_list = [61.53]

result = calculate_pe_value(pope_val, pre_pe_val, peers_list)
print(f"The calculated E value is: {result}")