
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

st.title("Bilt Rent Points Calculator")

# Input fields
monthly_rent = st.number_input("Monthly Rent Paid ($)", min_value=0.0, value=2500.0, step=100.0)
estimated_non_rent = st.number_input("Estimated Monthly Non-Rent Payments using the card ($)", min_value=0.0, value=500.0, step=50.0)

st.write("--- All values are in $")

# Calculation Method 2: Linear Function
def calculate_method2_points(rent, non_rent):
    return min(1.25 * non_rent, rent)

# Calculation Method 1: Step Function
def calculate_method1_points(rent, non_rent):
    non_rent_percentage = (non_rent / rent) * 100 if rent > 0 else 0
    if non_rent_percentage >= 100:
        multiplier = 1.25
    elif non_rent_percentage >= 75:
        multiplier = 1.0
    elif non_rent_percentage >= 50:
        multiplier = 0.75
    elif non_rent_percentage >= 25:
        multiplier = 0.5
    else:
        return 250
    return multiplier * rent

# Calculate points for user's input
points_method1 = calculate_method1_points(monthly_rent, estimated_non_rent)
points_method2 = calculate_method2_points(monthly_rent, estimated_non_rent)

st.subheader("Your Bilt Points Earned:")
st.write(f"Option 1: {points_method1:.2f} points")
st.write(f"Option 2: {points_method2:.2f} points")

# Determine the better method
if points_method1 > points_method2:
    st.markdown(f"**Method 1 is better for you, earning {points_method1 - points_method2:.2f} more points!**")
elif points_method2 > points_method1:
    st.markdown(f"**Method 2 is better for you, earning {points_method2 - points_method1:.2f} more points!**")
else:
    st.markdown("**Both methods earn you the same number of points!**")

st.subheader("Points Earned by Non-Rent Spent")

# Data for plotting
def generate_plot_data(rent_val):
    non_rent_spents = np.linspace(0, rent_val * 1.5, 300) # Extend non-rent spent to 150% of rent
    data = []
    for non_rent_spent in non_rent_spents:
        points_m1 = calculate_method1_points(rent_val, non_rent_spent)
        points_m2 = calculate_method2_points(rent_val, non_rent_spent)
        data.append({
            'Non-Rent Spent ($)': non_rent_spent,
            'Non-Rent % of Rent': (non_rent_spent / rent_val) * 100 if rent_val > 0 else 0,
            'Method 1 Points': points_m1,
            'Method 2 Points': points_m2,
        })
    return pd.DataFrame(data)

plot_df = generate_plot_data(monthly_rent)

# Initial plot with % of non-rent spent on x-axis
if monthly_rent > 0:
    chart_data = plot_df[['Non-Rent % of Rent', 'Method 1 Points', 'Method 2 Points']].set_index('Non-Rent % of Rent')
    st.line_chart(chart_data)

    # Highlight user's current point
    user_non_rent_percentage = (estimated_non_rent / monthly_rent) * 100
    st.markdown(f"Your current position: {user_non_rent_percentage:.2f}% non-rent spent, Method 1: {points_method1:.2f} points, Method 2: {points_method2:.2f} points")

    # Update plot to use actual $ figures for x-axis when user enters values
    st.subheader("Plot with Actual Dollar Figures")
    chart_data_dollars = plot_df[['Non-Rent Spent ($)', 'Method 1 Points', 'Method 2 Points']].set_index('Non-Rent Spent ($)')
    st.line_chart(chart_data_dollars)

    # Highlight user's current point on dollar plot
    st.markdown(f"Your current position: {estimated_non_rent:.2f}$ non-rent spent, Method 1: {points_method1:.2f} points, Method 2: {points_method2:.2f} points")
else:
    st.write("Please enter a monthly rent greater than 0 to see the plots.")
