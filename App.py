import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import hashlib
import sqlite3
from PIL import Image

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None

def initialize_database():
    """Creating and configuring the user database"""
    with sqlite3.connect('loan_app.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def register_user(username, password):
    """Securely registering a new user"""
    try:
        with sqlite3.connect('loan_app.db') as conn:
            cursor = conn.cursor()
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username, password):
    """Verifying user credentials"""
    with sqlite3.connect('loan_app.db') as conn:
        cursor = conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT username FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        return cursor.fetchone() is not None


def calculate_amortization_schedule(principal, annual_rate, years, payments_per_year, extra_payment=0):
    periodic_rate = annual_rate / 100 / payments_per_year
    total_payments = years * payments_per_year
    
    if periodic_rate > 0:
        payment = principal * (periodic_rate * (1 + periodic_rate)**total_payments) / ((1 + periodic_rate)**total_payments - 1)
    else:
        payment = principal / total_payments
    
    schedule = []
    balance = principal
    current_date = datetime.now().date()
    
    for payment_num in range(1, total_payments + 1):
        interest = balance * periodic_rate
        principal_payment = min(payment + extra_payment - interest, balance)
        balance -= principal_payment
     
        if payments_per_year == 12:  
            try:
                current_date = current_date.replace(month=current_date.month + 1)
            except ValueError:
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    next_month = current_date.replace(month=current_date.month + 1, day=1)
                    current_date = next_month - timedelta(days=1)
        elif payments_per_year == 26:  # Bi-weekly (every 2 weeks)
            current_date += timedelta(weeks=2)
        elif payments_per_year == 52:  # Weekly
            current_date += timedelta(weeks=1)
        
        schedule.append({
            "Payment #": payment_num,
            "Date": current_date.strftime("%Y-%m-%d"),
            "Payment": round(payment, 2),
            "Extra Payment": round(extra_payment, 2),
            "Total Payment": round(payment + extra_payment, 2),
            "Principal": round(principal_payment, 2),
            "Interest": round(interest, 2),
            "Balance": max(round(balance, 2), 0)
        })
        
        if balance <= 0:
            break
            
    return payment, schedule

def setup_custom_styles():
    """Injecting custom CSS for enhanced visual appeal"""
    st.markdown("""
    <style>
    /* Main app styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: white;
        box-shadow: 2px 0 15px rgba(0,0,0,0.1);
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        border: none;
        background: linear-gradient(90deg, #4f8bf9 0%, #6c5ce7 100%);
        color: white;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    
    /* Input styling */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input,
    .stDateInput>div>div>input {
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4f8bf9 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

def create_auth_interface():
    """Rendering the authentication UI"""
    auth_container = st.empty()
    
    with auth_container.container():
        st.title("🔐 Loan Calculator Authentication")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login_form"):
                st.subheader("Existing Users")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    if authenticate_user(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("register_form"):
                st.subheader("New Users")
                new_username = st.text_input("Choose a username")
                new_password = st.text_input("Create password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if new_password == confirm_password:
                        if register_user(new_username, new_password):
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error("Username already exists")
                    else:
                        st.error("Passwords do not match")

def create_amortization_chart(df):
    """Generating the amortization line chart"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df["Payment #"], df["Principal"], 
            label="Principal", color="#4f8bf9", linewidth=2.5)
    ax.plot(df["Payment #"], df["Interest"], 
            label="Interest", color="#ff6b6b", linewidth=2.5)
    
    if df["Extra Payment"].sum() > 0:
        ax.plot(df["Payment #"], df["Extra Payment"], 
                label="Extra Payment", color="#28a745", linewidth=2.5, linestyle="--")
    
    ax.set_title("Payment Composition Over Time", fontsize=16, pad=20)
    ax.set_xlabel("Payment Number", fontsize=12)
    ax.set_ylabel("Amount ($)", fontsize=12)
    ax.legend(fontsize=10, framealpha=0.9)
    ax.grid(True, alpha=0.2)
    ax.set_facecolor("#f8f9fa")
    
    return fig

def create_payment_pie_chart(principal, total_interest):
    """Generating the payment breakdown pie chart"""
    fig, ax = plt.subplots(figsize=(8, 8))
    
    colors = ['#4f8bf9', '#ff6b6b']
    explode = (0.05, 0)
    
    ax.pie([principal, total_interest],
           labels=["Principal", "Interest"],
           autopct='%1.1f%%',
           startangle=90,
           colors=colors,
           explode=explode,
           shadow=True,
           textprops={'fontsize': 12})
    
    ax.set_title("Total Payment Composition", fontsize=14, pad=20)
    
    return fig


