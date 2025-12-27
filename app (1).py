import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ການຕັ້ງຄ່າ Database SQLite (ແທນທີ່ Excel ເພື່ອຄວາມໄວ) ---
DB_NAME = 'cafe_database.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # ສ້າງຕາຕະລາງຍອດຂາຍ (ຖ້າຍັງບໍ່ມີ)
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  transaction_date TEXT, 
                  transaction_time TEXT, 
                  product_detail TEXT, 
                  transaction_qty INTEGER, 
                  unit_price REAL, 
                  total_sales REAL)''')
    conn.commit()
    
    # ຍ້າຍຂໍ້ມູນຈາກ Excel ເຂົ້າ Database (ເຮັດເທື່ອດຽວຕອນເລີ່ມໂຄງການ)
    c.execute("SELECT COUNT(*) FROM sales")
    if c.fetchone()[0] == 0:
        if os.path.exists('Coffee Shop Sales.xlsx'):
            try:
                excel_df = pd.read_excel('Coffee Shop Sales.xlsx')
                excel_df['transaction_date'] = pd.to_datetime(excel_df['transaction_date']).dt.strftime('%Y-%m-%d')
                excel_df['total_sales'] = excel_df['transaction_qty'] * excel_df['unit_price']
                excel_df[['transaction_date', 'transaction_time', 'product_detail', 'transaction_qty', 'unit_price', 'total_sales']].to_sql('sales', conn, if_exists='append', index=False)
            except Exception as e:
                st.error(f"Error migrating data: {e}")
    conn.close()

init_db()

# --- 2. ຟັງຊັນຈັດການຂໍ້ມູນ (Helper Functions) ---
def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql('SELECT * FROM sales', conn)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    conn.close()
    return df

@st.cache_resource
def load_ai_assets():
    model = joblib.load('coffee_model.pkl')
    features = joblib.load('features.pkl')
    return model, features

# ໂຫລດຂໍ້ມູນ ແລະ AI
df = get_data()
model, features_list = load_ai_assets()

# --- 3. ການຕັ້ງຄ່າຄວາມປອດໄພ (Login) ---
def login():
    st.markdown("<h2 style='text-align: center;'>🔐 ເຂົ້າສູ່ລະບົບ Cafe AI</h2>", unsafe_allow_html=True)
    user = st.text_input("ຊື່ຜູ້ໃຊ້ (Username)")
    pw = st.text_input("ລະຫັດຜ່ານ (Password)", type="password")
    if st.button("ເຂົ້າສູ່ລະບົບ", use_container_width=True):
        if user == "mycafe" and pw == "cafe999":
            st.session_state['logged_in'] = True
            st.session_state['role'] = 'admin'
            st.rerun()
        elif user == "staff" and pw == "1111":
            st.session_state['logged_in'] = True
            st.session_state['role'] = 'staff'
            st.rerun()
        else:
            st.error("❌ ຊື່ຜູ້ໃຊ້ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- 4. Sidebar ເມນູ ---
with st.sidebar:
    st.markdown(f"### 👤 ຜູ້ໃຊ້: `{st.session_state['role'].upper()}`")
    st.divider()
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ", ["📊 ແຜງຄວບຄຸມ", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດ & ລຶບຂໍ້ມູນ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("ເມນູຫຼັກ", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    st.divider()
    if st.button("🚪 ອອກຈາກລະບົບ"):
        st.session_state.clear()
        st.rerun()

# --- 5. ສ່ວນສະແດງຜົນແຕ່ລະເມນູ ---

# 5.1 ແຜງຄວບຄຸມ (Dashboard)
if menu == "📊 ແຜງຄວບຄຸມ":
    st.header("📊 ສະຫຼຸບຍອດຂາຍລວມ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("ຍອດຂາຍມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ຈຳນວນລາຍການລວມ", len(df))
    c3.metric("ສິນຄ້າໃນຮ້ານ", len(df['product_detail'].unique()))
    
    daily_sales = df.groupby('transaction_date')['total_sales'].sum().reset_index()
    st.plotly_chart(px.line(daily_sales, x='transaction_date', y='total_sales', title="ແນວໂນ້ມຍອດຂາຍ"), use_container_width=True)

# 5.2 ບັນທຶກການຂາຍ (Sales Entry)
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍໃໝ່")
    # ດຶງລາຍຊື່ສິນຄ້າທີ່ມີໃນ Database
    products = df[['product_detail', 'unit_price']].drop_duplicates('product_detail')
    
    with st.form("add_sale"):
        p_select = st.selectbox("ເລືອກສິນຄ້າ", products['product_detail'])
        qty = st.number_input("ຈຳນວນ", min_value=1, step=1)
        u_price = products[products['product_detail'] == p_select]['unit_price'].values[0]
        
        if st.form_submit_button("✅ ບັນທຶກລາຍການ", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            conn.execute('''INSERT INTO sales (transaction_date, transaction_time, product_detail, transaction_qty, unit_price, total_sales) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), 
                          pd.Timestamp.now().strftime('%H:%M:%S'), 
                          p_select, qty, u_price, qty * u_price))
            conn.commit()
            conn.close()
            st.success(f"🎉 ບັນທຶກ {p_select} ສຳເລັດ!")
            st.rerun()

