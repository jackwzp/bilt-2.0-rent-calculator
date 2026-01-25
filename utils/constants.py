# Brand colors from brand.html
COLORS = {
    "teal": "#0891B2",
    "teal_light": "#CFFAFE",
    "teal_dark": "#0E7490",
    "navy": "#1E293B",
    "navy_light": "#94A3B8",
    "charcoal": "#0F172A",
    "white": "#F8FAFC",
    "gray": "#64748B",
    "gray_light": "#CBD5E1",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#EF4444",
    "purple": "#8B5CF6",
    "orange": "#F97316",
}

# Card-specific colors for visualizations
CARD_COLORS = {
    "Bilt 1.0": "#64748B",   # Gray - legacy card
    "Blue": "#0891B2",       # Teal - entry level
    "Obsidian": "#1E293B",   # Navy - mid tier
    "Palladium": "#8B5CF6",  # Purple - premium
}

# Card names in display order
CARD_NAMES = ["Bilt 1.0", "Blue", "Obsidian", "Palladium"]

# Cards to include in optimizer (excludes legacy Bilt 1.0)
CARD_NAMES_2_0 = ["Blue", "Obsidian", "Palladium"]

# Card earning rates and benefits
CARD_DATA = {
    "Bilt 1.0": {
        "annual_fee": 0,
        "dining_multiplier": 3,
        "grocery_multiplier": 1,
        "travel_multiplier": 2,
        "other_multiplier": 1,
        "rent_day_non_rent_multiplier": 2,  # 2X on rent day for all non-rent category
        "signup_bonus_cash": 0,
        "signup_bonus_points": 0,
        "hotel_credit": 0,
        "annual_bilt_cash": 0,
        "has_4pct_bilt_cash": False,  # Bilt 1.0 doesn't have this
        "description": "Original Bilt card with 3X dining, 2X on rent day",
    },
    "Blue": {
        "annual_fee": 0,
        "dining_multiplier": 1,
        "grocery_multiplier": 1,
        "travel_multiplier": 1,
        "other_multiplier": 1,
        "rent_day_non_rent_multiplier": 1,  # No rent day bonus
        "signup_bonus_cash": 100,
        "signup_bonus_points": 0,
        "hotel_credit": 0,
        "annual_bilt_cash": 0,
        "has_4pct_bilt_cash": True,
        "description": "No annual fee, 1X everywhere, $100 sign-up bonus",
    },
    "Obsidian": {
        "annual_fee": 95,
        "dining_multiplier": 3,
        "grocery_multiplier": 3,  # Capped at $25K/year
        "grocery_annual_cap": 25000,
        "travel_multiplier": 2,
        "other_multiplier": 1,
        "rent_day_non_rent_multiplier": 1,
        "signup_bonus_cash": 200,
        "signup_bonus_points": 0,
        "hotel_credit": 100,  # $100 annual hotel credit
        "annual_bilt_cash": 0,
        "has_4pct_bilt_cash": True,
        "description": "$95/year, 3X dining/grocery, 2X travel, $100 hotel credit",
    },
    "Palladium": {
        "annual_fee": 495,
        "dining_multiplier": 2,
        "grocery_multiplier": 2,
        "travel_multiplier": 2,
        "other_multiplier": 2,
        "rent_day_non_rent_multiplier": 2,
        "signup_bonus_cash": 300,
        "signup_bonus_points": 50000,  # Requires $4K spend in 3 months
        "hotel_credit": 400,  # $400 annual hotel credit
        "annual_bilt_cash": 200,  # $200 annual Bilt Cash
        "has_4pct_bilt_cash": True,
        "description": "$495/year, 2X everywhere, $400 hotel credit, $200 Bilt Cash",
    },
}

# Default values
DEFAULT_CPP = 1.5  # cents per point
DEFAULT_RENT = 2000.0
DEFAULT_NON_RENT = 750.0
DEFAULT_RENT_DAY_PCT = 5.0  # 5%

# CPP options for dropdown
CPP_OPTIONS = {
    "1.0 cpp (Cash/Statement)": 1.0,
    "1.5 cpp (Average Transfer)": 1.5,
    "2.0 cpp (Good Transfer)": 2.0,
    "Custom": None,
}
