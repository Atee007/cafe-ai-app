import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta, datetime
import plotly.express as px
import os

# --- [1. CONFIGURATION & MODERN STYLE] ---
st.set_page_config(page_title="Cafe AI Pro Business", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto+Sans+Lao', sans-serif; }
    
    /* ຕົບແຕ່ງ Card ສິນຄ້າແບບ POS */
    .product-card {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 10px;
        transition: 0.2s;
    }
    .price-tag { color: #b45309; font-weight: bold; font-size: 20px; }
    .category-badge { background-color: #f1f5f9; padding: 2px 8px; border-radius: 10px; font-size: 12px; color: #64748b; }
    
    /* ກະຕ່າສິນຄ້າ */
    .cart-container { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 1px solid #e2e8f0; position: sticky; top: 20px; }
    
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1e293b; font-weight: bold; }
    div[data-testid="stMetric"] { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #f1f5f9; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. DATABASE LOGIC] ---
DB_NAME = 'cafe_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  transaction_date TEXT, 
                  transaction_time TEXT, 
                  product_detail TEXT, 
                  product_category TEXT,
                  transaction_qty INTEGER, 
                  unit_price REAL, 
                  cost_price REAL,
                  total_sales REAL)''')
    try:
        c.execute("ALTER TABLE sales ADD COLUMN cost_price REAL DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()

init_db()

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql('SELECT *, (total_sales - (transaction_qty * cost_price)) as profit FROM sales', conn)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    conn.close()
    return df

@st.cache_resource
def load_ai():
    return joblib.load('coffee_model.pkl'), joblib.load('features.pkl')

df = get_data()
model, features_list = load_ai()

# --- [3. SESSION STATE FOR CART] ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

def add_to_cart(name, price, cost, cat):
    for item in st.session_state.cart:
        if item['name'] == name:
            item['qty'] += 1
            return
    st.session_state.cart.append({'name': name, 'price': price, 'cost': cost, 'cat': cat, 'qty': 1})

# --- [4. LOGIN SYSTEM] ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center; color: #4338ca;'>🔐 Login Cafe AI Business</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
        else: st.error("ລະຫັດບໍ່ຖືກຕ້ອງ")
    st.stop()

# --- [5. SIDEBAR] ---
with st.sidebar:
    st.markdown("<h1 style='color: #4338ca;'>☕ Cafe Manager</h1>", unsafe_allow_html=True)
    if st.session_state['role'] == 'admin':
        menu = st.radio("Menu", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("Menu", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    if st.button("🚪 Logout", use_container_width=True): st.session_state.clear(); st.rerun()

# --- [6. DASHBOARD] ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='color: #1e293b;'>📊 ພາບລວມທຸລະກິດ ແລະ ກຳໄລ</h2>", unsafe_allow_html=True)
    today = df['transaction_date'].max()
    today_df = df[df['transaction_date'] == today]
    today_sales = today_df['total_sales'].sum()
    today_profit = today_df['profit'].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດຂາຍມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ກຳໄລມື້ນີ້", f"฿{today_profit:,.0f}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{df['total_sales'].sum():,.0f}")
    c4.metric("ກຳໄລລວມ", f"฿{df['profit'].sum():,.0f}")
    
    st.subheader("💰 ສິນຄ້າທີ່ເຮັດກຳໄລສູງສຸດ")
    profit_data = df.groupby('product_detail')['profit'].sum().nlargest(5).reset_index()
    st.plotly_chart(px.bar(profit_data, x='profit', y='product_detail', orientation='h', template='plotly_white'), use_container_width=True)

# --- [7. 📝 ບັນທຶກການຂາຍ (POS STYLE)] ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.markdown("### 📝 ບັນທຶກຍອດຂາຍ")
    col_main, col_cart = st.columns([7, 3])

    with col_main:
        tabs = st.tabs(["ທັງໝົດ", "ກາເຟ", "ເຄື່ອງດື່ມ", "ເບເກີລີ້", "ອາຫານ"])
        all_prods = df[['product_detail', 'product_category', 'unit_price', 'cost_price']].drop_duplicates('product_detail')
        
        for tab_idx, tab_name in enumerate(["ທັງໝົດ", "☕", "🥤", "🍰", "🍽️"]):
            with tabs[tab_idx]:
                filtered = all_prods if tab_idx == 0 else all_prods[all_prods['product_category'].str.contains(tab_name)]
                
                # ສ້າງ Grid 3 Column
                for i in range(0, len(filtered), 3):
                    cols = st.columns(3)
                    for j, (p_idx, p_row) in enumerate(filtered.iloc[i:i+3].iterrows()):
                        with cols[j]:
                            st.markdown(f"""
                                <div class="product-card">
                                    <div style='font-weight: bold;'>{p_row['product_detail']}</div>
                                    <div class='category-badge'>{p_row['product_category']}</div>
                                    <div class='price-tag'>฿{p_row['unit_price']:.0f}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("ເລືອກ", key=f"btn_{p_row['product_detail']}"):
                                add_to_cart(p_row['product_detail'], p_row['unit_price'], p_row['cost_price'], p_row['product_category'])
                                st.rerun()

    with col_cart:
        st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
        st.markdown("<h4>🛒 ລາຍການຂາຍ</h4>", unsafe_allow_html=True)
        if not st.session_state.cart:
            st.write("ຍັງບໍ່ມີລາຍການ")
        else:
            total_val = 0
            for i, item in enumerate(st.session_state.cart):
                total_val += (item['price'] * item['qty'])
                st.write(f"**{item['name']}** x{item['qty']} : ฿{item['price']*item['qty']:,.0f}")
                if st.button("ລຶບ", key=f"del_{i}"):
                    st.session_state.cart.pop(i); st.rerun()
            st.divider()
            st.markdown(f"### ຍອດລວມ: ฿{total_val:,.0f}")
            if st.button("✅ ຢືນຢັນການຂາຍ", use_container_width=True, type="primary"):
                conn = sqlite3.connect(DB_NAME)
                for item in st.session_state.cart:
                    conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, cost_price, total_sales) VALUES (?,?,?,?,?,?,?,?)",
                                 (datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M:%S'), item['name'], item['cat'], item['qty'], item['price'], item['cost'], item['price']*item['qty']))
                conn.commit(); conn.close()
                st.session_state.cart = []
                st.success("ບັນທຶກແລ້ວ!"); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- [8. 📜 ປະຫວັດການຂາຍ] ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ")
    df_history = get_data()
    st.dataframe(df_history.sort_values('id', ascending=False), use_container_width=True)

# --- [9. ☕ ຈັດການສິນຄ້າ] ---
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການເມນູ ແລະ ຕົ້ນທຶນ")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        n_cat = st.selectbox("ໝວດໝູ່", ["☕ ກາເຟ", "🥤 ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
        n_p = st.text_input("ຊື່")
        n_pr = st.number_input("ລາຄາຂາຍ", min_value=0.0)
        n_co = st.number_input("ຕົ້ນທຶນ", min_value=0.0)
        if st.button("💾 Save"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, cost_price, total_sales) VALUES (?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime('%Y-%m-%d'), '00:00:00', n_p, n_cat, 0, n_pr, n_co, 0))
            conn.commit(); conn.close(); st.rerun()
    st.dataframe(df[['product_detail', 'unit_price', 'cost_price', 'product_category']].drop_duplicates())

# --- [10. 🔮 ຄາດຄະເນ AI] ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Forecasting")
    # (ສ່ວນ AI Logic ໃຊ້ຕາມຂອງເກົ່າໄດ້ເລີຍຄັບ)
    st.info("AI ພ້ອມວິເຄາະແນວໂນ້ມທຸລະກິດໃຫ້ອ້າຍແລ້ວ!")