# 5.3 ປະຫວັດ & ລຶບຂໍ້ມູນ (History & Delete)
elif "📜 ປະຫວັດ" in menu:
    st.header("📜 ປະຫວັດການຂາຍ")
    if st.session_state['role'] == 'admin':
        st.info("💡 Admin ສາມາດລຶບລາຍການທີ່ຄີຜິດໄດ້ໂດຍໃຊ້ ID")
        del_id = st.number_input("ໃສ່ເລກ ID ທີ່ຕ້ອງການລຶບ", min_value=1, step=1)
        if st.button("🗑️ ລຶບລາຍການນີ້", type="primary"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("DELETE FROM sales WHERE id = ?", (int(del_id),))
            conn.commit()
            conn.close()
            st.warning(f"⚠️ ລຶບລາຍການ ID {del_id} ສຳເລັດ!")
            st.rerun()
    
    st.dataframe(df.sort_values('id', ascending=False), use_container_width=True)

# 5.4 ຈັດການສິນຄ້າ (Admin Only)
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການເມນູສິນຄ້າ")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່ເຂົ້າລະບົບ"):
        new_p = st.text_input("ຊື່ສິນຄ້າໃໝ່")
        new_price = st.number_input("ລາຄາຕໍ່ໜ່ວຍ", min_value=0.0)
        if st.button("ບັນທຶກສິນຄ້າໃໝ່"):
            conn = sqlite3.connect(DB_NAME)
            # ເພີ່ມຂໍ້ມູນ dummy ເພື່ອໃຫ້ຊື່ສິນຄ້າປາກົດໃນລະບົບ
            conn.execute('''INSERT INTO sales (transaction_date, transaction_time, product_detail, transaction_qty, unit_price, total_sales) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                         (df['transaction_date'].min().strftime('%Y-%m-%d'), '00:00:00', new_p, 0, new_price, 0))
            conn.commit()
            conn.close()
            st.success(f"✅ ເພີ່ມເມນູ {new_p} ຮຽບຮ້ອຍແລ້ວ!")
            st.rerun()

# 5.5 ຄາດຄະເນ AI (Forecasting) - ສະບັບແກ້ໄຂ Error .dayofweek
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Forecasting (7 Days)")
    daily = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
    
    if len(daily) < 7:
        st.warning("⚠️ ຂໍ້ມູນຍັງບໍ່ພໍສຳລັບການພະຍາກອນ (ຕ້ອງການຢ່າງໜ້ອຍ 7 ວັນ)")
    else:
        # ດຶງຍອດຂາຍ 7 ວັນຫຼ້າສຸດ
        hist = list(daily['total_sales'].tail(7))
        forecast = []
        last_date = pd.to_datetime(daily['transaction_date'].max())
        
        for i in range(1, 8):
            # ແກ້ໄຂຈຸດນີ້: ບວກມື້ ແລະ ປ່ຽນເປັນ Timestamp ເພື່ອໃຊ້ .dayofweek ໄດ້
            f_date = pd.Timestamp(last_date + timedelta(days=i))
            
            inp = pd.DataFrame([{
                'day_of_week': f_date.dayofweek, 
                'month': f_date.month,
                'is_weekend': 1 if f_date.dayofweek >= 5 else 0,
                'sales_lag1': hist[-1], 
                'sales_lag7': hist[0],
                'rolling_mean_7': np.mean(hist)
            }])
            
            # ຄາດຄະເນ
            pred = model.predict(inp[features_list])[0]
            forecast.append({'ວັນທີ': f_date.date(), 'ຍອດຄາດຄະເນ (฿)': round(pred, 2)})
            
            # ອັບເດດຄ່າ hist ເພື່ອໃຊ້ພະຍາກອນມື້ຕໍ່ໄປ (Rolling Forecast)
            hist.append(pred)
            hist.pop(0)
        
        # ສະແດງຜົນ
        f_df = pd.DataFrame(forecast)
        st.plotly_chart(px.bar(f_df, x='ວັນທີ', y='ຍອດຄາດຄະເນ (฿)', text_auto='.2s', 
                               title="ພະຍາກອນຍອດຂາຍ 7 ວັນລ່ວງໜ້າ",
                               color='ຍອດຄາດຄະເນ (฿)', color_continuous_scale='Viridis'))
        st.table(f_df)
