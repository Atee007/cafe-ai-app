import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- ส่วนที่เพิ่มเพื่อความสวยงาม (Inject CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #F8F9FA; }
    
    /* ปรับแต่งปุ่มสินค้า POS ให้ดูเหมือนปุ่มกดจริง */
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid #E0E0E0 !important;
        background-color: white !important;
        color: #333 !important;
        height: 100px !important;
        white-space: normal !important;
        padding: 5px !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #F0F0F0 !important;
        border-color: #6F4E37 !important;
        transform: translateY(-2px);
    }
    
    /* ปุ่มยืนยันการขาย (สีน้ำตาล) */
    div.stButton > button[kind="primary"] {
        background-color: #6F4E37 !important;
        color: white !important;
        height: 50px !important;
    }
    
    /* สไตล์ตะกร้าสินค้า */
    .cart-box {
        background-color: #FFF;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #DDD;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. การตั้งค่าและโหลดข้อมูล ---
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
                  total_sales REAL)''')
    conn.commit()
    conn.close()

init_db()

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql('SELECT * FROM sales', conn)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    # ทำความสะอาดข้อมูลหมวดหมู่เพื่อป้องกัน Error
    df['product_category'] = df['product_category'].fillna("อื่น ๆ")
    conn.close()
    return df

@st.cache_resource
def load_ai():
    try:
        model = joblib.load('coffee_model.pkl')
        features = joblib.load('features.pkl')
        return model, features
    except:
        return None, None

df = get_data()
model, features_list = load_ai()

# --- ระบบ Session สำหรับตะกร้าสินค้า ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}

# --- 2. ระบบ Login ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'role' not in st.session_state: st.session_state['role'] = 'guest'

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Cafe AI Pro</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
        else: st.error("ລະຫັດບໍ່ຖືກຕ້ອງ")
    st.stop()

# --- 3. Sidebar Menu ---
with st.sidebar:
    st.title("☕ Cafe Management")
    st.write(f"ສະຖານະ: **{st.session_state['role'].upper()}**")
    
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("ເມนູຫຼັກ", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    
    st.divider()
    if st.button("🚪 Logout", use_container_width=True): 
        st.session_state.clear()
        st.rerun()

# --- 4. Dashboard (คงเดิม) ---
if menu == "📊 Dashboard":
    st.header("📊 ພາບລວມທຸລະກິດ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    avg_daily = sales_30d / 30 if sales_30d > 0 else 0
    
    diff_percent = ((today_sales - avg_daily) / avg_daily * 100) if avg_daily > 0 else 0
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດມື້ນີ້", f"฿{today_sales:,.0f}", delta=f"{diff_percent:.1f}%" if avg_daily > 0 else None)
    c2.metric("ບິນມື້ນີ້", f"{len(df[df['transaction_date'] == today])}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{sales_30d:,.0f}")
    c4.metric("ສະເລ່ຍ/ວัน", f"฿{avg_daily:,.0f}")

    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("🏆 5 ອັນດັບສິນຄ້າຂາຍດີ")
        top_5 = df.groupby('product_detail')['transaction_qty'].sum().nlargest(5).reset_index()
        fig_bar = px.bar(top_5, x='transaction_qty', y='product_detail', orientation='h', color='transaction_qty', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_r:
        st.subheader("🕒 ລາຍການຂາຍຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(8), use_container_width=True)

# --- 5. 📝 ບັນທຶກการขาย (GRID POS FIXED) ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ລະບົບຂາຍໜ້າຮ້ານ (POS)")
    
    # ดึงข้อมูลสินค้าที่เคยขายหรือเพิ่มไว้
    prods = df[['product_detail', 'product_category', 'unit_price']].drop_duplicates('product_detail')
    
    if prods.empty:
        st.warning("⚠️ ຍັງບໍ່ມີຂໍ້ມູນສິນຄ້າ ກະລຸນາໄປທີ່ເມນູ 'ຈັດການສິນຄ້າ' ເພື່ອເພີ່ມຂໍ້ມູນກ່ອນ")
    else:
        col_grid, col_cart = st.columns([2, 1])
        
        with col_grid:
            # ดึงหมวดหมู่ที่มีอยู่จริงใน Database
            available_cats = prods['product_category'].unique().tolist()
            tabs = st.tabs(available_cats)
            
            for i, cat in enumerate(available_cats):
                with tabs[i]:
                    cat_items = prods[prods['product_category'] == cat]
                    # สร้าง Grid 3 คอลัมน์
                    for j in range(0, len(cat_items), 3):
                        cols = st.columns(3)
                        for k in range(3):
                            if j + k < len(cat_items):
                                item = cat_items.iloc[j+k]
                                name = item['product_detail']
                                price = item['unit_price']
                                # แสดงปุ่ม
                                if cols[k].button(f"{name}\n\n฿{price:,.0f}", key=f"pos_{name}"):
                                    if name in st.session_state.cart:
                                        st.session_state.cart[name]['qty'] += 1
                                    else:
                                        st.session_state.cart[name] = {'qty': 1, 'price': price, 'cat': cat}

        with col_cart:
            st.markdown("### 🛍️ ຕະກ້າ")
            if not st.session_state.cart:
                st.write("ວ່າງເປົ່າ")
            else:
                total_all = 0
                for n, info in list(st.session_state.cart.items()):
                    subtotal = info['qty'] * info['price']
                    total_all += subtotal
                    st.write(f"**{n}** x {info['qty']} = ฿{subtotal:,.0f}")
                
                st.divider()
                st.subheader(f"ລວມ: ฿{total_all:,.0f}")
                
                if st.button("✅ ຢືນຢັນ", type="primary", use_container_width=True):
                    conn = sqlite3.connect(DB_NAME)
                    d_now = pd.Timestamp.now().strftime('%Y-%m-%d')
                    t_now = pd.Timestamp.now().strftime('%H:%M:%S')
                    for n, info in st.session_state.cart.items():
                        conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                                     (d_now, t_now, n, info['cat'], info['qty'], info['price'], info['qty'] * info['price']))
                    conn.commit(); conn.close()
                    st.session_state.cart = {}
                    st.success("ຂາຍສຳເລັດ!"); st.rerun()
                
                if st.button("🗑️ ລ້າງຕະກ້າ", use_container_width=True):
                    st.session_state.cart = {}
                    st.rerun()

# --- เมนูอื่นๆ (คงเดิม) ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ")
    d_search = st.date_input("ວັນທີ", df['transaction_date'].max())
    filtered = df[df['transaction_date'].dt.date == d_search]
    st.dataframe(filtered.sort_values('id', ascending=False), use_container_width=True)

elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການສິນຄ້າ")
    with st.expander("➕ ເພີ່ມສິນຄ້າ"):
        c_in = st.selectbox("ໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ", "อื่น ๆ"])
        n_in = st.text_input("ຊື່")
        p_in = st.number_input("ລາຄາ", min_value=0.0)
        if st.button("Save"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), '00:00:00', n_in, c_in, 0, p_in, 0))
            conn.commit(); conn.close(); st.rerun()

elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Prediction")
    if model is None: st.error("Model Not Found")
    else: st.write("AI กำลังวิเคราะห์ข้อมูลของคุณ...")