def main_application():
    """The core loan calculator interface"""
    st.set_page_config(
        page_title="Advanced Loan Calculator",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    setup_custom_styles()
    
    st.title("💰 Advanced Loan Calculator")
    st.markdown("""
    <div style="background: linear-gradient(90deg, #4f8bf9 0%, #6c5ce7 100%);
                padding: 1.5rem; 
                border-radius: 12px; 
                color: white;
                margin-bottom: 2rem;">
        <h2 style="color: white; margin: 0;">Smart Loan Analysis Tool</h2>
        <p style="margin: 0.5rem 0 0; opacity: 0.9;">Calculate payments, visualize amortization, and optimize your loans</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Loan Parameters")
        
        loan_amount = st.number_input(
            "Loan Amount ($)", 
            min_value=1000, 
            max_value=1000000, 
            value=25000, 
            step=1000,
            help="The total amount being borrowed"
        )
        
        interest_rate = st.slider(
            "Annual Interest Rate (%)", 
            min_value=0.1, 
            max_value=20.0, 
            value=5.5, 
            step=0.1,
            help="The annual interest rate for the loan"
        )
        
        loan_term = st.select_slider(
            "Loan Term (years)",
            options=list(range(1, 31)),
            value=5,
            help="The duration of the loan in years"
        )
        
        payment_freq = st.radio(
            "Payment Frequency",
            options=["Monthly", "Bi-Weekly", "Weekly"],
            index=0,
            horizontal=True
        )
        
        with st.expander("💎 Extra Payment Options"):
            extra_payment = st.number_input(
                "Additional Payment ($)",
                min_value=0,
                max_value=10000,
                value=0,
                step=100,
                help="Extra amount to pay each period"
            )
        
        st.markdown("---")
        st.markdown(f"Logged in as: **{st.session_state.username}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
    
    freq_map = {"Monthly": 12, "Bi-Weekly": 26, "Weekly": 52}
    payments_per_year = freq_map[payment_freq]
    
    monthly_payment, amortization_schedule = calculate_amortization_schedule(
        loan_amount, interest_rate, loan_term, payments_per_year, extra_payment
    )
    
    schedule_df = pd.DataFrame(amortization_schedule)
    total_interest = schedule_df["Interest"].sum()
    total_cost = loan_amount + total_interest
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4f8bf9; margin-top: 0;">{payment_freq} Payment</h3>
            <h1 style="margin: 0.5rem 0; color: #2c3e50;">${monthly_payment:,.2f}</h1>
            <p style="color: #7f8c8d; margin-bottom: 0;">Base payment amount</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4f8bf9; margin-top: 0;">Total Interest</h3>
            <h1 style="margin: 0.5rem 0; color: #2c3e50;">${total_interest:,.2f}</h1>
            <p style="color: #7f8c8d; margin-bottom: 0;">Over {len(schedule_df)} payments</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4f8bf9; margin-top: 0;">Total Cost</h3>
            <h1 style="margin: 0.5rem 0; color: #2c3e50;">${total_cost:,.2f}</h1>
            <p style="color: #7f8c8d; margin-bottom: 0;">Principal + Interest</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("## 📊 Loan Visualization")
    
    tab1, tab2, tab3 = st.tabs(["Amortization Schedule", "Payment Breakdown", "Interest Analysis"])
    
    with tab1:
        st.markdown("### 📋 Complete Payment Schedule")
        st.dataframe(
            schedule_df.style.format({
                "Payment": "${:,.2f}",
                "Extra Payment": "${:,.2f}",
                "Total Payment": "${:,.2f}",
                "Principal": "${:,.2f}",
                "Interest": "${:,.2f}",
                "Balance": "${:,.2f}"
            }),
            height=500,
            use_container_width=True
        )
        
        csv = schedule_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Schedule as CSV",
            data=csv,
            file_name="loan_amortization_schedule.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab2:
        st.markdown("### 📈 Payment Composition Over Time")
        st.pyplot(create_amortization_chart(schedule_df))
    
    with tab3:
        st.markdown("### 🥧 Interest vs Principal Breakdown")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.pyplot(create_payment_pie_chart(loan_amount, total_interest))
        
        with col2:
            st.markdown("""
            #### Interest Savings Analysis
            
            - **Original Loan Amount:** ${:,.2f}
            - **Total Interest Paid:** ${:,.2f}
            - **Interest Percentage:** {:.1f}% of total payments
            
            {}
            """.format(
                loan_amount,
                total_interest,
                (total_interest / total_cost) * 100,
                "✨ **You're saving money with extra payments!**" if extra_payment > 0 else "💡 Consider adding extra payments to reduce interest"
            ))
   
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; color: #7f8c8d;">
        <p><strong>Advanced Loan Calculator</strong> | AF3005 Programming for Finance</p>
        <p>Developed with ❤️ by Danish Ejaz</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    initialize_database()
    
    if not st.session_state.authenticated:
        create_auth_interface()
    else:
        main_application()