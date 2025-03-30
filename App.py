import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Configure page settings
st.set_page_config(
    page_title="Loan Calculator | AF3005 Assignment",
    page_icon="💰",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stSlider > div > div > div > div {
        background-color: #4f8bf9;
    }
    .stSelectbox > div > div > div > div {
        background-color: #f5f5f5;
    }
    .st-b7 {
        background-color: #f5f5f5;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# App title and description
st.title("💰 Loan Calculator")
st.markdown("""
    ### AF3005 - Programming for Finance - Assignment 2
    **Instructor:** Dr. Usama Arshad  
    **Developed by:** [Your Name]  
    Calculate your loan payments, amortization schedule, and visualize the loan breakdown.
    """)

# Sidebar with user inputs
with st.sidebar:
    st.header("Loan Parameters")
    
    # Loan amount input
    loan_amount = st.number_input(
        "Loan Amount ($)", 
        min_value=1000, 
        max_value=1000000, 
        value=25000, 
        step=1000
    )
    
    # Interest rate input
    interest_rate = st.slider(
        "Annual Interest Rate (%)", 
        min_value=1.0, 
        max_value=20.0, 
        value=5.5, 
        step=0.1
    )
    
    # Loan term input
    loan_term = st.slider(
        "Loan Term (years)", 
        min_value=1, 
        max_value=30, 
        value=5, 
        step=1
    )
    
    # Start date input
    start_date = st.date_input(
        "Start Date", 
        value=datetime.now()
    )
    
    # Payment frequency selection
    payment_freq = st.selectbox(
        "Payment Frequency", 
        options=["Monthly", "Bi-Weekly", "Weekly"], 
        index=0
    )

# Calculate payment frequency multiplier
if payment_freq == "Monthly":
    payments_per_year = 12
elif payment_freq == "Bi-Weekly":
    payments_per_year = 26
else:  # Weekly
    payments_per_year = 52

# Calculate loan details
def calculate_loan(principal, annual_rate, years, payments_per_year):
    # Convert annual rate to periodic rate
    periodic_rate = annual_rate / 100 / payments_per_year
    
    # Calculate total number of payments
    total_payments = years * payments_per_year
    
    # Calculate payment amount
    if periodic_rate == 0:
        payment = principal / total_payments
    else:
        payment = principal * (periodic_rate * (1 + periodic_rate)**total_payments) / ((1 + periodic_rate)**total_payments - 1)
    
    # Generate amortization schedule
    balance = principal
    amortization = []
    
    for payment_num in range(1, total_payments + 1):
        interest = balance * periodic_rate
        principal_payment = payment - interest
        balance -= principal_payment
        
        # Handle final payment adjustment
        if payment_num == total_payments:
            principal_payment += balance
            balance = 0
        
        amortization.append({
            "Payment #": payment_num,
            "Date": (start_date + pd.DateOffset(months=payment_num*12/payments_per_year)).strftime("%Y-%m-%d"),
            "Payment": round(payment, 2),
            "Principal": round(principal_payment, 2),
            "Interest": round(interest, 2),
            "Balance": round(balance, 2) if balance > 0 else 0
        })
    
    return payment, amortization

# Calculate loan based on user inputs
monthly_payment, amortization_schedule = calculate_loan(
    loan_amount, 
    interest_rate, 
    loan_term, 
    payments_per_year
)

# Display results in columns
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="**Payment Amount**", 
        value=f"${monthly_payment:,.2f}", 
        help=f"Your {payment_freq.lower()} payment amount"
    )

with col2:
    total_payments = len(amortization_schedule)
    total_interest = sum(payment["Interest"] for payment in amortization_schedule)
    st.metric(
        label="**Total Interest**", 
        value=f"${total_interest:,.2f}", 
        help="Total interest paid over loan term"
    )

with col3:
    total_cost = loan_amount + total_interest
    st.metric(
        label="**Total Cost**", 
        value=f"${total_cost:,.2f}", 
        help="Total amount paid (principal + interest)"
    )

# Visualization section
st.header("Loan Visualization")

# Create tabs for different visualizations
tab1, tab2, tab3 = st.tabs(["Amortization Schedule", "Payment Breakdown", "Interest vs Principal"])

with tab1:
    st.subheader("Amortization Schedule")
    schedule_df = pd.DataFrame(amortization_schedule)
    st.dataframe(
        schedule_df, 
        height=300,
        use_container_width=True
    )
    
    # Download button for amortization schedule
    csv = schedule_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="amortization_schedule.csv",
        mime="text/csv"
    )

with tab2:
    st.subheader("Payment Breakdown Over Time")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(
        schedule_df["Payment #"], 
        schedule_df["Principal"], 
        label="Principal"
    )
    ax.plot(
        schedule_df["Payment #"], 
        schedule_df["Interest"], 
        label="Interest"
    )
    ax.set_xlabel("Payment Number")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Payment Composition Over Time")
    ax.legend()
    ax.grid(True)
    
    st.pyplot(fig)

with tab3:
    st.subheader("Interest vs Principal")
    
    # Pie chart
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(
        [loan_amount, total_interest],
        labels=["Principal", "Interest"],
        autopct='%1.1f%%',
        startangle=90,
        colors=['#4f8bf9', '#ff6b6b']
    )
    ax.set_title("Total Payment Composition")
    
    st.pyplot(fig)

# Additional loan information
with st.expander("Loan Details"):
    st.markdown(f"""
    - **Loan Amount:** ${loan_amount:,.2f}
    - **Annual Interest Rate:** {interest_rate}%
    - **Loan Term:** {loan_term} years
    - **Payment Frequency:** {payment_freq}
    - **Number of Payments:** {len(amortization_schedule)}
    - **Total Interest Paid:** ${total_interest:,.2f}
    - **Total Cost of Loan:** ${total_cost:,.2f}
    """)

# Footer
st.markdown("---")
st.markdown("""
    **AF3005 - Programming for Finance**  
    **Spring 2025** | **FAST-NUCES Islamabad**  
    Developed for Assignment 2 - Financial App Development with Streamlit
    """)