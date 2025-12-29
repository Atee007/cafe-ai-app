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
    
    /* สไตล์ Card สินค้าตามรูปที่อ้ายส่งมา */
    .product-card {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #eee;
        text-align: left;
        margin-bottom: 10px;
    }
    .price-tag { color: #7e5233; font-weight: bold; font-size: 20px; margin-top: 5px; }
    .category-badge { background-color: #f0f0f0; padding: 2px 8px; border-radius: 10px; font-size: 12px; color: #666; float: right; }
    
    /* ส่วนกระต่ายอดขายทางขวา */
    .cart-container {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        min-height: 400px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [2. DATABASE LOGIC - คงเดิม] ---
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
    df['profit'] = pd.to_numeric(df['profit'], errors='coerce').fillna(0)
    conn.close()
    return df

@st.cache_resource
def load_ai():
    try:
        return joblib.load('coffee_model.pkl'), joblib.load('features.pkl')
    except: return None, None

df = get_data()
model, features_list = load_ai()

# --- [3. SESSION STATE สำหรับตะกร้าสินค้า] ---
if 'cart' not in st.session_state:
    st.session_state.cart = []

def add_to_cart(name, price, cost, cat):
    for item in st.session_state.cart:
        if item['name'] == name:
            item['qty'] += 1
            return
    st.session_state.cart.append({'name': name, 'price': price, 'cost': cost, 'cat': cat, 'qty': 1})

# --- [4. LOGIN SYSTEM - คงเดิม] ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Cafe AI</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
    st.stop()

# --- [5. SIDEBAR MENU] ---
with st.sidebar:
    st.markdown("## ☕ Cafe Manager")
    if st.session_state['role'] == 'admin':
        menu = st.radio("Menu", ["📊 Dashboard", "📝 ບັນທຶກການຂาย", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 คาดการณ์ AI"])
    else:
        menu = st.radio("Menu", ["📝 ບັນທຶກການຂาย", "📜 ປະຫວັດการขยาย"])
    if st.button("Logout"): st.session_state.clear(); st.rerun()

# --- [6. DASHBOARD - แก้ไขเรื่อง nlargest] ---
if menu == "📊 Dashboard":
    st.header("📊 Dashboard")
    profit_sum = df.groupby('product_detail')['profit'].sum().reset_index()
    if not profit_sum.empty:
        top_5 = profit_sum.nlargest(5, 'profit')
        st.plotly_chart(px.bar(top_5, x='profit', y='product_detail', orientation='h', title="Top 5 Profit"))

# --- [7. 📝 เมนูบันทึกการขาย (ระบบ Card ตามรูปภาพ)] ---
elif menu == "📝 ບັນທຶກการขยาย":
    st.markdown("### บันทึกยอดขาย")
    st.write("เลือกสินค้าและบันทึกรายการขาย")
    
    col_main, col_cart = st.columns([7, 3])

    with col_main:
        # ดึงสินค้าจากฐานข้อมูลมาแสดงเป็นปุ่ม
        all_prods = df[['product_detail', 'product_category', 'unit_price', 'cost_price']].drop_duplicates('product_detail')
        
        tabs = st.tabs(["ทั้งหมด", "กาแฟ", "เครื่องดื่ม", "เบเกอรี่", "อาหาร"])
        cats = ["", "ກາເຟ", "ເຄື່ອງດື່ມ", "ເບເກີລີ້", "ອາຫານ"]
        
        for i, tab in enumerate(tabs):
            with tab:
                filtered = all_prods if i == 0 else all_prods[all_prods['product_category'].str.contains(cats[i], na=False)]
                
                if filtered.empty:
                    st.info("ยังไม่มีสินค้าในหมวดนี้ กรุณาเพิ่มที่เมนู 'จัดการสินค้า'")
                else:
                    # แสดงสินค้าแบบ 3 คอลัมน์
                    for k in range(0, len(filtered), 3):
                        cols = st.columns(3)
                        for idx, (p_idx, p_row) in enumerate(filtered.iloc[k:k+3].iterrows()):
                            with cols[idx]:
                                st.markdown(f"""
                                    <div class="product-card">
                                        <span class="category-badge">{p_row['product_category']}</span>
                                        <b>{p_row['product_detail']}</b><br>
                                        <div class="price-tag">฿{p_row['unit_price']:.0f}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                if st.button("เลือก", key=f"btn_{p_row['product_detail']}"):
                                    add_to_cart(p_row['product_detail'], p_row['unit_price'], p_row['cost_price'], p_row['product_category'])
                                    st.rerun()

    with col_cart:
        st.markdown("<div class='cart-container'>", unsafe_allow_html=True)
        st.markdown("<h4>🛒 รายการขาย</h4>", unsafe_allow_html=True)
        
        if not st.session_state.cart:
            st.write("ยังไม่มีรายการ")
            total_val = 0
        else:
            total_val = 0
            for i, item in enumerate(st.session_state.cart):
                sub = item['price'] * item['qty']
                total_val += sub
                st.write(f"**{item['name']}** x{item['qty']} = ฿{sub:,.0f}")
                if st.button("❌ ลบ", key=f"rem_{i}"):
                    st.session_state.cart.pop(i); st.rerun()
            
            st.divider()
            st.markdown(f"### ยอดรวม: ฿{total_val:,.0f}")
            if st.button("✅ บันทึกยอดขาย", use_container_width=True, type="primary"):
                conn = sqlite3.connect(DB_NAME)
                for item in st.session_state.cart:
                    conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, cost_price, total_sales) VALUES (?,?,?,?,?,?,?,?)",
                                 (datetime.now().strftime('%Y-%m-%d'), datetime.now().strftime('%H:%M:%S'), item['name'], item['cat'], item['qty'], item['price'], item['cost'], item['price']*item['qty']))
                conn.commit(); conn.close()
                st.session_state.cart = []
                st.success("บันทึกสำเร็จ!"); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- [8. 📜 ประวัติการขาย - คงเดิม] ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ประวัติการขาย")
    st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)

# --- [9. ☕ จัดการสินค้า - คงเดิม] ---
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ จัดการเมนูและต้นทุน")
    with st.expander("➕ เพิ่มสินค้าใหม่"):
        n_p = st.text_input("ชื่อสินค้า")
        n_cat = st.selectbox("หมวดหมู่", ["☕ กาแฟ", "🥤 เครื่องดื่ม", "🍰 เบเกอรี่", "🍽️ อาหาร"])
        n_pr = st.number_input("ราคาขาย", min_value=0.0)
        n_co = st.number_input("ต้นทุน", min_value=0.0)
        if st.button("บันทึก"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, cost_price, total_sales) VALUES (?,?,?,?,?,?,?,?)",
                         (datetime.now().strftime('%Y-%m-%d'), '00:00:00', n_p, n_cat, 0, n_pr, n_co, 0))
            conn.commit(); conn.close(); st.rerun()

# --- [10. 🔮 คาดการณ์ AI - คงเดิม] ---
elif menu == "🔮 คาดการณ์ AI":
    st.header("🔮 AI Forecasting")
    if model: st.write("AI Model พร้อมทำงาน...")
