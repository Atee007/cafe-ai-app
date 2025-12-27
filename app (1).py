import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ການຕັ້ງຄ່າ Database SQLite ---
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
    
    # ຍ້າຍຂໍ້ມູນຈາກ Excel (ຖ້າລັນເທື່ອທຳອິດ)
    c.execute("SELECT COUNT(*) FROM sales")
    if c.fetchone()[0] == 0 and os.path.exists('Coffee Shop Sales.xlsx'):
        try:
            ex_df = pd.read_excel('Coffee Shop Sales.xlsx')
            ex_df['transaction_date'] = pd.to_datetime(ex_df['transaction_date']).dt.strftime('%Y-%m-%d')
            # ສຸ່ມໝວດໝູ່ສຳລັບຂໍ້ມູນເກົ່າ
            ex_df['product_category'] = "☕ ເຄື່ອງດື່ມ"
            ex_df['total_sales'] = ex_df['transaction_qty'] * ex_df['unit_price']
            ex_df[['transaction_date', 'transaction_time', 'product_detail', 'product_category', 'transaction_qty', 'unit_price', 'total_sales']].to_sql('sales', conn, if_exists='append', index=False)
        except: pass
    conn.close()

init_db()

def get_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql('SELECT * FROM sales', conn)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    conn.close()
    return df

@st.cache_resource
def load_ai():
    return joblib.load('coffee_model.pkl'), joblib.load('features.pkl')

df = get_data()
model, features_list = load_ai()

# --- 2. ລະບົບ Login ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Cafe AI Pro</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
        else: st.error("ລະຫັດບໍ່ຖືກຕ້ອງ")
    st.stop()

# --- 3. Sidebar ---
with st.sidebar:
    st.title("☕ Cafe Management")
    st.write(f"Status: `{st.session_state['role'].upper()}`")
    menu = st.radio("Menu", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "🔮 ຄາດຄະເນ AI"])
    if st.button("🚪 Logout"): st.session_state.clear(); st.rerun()

# --- 4. Dashboard (ລະອຽດຕາມສັ່ງ) ---
if menu == "📊 Dashboard":
    st.header("📊 Dashboard ພາບລວມ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ບິນມື້ນີ້", f"{len(df[df['transaction_date'] == today])}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{sales_30d:,.0f}")
    c4.metric("ສະເລ່ຍ/ວັນ", f"฿{(sales_30d/30):,.0f}")

    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🏆 ຂາຍດີ 30 ວັນ")
        st.bar_chart(df.groupby('product_detail')['transaction_qty'].sum().nlargest(5))
    with col_r:
        st.subheader("🕒 ລາຍການຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(10), use_container_width=True)

# --- 5. ບັນທຶກການຂາຍ (ມີການສະແດງລາຄາ ແລະ ຍອດລວມ) ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍ")
    
    # 1. ເລືອກໝວດໝູ່
    cat = st.selectbox("ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
    
    # 2. ດຶງຂໍ້ມູນສິນຄ້າ ແລະ ລາຄາ
    prods = df[['product_detail', 'unit_price']].drop_duplicates('product_detail')
    
    with st.form("sale"):
        p_name = st.selectbox("ເລືອກສິນຄ້າ", prods['product_detail'])
        
        # ດຶງລາຄາຕໍ່ໜ່ວຍມາສະແດງ
        u_price = float(prods[prods['product_detail'] == p_name]['unit_price'].values[0])
        st.info(f"💰 ລາຄາຕໍ່ໜ່ວຍ: {u_price:,.2f} ฿")
        
        qty = st.number_input("ຈຳນວນຊິ້ນ", min_value=1, step=1)
        
        # ຄຳນວນຍອດລວມໃຫ້ເຫັນກ່ອນບັນທຶກ
        total_bill = qty * u_price
        st.markdown(f"### 💵 ຍອດລວມບິນນີ້: `{total_bill:,.2f}` ฿")
        
        if st.form_submit_button("✅ ຢືນຢັນການຂາຍ", use_container_width=True):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("""INSERT INTO sales (transaction_date, transaction_time, product_detail, 
                            product_category, transaction_qty, unit_price, total_sales) 
                            VALUES (?,?,?,?,?,?,?)""",
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), 
                          pd.Timestamp.now().strftime('%H:%M:%S'), 
                          p_name, cat, qty, u_price, total_bill))
            conn.commit()
            conn.close()
            st.success(f"🎉 ບັນທຶກສຳເລັດ! ຮັບເງິນ: {total_bill:,.2f} ฿")
            st.rerun()

# --- 6. ປະຫວັດການຂາຍ (ເບິ່ງລາຍວັນ) ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ")
    d_search = st.date_input("ເລືອກວັນທີ", df['transaction_date'].max())
    filtered = df[df['transaction_date'].dt.date == d_search]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("ບິນ", len(filtered))
    m2.metric("ຊິ້ນ", filtered['transaction_qty'].sum())
    m3.metric("ຍອດລວມ", f"฿{filtered['total_sales'].sum():,.0f}")
    
    if st.session_state['role'] == 'admin':
        del_id = st.number_input("ID ທີ່ຕ້ອງການລຶບ", min_value=1, step=1)
        if st.button("🗑️ ລຶບ", type="primary"):
            conn = sqlite3.connect(DB_NAME); conn.execute("DELETE FROM sales WHERE id=?", (int(del_id),))
            conn.commit(); conn.close(); st.rerun()
    st.dataframe(filtered.sort_values('id', ascending=False), use_container_width=True)

# --- 7. AI Forecasting (ມີ %, ສະເລ່ຍ 7 ວັນ) ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 ວິເຄາະແນວໂນ້ມ AI")
    daily = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
    avg_7p = daily['total_sales'].tail(7).mean()
    
    hist = list(daily['total_sales'].tail(7))
    forecast = []
    last_d = pd.to_datetime(daily['transaction_date'].max())
    
    for i in range(1, 8):
        f_date = pd.Timestamp(last_d + timedelta(days=i))
        inp = pd.DataFrame([{'day_of_week':f_date.dayofweek, 'month':f_date.month, 'is_weekend':1 if f_date.dayofweek >=5 else 0, 'sales_lag1':hist[-1], 'sales_lag7':hist[0], 'rolling_mean_7':np.mean(hist)}])
        pred = model.predict(inp[features_list])[0]
        forecast.append(pred); hist.append(pred); hist.pop(0)
    
    avg_7f = np.mean(forecast)
    diff = ((avg_7f - avg_7p) / avg_7p) * 100
    
    a1, a2, a3 = st.columns(3)
    a1.metric("ສະເລ່ຍ 7 ວັນຜ່ານມາ", f"฿{avg_7p:,.2f}")
    a2.metric("ສະເລ່ຍ 7 ວັນຂ້າງໜ້າ", f"฿{avg_7f:,.2f}")
    a3.metric("ແນວໂນ້ມ", f"{abs(diff):.1f}%", delta=("ເພີ່ມຂຶ້ນ" if diff > 0 else "ຫຼຸດລົງ"))
    
    st.plotly_chart(px.bar(x=[(last_d + timedelta(days=i)).date() for i in range(1,8)], y=forecast, title="ພະຍາກອນ 7 ວັນລ່ວງໜ້າ"))
