import numpy as np
from .constants import CARD_DATA


def calculate_method1_points(rent: float, non_rent: float) -> float:
    """
    Calculate rent points using Option 1 (Tier-based).

    Multiplier based on non-rent spending as percentage of rent:
    - >= 100%: 1.25x rent
    - >= 75%: 1.0x rent
    - >= 50%: 0.75x rent
    - >= 25%: 0.5x rent
    - < 25%: Fixed 250 points
    """
    if rent <= 0:
        return 0

    non_rent_percentage = (non_rent / rent) * 100

    if non_rent_percentage >= 100:
        multiplier = 1.25
    elif non_rent_percentage >= 75:
        multiplier = 1.0
    elif non_rent_percentage >= 50:
        multiplier = 0.75
    elif non_rent_percentage >= 25:
        multiplier = 0.5
    else:
        return 250  # Fixed points for low spend

    return multiplier * rent


def calculate_method2_points(rent: float, non_rent: float) -> float:
    """
    Calculate rent points using Option 2 (Bilt Cash method).

    Points = non_rent * 0.04 * 100 / 3, capped at rent amount.
    """
    if rent <= 0:
        return 0

    points = non_rent * 0.04 * 100 / 3
    return min(points, rent)


def calculate_card_annual_value(
    rent: float,
    dining: float,
    grocery: float,
    travel: float,
    other: float,
    card: str,
    rent_option: int,
    cpp: float,
    rent_day_pct: float = 3.33,
    include_signup: bool = True,
    use_hotel_credits: bool = True,
    palladium_meets_min_spend: bool = True,
    obsidian_3x_choice: str = "dining",  # "dining" or "grocery"
    bilt_cash_value: float = 1.0,  # 0.1 to 1.0
    convert_bilt_cash_to_rent: bool = True,  # For Option 2: convert Bilt Cash to rent points?
) -> dict:
    """
    Calculate total annual value for a card.

    Args:
        rent: Monthly rent/mortgage amount
        dining: Monthly dining spending
        grocery: Monthly grocery spending
        travel: Monthly travel spending
        other: Monthly other spending
        card: Card name (from CARD_NAMES)
        rent_option: 1 for tier-based, 2 for Bilt Cash method
        cpp: Cents per point valuation
        rent_day_pct: Percentage of "other" spending on rent day (for Bilt 1.0)
        include_signup: Whether to include Year 1 sign-up bonus
        use_hotel_credits: Whether to value hotel credits
        palladium_meets_min_spend: Whether user will meet Palladium's $4K min spend
        obsidian_3x_choice: For Obsidian, choose "dining" (3X no cap) or "grocery" (3X $25K cap)
        bilt_cash_value: How much user values Bilt Cash (1.0 = full value)

    Returns:
        dict with detailed breakdown of points, cash, credits, and net value
    """
    card_info = CARD_DATA[card]
    total_non_rent = dining + grocery + travel + other

    # --- RENT POINTS (Annual) ---
    if card == "Bilt 1.0":
        annual_rent_points = rent * 12
    elif rent_option == 1:
        monthly_rent_points = calculate_method1_points(rent, total_non_rent)
        annual_rent_points = monthly_rent_points * 12
    elif rent_option == 2 and convert_bilt_cash_to_rent:
        # Option 2 with conversion: earn rent points from Bilt Cash
        monthly_rent_points = calculate_method2_points(rent, total_non_rent)
        annual_rent_points = monthly_rent_points * 12
    else:
        # Option 2 without conversion: no rent points, keep all Bilt Cash
        annual_rent_points = 0

    # --- NON-RENT POINTS (Annual) ---
    # Get default multipliers and ovewrite later by specific card and options
    dining_multiplier = card_info["dining_multiplier"]
    grocery_multiplier = card_info["grocery_multiplier"]
    travel_multiplier = card_info["travel_multiplier"]
    other_multiplier = card_info["other_multiplier"]

    # Dining - handle Obsidian either/or
    if card == "Obsidian":
        if obsidian_3x_choice == "dining":
            dining_multiplier = 3  # No cap
        else:
            dining_multiplier = 1
    annual_dining_points = dining * dining_multiplier * 12

    # Grocery - handle Obsidian either/or with cap
    annual_grocery_spend = grocery * 12
    if card == "Obsidian":
        if obsidian_3x_choice == "grocery":
            # 3X capped at $25K/year
            capped_grocery = min(annual_grocery_spend, card_info["grocery_annual_cap"])
            annual_grocery_points = capped_grocery * 3
            # Remaining grocery at 1X
            annual_grocery_points += max(0, annual_grocery_spend - card_info["grocery_annual_cap"])
        else:
            # 1X if dining is chosen
            annual_grocery_points = annual_grocery_spend * 1
        grocery_multiplier = 3 if obsidian_3x_choice else 1
    elif "grocery_annual_cap" in card_info:
        capped_grocery = min(annual_grocery_spend, card_info["grocery_annual_cap"])
        annual_grocery_points = capped_grocery * card_info["grocery_multiplier"]
        annual_grocery_points += max(0, annual_grocery_spend - card_info["grocery_annual_cap"])
    else:
        annual_grocery_points = annual_grocery_spend * card_info["grocery_multiplier"]

    # Travel
    annual_travel_points = travel * card_info["travel_multiplier"] * 12

    # Other spending
    annual_other_spend = other * 12

    # For Bilt 1.0, rent day bonus applies to ALL non-rent spending
    # The 2x bonus MULTIPLIES ON TOP of the normal category multipliers
    # e.g., Dining: 3x normally, 3x * 2 = 6x on rent day
    rent_day_bonus_points = 0  # Track this separately for breakdown display

    if card == "Bilt 1.0":
        rent_day_fraction = rent_day_pct / 100
        non_rent_day_fraction = 1 - rent_day_fraction

        # The calculation below -1 from this multiplier b/c we already included the first 1x in the base component
        # E.g. $100 on dining and $10 is on rent day. 10 * 6 + 90 * 3 = 100 * 3 + 10 * 3
        rent_day_multiplier = card_info["rent_day_non_rent_multiplier"]  # 2x

        # Dining: 3X normally, 3X * 2X = 6X on rent day
        annual_dining_base = dining * 12 * card_info["dining_multiplier"]
        dining_rent_day_bonus = dining * 12 * rent_day_fraction * card_info["dining_multiplier"] * (rent_day_multiplier - 1)
        annual_dining_points = annual_dining_base + dining_rent_day_bonus

        # Grocery: 1X normally, 1X * 2X = 2X on rent day
        annual_grocery_base = grocery * 12 * card_info["grocery_multiplier"]
        grocery_rent_day_bonus = grocery * 12 * rent_day_fraction * card_info["grocery_multiplier"] * (rent_day_multiplier - 1)
        annual_grocery_points = annual_grocery_base + grocery_rent_day_bonus

        # Travel: 2X normally, 2X * 2X = 4X on rent day
        annual_travel_base = travel * 12 * card_info["travel_multiplier"]
        travel_rent_day_bonus = travel * 12 * rent_day_fraction * card_info["travel_multiplier"] * (rent_day_multiplier - 1)
        annual_travel_points = annual_travel_base + travel_rent_day_bonus

        # Other: 1X normally, 1X * 2X = 2X on rent day
        annual_other_base = other * 12 * card_info["other_multiplier"]
        other_rent_day_bonus = other * 12 * rent_day_fraction * card_info["other_multiplier"] * (rent_day_multiplier - 1)
        annual_other_points = annual_other_base + other_rent_day_bonus

        # Total rent day bonus (the extra points from the 2x multiplier)
        rent_day_bonus_points = dining_rent_day_bonus + grocery_rent_day_bonus + travel_rent_day_bonus + other_rent_day_bonus
    else:
        annual_other_points = annual_other_spend * card_info["other_multiplier"]

    # Total points
    total_non_rent_points = (
        annual_dining_points +
        annual_grocery_points +
        annual_travel_points +
        annual_other_points
    )
    total_points = annual_rent_points + total_non_rent_points

    # --- BILT CASH EARNINGS ---
    annual_non_rent_spend = total_non_rent * 12
    annual_rent_total = rent * 12

    # 4% Bilt Cash - ONLY for Bilt 2.0 cards AND ONLY for Option 2
    if card_info["has_4pct_bilt_cash"] and rent_option == 2:
        bilt_cash_4pct = annual_non_rent_spend * 0.04
    else:
        bilt_cash_4pct = 0

    # Sign-up bonus
    if include_signup:
        signup_cash = card_info["signup_bonus_cash"]
        if card == "Palladium" and palladium_meets_min_spend:
            signup_points = card_info["signup_bonus_points"]
        else:
            signup_points = 0
    else:
        signup_cash = 0
        signup_points = 0

    # Annual Bilt Cash (Palladium only)
    annual_bilt_cash_benefit = card_info["annual_bilt_cash"]

    # Bilt Cash used for rent redemption (only for Option 2 with conversion)
    # Can use 4% Bilt Cash, sign-up bonus cash, annual Bilt Cash, AND $50 per 25K for additional rent points
    # The $50 per 25K is iterative: as you earn more rent points, you get more $50 bonuses,
    # which can be converted to more rent points, until you hit your annual rent cap.
    bilt_cash_used_for_rent = 0
    bilt_cash_4pct_used_for_rent = 0
    rent_points_from_4pct = 0
    rent_points_from_bonus_cash = 0
    bilt_cash_25k_used_for_rent = 0
    bilt_cash_25k_bonus = 0

    if rent_option == 2 and convert_bilt_cash_to_rent and card != "Bilt 1.0":
        # Rent points from 4% Bilt Cash
        rent_points_from_4pct = annual_rent_points  # This was calculated by method2
        # How much 4% Bilt Cash was needed to earn the rent points from non-rent spending
        # $3 Bilt Cash = 100 rent points
        bilt_cash_4pct_used_for_rent = min(bilt_cash_4pct, 3 * annual_rent_points / 100)
        bilt_cash_used_for_rent = bilt_cash_4pct_used_for_rent

        # Fixed bonus cash pool (signup + annual benefit)
        bonus_cash_pool = signup_cash + annual_bilt_cash_benefit
        bonus_cash_used_for_rent = 0

        # Iteratively convert bonus cash (including $50 per 25K) to rent points
        # Each iteration: earn $50 per 25K based on current points, use it for more rent points
        # Continue until rent capacity is filled or no more cash available
        for _ in range(100):  # Max iterations (converges quickly)
            remaining_rent_capacity = annual_rent_total - annual_rent_points
            if remaining_rent_capacity <= 0.01:
                break

            # Calculate current $50 per 25K bonus based on current total points
            # Note: Only rent + non-rent points qualify, NOT signup bonus points
            current_total = annual_rent_points + total_non_rent_points
            current_25k_bonus = (current_total // 25000) * 50

            # Total available cash = fixed pool + current 25K bonus - what's been used
            available_cash = bonus_cash_pool + current_25k_bonus - bonus_cash_used_for_rent

            if available_cash <= 0.01:
                break

            # How much cash needed to fill remaining rent capacity
            cash_needed = remaining_rent_capacity * 3 / 100

            # Use available cash up to what's needed
            cash_to_use = min(available_cash, cash_needed)

            if cash_to_use <= 0.01:
                break

            # Convert to rent points
            new_rent_points = cash_to_use * 100 / 3
            annual_rent_points += new_rent_points
            rent_points_from_bonus_cash += new_rent_points
            bonus_cash_used_for_rent += cash_to_use

        # Final $50 per 25K calculation after all conversions
        final_total = annual_rent_points + total_non_rent_points
        final_25k_bonus = (final_total // 25000) * 50

        # Track how much of each source was used for rent
        # Order of usage: signup first, then annual, then $50 per 25K
        signup_used = min(bonus_cash_used_for_rent, signup_cash)
        annual_used = min(max(0, bonus_cash_used_for_rent - signup_cash), annual_bilt_cash_benefit)
        bilt_cash_25k_used_for_rent = max(0, bonus_cash_used_for_rent - signup_cash - annual_bilt_cash_benefit)

        # Remaining $50 per 25K bonus (what wasn't used for rent)
        bilt_cash_25k_bonus = max(0, final_25k_bonus - bilt_cash_25k_used_for_rent)

        # Update total Bilt Cash used for rent
        bilt_cash_used_for_rent = bilt_cash_4pct_used_for_rent + bonus_cash_used_for_rent

        # Calculate remaining amounts
        signup_cash_remaining = signup_cash - signup_used
        annual_bilt_cash_remaining = annual_bilt_cash_benefit - annual_used

        # Update total points
        total_points = annual_rent_points + total_non_rent_points

    else:
        # For Option 1, Bilt 1.0, or Option 2 without conversion
        if card != "Bilt 1.0":
            bilt_cash_25k_bonus = (total_points // 25000) * 50
        signup_cash_remaining = signup_cash
        annual_bilt_cash_remaining = annual_bilt_cash_benefit

    # Keep bonus_rent_points_from_cash for backwards compatibility (used in display)
    bonus_rent_points_from_cash = rent_points_from_bonus_cash

    # Remaining Bilt Cash after rent redemption
    bilt_cash_remaining_4pct = bilt_cash_4pct - bilt_cash_4pct_used_for_rent

    # Total Bilt Cash (excluding what was used for rent)
    total_bilt_cash = (
        bilt_cash_remaining_4pct +
        bilt_cash_25k_bonus +
        signup_cash_remaining +
        annual_bilt_cash_remaining
    )

    # --- CREDITS ---
    if use_hotel_credits:
        hotel_credit = card_info["hotel_credit"]
    else:
        hotel_credit = 0

    # --- VALUE CALCULATION ---
    # Points value (including signup points)
    all_points = total_points + signup_points
    points_value = all_points * cpp / 100  # cpp is cents, convert to dollars

    # Apply Bilt Cash valuation
    effective_bilt_cash = total_bilt_cash * bilt_cash_value

    # Annual fee
    annual_fee = card_info["annual_fee"]

    # Net annual value
    net_value = points_value + effective_bilt_cash + hotel_credit - annual_fee

    return {
        "card": card,
        "annual_fee": annual_fee,
        # Points breakdown
        "rent_points": annual_rent_points,
        "rent_points_from_4pct": rent_points_from_4pct,
        "rent_points_from_bonus_cash": rent_points_from_bonus_cash,
        "bonus_rent_points_from_cash": bonus_rent_points_from_cash,  # For backwards compatibility
        "dining_points": annual_dining_points,
        "dining_multiplier": dining_multiplier,
        "grocery_points": annual_grocery_points,
        "grocery_multiplier": grocery_multiplier,
        "travel_points": annual_travel_points,
        "travel_multiplier": travel_multiplier,
        "other_points": annual_other_points,
        "other_multiplier": other_multiplier,
        "rent_day_bonus_points": rent_day_bonus_points,  # Bilt 1.0 rent day 2x bonus
        "total_non_rent_points": total_non_rent_points,
        "total_points": total_points,
        "signup_points": signup_points,
        "all_points": all_points,
        "points_value": points_value,
        # Bilt Cash breakdown
        "bilt_cash_4pct": bilt_cash_4pct,
        "bilt_cash_4pct_used_for_rent": bilt_cash_4pct_used_for_rent,
        "bilt_cash_used_for_rent": bilt_cash_used_for_rent,
        "bilt_cash_remaining_4pct": bilt_cash_remaining_4pct,
        "bilt_cash_25k_bonus": bilt_cash_25k_bonus,
        "bilt_cash_25k_used_for_rent": bilt_cash_25k_used_for_rent,
        "bilt_cash_25k_total": bilt_cash_25k_bonus + bilt_cash_25k_used_for_rent,
        "signup_cash": signup_cash,
        "signup_cash_remaining": signup_cash_remaining,
        "annual_bilt_cash": annual_bilt_cash_benefit,
        "annual_bilt_cash_remaining": annual_bilt_cash_remaining,
        "total_bilt_cash": total_bilt_cash,
        "effective_bilt_cash": effective_bilt_cash,
        # Credits
        "hotel_credit": hotel_credit,
        # Summary
        "net_value": net_value,
        # Config used
        "obsidian_3x_choice": obsidian_3x_choice if card == "Obsidian" else None,
        "rent_option": rent_option,
        "convert_bilt_cash_to_rent": convert_bilt_cash_to_rent if rent_option == 2 else None,
    }


def find_best_config_for_card(
    rent: float,
    dining: float,
    grocery: float,
    travel: float,
    other: float,
    card: str,
    cpp: float,
    rent_day_pct: float = 3.33,
    include_signup: bool = True,
    use_hotel_credits: bool = True,
    palladium_meets_min_spend: bool = True,
    bilt_cash_value: float = 1.0,
) -> dict:
    """
    Find the best configuration (rent option, Obsidian 3X choice, conversion) for a card.

    Returns the result dict with the highest net_value.
    """
    best_result = None
    best_value = float('-inf')

    # Try both rent options
    for rent_option in [1, 2]:
        # Try both Obsidian 3X choices (only matters for Obsidian)
        obsidian_choices = ["dining", "grocery"] if card == "Obsidian" else ["dining"]

        # Try both conversion options for Option 2
        # conversion_options = [True, False] if rent_option == 2 else [True]

        # No need to try both sub-option for Option 2, just convert to rent points (most user care about this)
        conversion_options = [True]

        for obsidian_choice in obsidian_choices:
            for convert_to_rent in conversion_options:
                result = calculate_card_annual_value(
                    rent=rent,
                    dining=dining,
                    grocery=grocery,
                    travel=travel,
                    other=other,
                    card=card,
                    rent_option=rent_option,
                    cpp=cpp,
                    rent_day_pct=rent_day_pct,
                    include_signup=include_signup,
                    use_hotel_credits=use_hotel_credits,
                    palladium_meets_min_spend=palladium_meets_min_spend,
                    obsidian_3x_choice=obsidian_choice,
                    bilt_cash_value=bilt_cash_value,
                    convert_bilt_cash_to_rent=convert_to_rent,
                )

                if result["net_value"] > best_value:
                    best_value = result["net_value"]
                    best_result = result

    return best_result


def find_intersections(rent_val: float) -> list:
    """
    Find where Option 1 and Option 2 earn equal rent points.

    Returns list of dicts with 'non_rent' and 'points' keys.
    """
    if rent_val <= 0:
        return []

    intersections = []
    non_rent_values = np.linspace(0, rent_val * 1.5, 10000)

    prev_diff = None
    prev_equal = False
    in_equal_segment = False

    for i, non_rent in enumerate(non_rent_values):
        m1 = calculate_method1_points(rent_val, non_rent)
        m2 = calculate_method2_points(rent_val, non_rent)
        diff = abs(m1 - m2)

        is_equal = diff < 0.01

        if is_equal and not in_equal_segment:
            intersection_point = non_rent
            for pct in [0.25, 0.5, 0.75, 1.0]:
                threshold = pct * rent_val
                if abs(non_rent - threshold) < rent_val * 0.01:
                    intersection_point = threshold
                    break

            intersections.append({
                'non_rent': intersection_point,
                'points': calculate_method1_points(rent_val, intersection_point)
            })
            in_equal_segment = True

        if not is_equal and in_equal_segment:
            in_equal_segment = False

        if prev_diff is not None and not in_equal_segment and not prev_equal:
            sign_change = (m1 - m2) * prev_diff < 0
            if sign_change:
                left = non_rent_values[i-1]
                right = non_rent

                for _ in range(50):
                    mid = (left + right) / 2
                    m1_mid = calculate_method1_points(rent_val, mid)
                    m2_mid = calculate_method2_points(rent_val, mid)
                    diff_mid = m1_mid - m2_mid

                    if abs(diff_mid) < 0.01:
                        intersection_point = mid
                        for pct in [0.25, 0.5, 0.75, 1.0]:
                            threshold = pct * rent_val
                            if abs(mid - threshold) < rent_val * 0.005:
                                intersection_point = threshold
                                break

                        intersections.append({
                            'non_rent': intersection_point,
                            'points': calculate_method1_points(rent_val, intersection_point)
                        })
                        break

                    if np.sign(diff_mid) == np.sign(m1 - m2):
                        right = mid
                    else:
                        left = mid

        prev_diff = m1 - m2
        prev_equal = is_equal

    # Remove duplicates
    filtered = []
    for inter in intersections:
        is_dup = False
        for existing in filtered:
            if abs(inter['non_rent'] - existing['non_rent']) < rent_val * 0.01:
                is_dup = True
                break
        if not is_dup:
            filtered.append(inter)

    return filtered
