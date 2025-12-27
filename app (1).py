import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ການຕັ້ງຄ່າຄວາມປອດໄພ ---
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

# --- 2. ຟັງຊັນຈັດການຂໍ້ມູນ (Helper Functions) ---
def load_data():
    df = pd.read_excel('Coffee Shop Sales.xlsx')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    if 'total_sales' not in df.columns:
        df['total_sales'] = df['transaction_qty'] * df['unit_price']
    return df

def save_to_excel(df):
    df.to_excel('Coffee Shop Sales.xlsx', index=False)

# ໂຫລດຂໍ້ມູນເລີ່ມຕົ້ນ
df = load_data()
model = joblib.load('coffee_model.pkl')
features_list = joblib.load('features.pkl')

# --- 3. Sidebar ເມນູ ---
with st.sidebar:
    st.markdown(f"### 👤 ຜູ້ໃຊ້: `{st.session_state['role'].upper()}`")
    st.divider()
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ", ["📊 ແຜງຄວບຄຸມ", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດ & ລຶບຂໍ້ມູນ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("ເມນູຫຼັກ", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    st.divider()
    if st.button("🚪 ອອກຈາກລະບົບ"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 4. ສ່ວນສະແດງຜົນແຕ່ລະເມນູ ---

# 4.1 ແຜງຄວບຄຸມ (Dashboard)
if menu == "📊 ແຜງຄວບຄຸມ":
    st.header("📊 ສະຫຼຸບຍອດຂາຍລວມ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("ຍອດຂາຍມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ຈຳນວນລາຍການ", len(df))
    c3.metric("ສິນຄ້າໃນຮ້ານ", len(df['product_detail'].unique()))
    st.plotly_chart(px.line(df.groupby('transaction_date')['total_sales'].sum().reset_index(), x='transaction_date', y='total_sales'))

# 4.2 ບັນທຶກການຂາຍ (Sales Entry)
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("📝 ບັນທຶກການຂາຍໃໝ່")
    products = df[['product_detail', 'unit_price']].drop_duplicates()
    with st.form("add_sale"):
        p_select = st.selectbox("ເລືອກສິນຄ້າ", products['product_detail'])
        qty = st.number_input("ຈຳນວນ", min_value=1, step=1)
        u_price = products[products['product_detail'] == p_select]['unit_price'].values[0]
        if st.form_submit_button("✅ ບັນທຶກ"):
            new_row = pd.DataFrame([{
                'transaction_date': pd.Timestamp.now(), 'transaction_time': pd.Timestamp.now().strftime('%H:%M:%S'),
                'product_detail': p_select, 'transaction_qty': qty, 'unit_price': u_price, 'total_sales': qty * u_price
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            save_to_excel(df)
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# 4.3 ປະຫວັດ & ລຶບຂໍ້ມູນ (History & Delete)
elif menu == "📜 ປະຫວັດ & ລຶບຂໍ້ມູນ" or menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ")
    if st.session_state['role'] == 'admin':
        st.info("Admin ສາມາດລຶບລາຍການທີ່ຄີຜິດໄດ້ໂດຍການເລືອກ Index")
        del_idx = st.number_input("ໃສ່ເລກ Index ທີ່ຕ້ອງການລຶບ", min_value=0, max_value=len(df)-1, step=1)
        if st.button("🗑️ ລຶບລາຍການນີ້", type="primary"):
            df = df.drop(df.index[del_idx])
            save_to_excel(df)
            st.warning(f"ລຶບລາຍການ Index {del_idx} ສຳເລັດ!")
            st.rerun()
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)

# 4.4 ຈັດການສິນຄ້າ (Product Management - Admin Only)
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການເມນູສິນຄ້າ")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        new_p = st.text_input("ຊື່ສິນຄ້າໃໝ່")
        new_price = st.number_input("ລາຄາ", min_value=0.0)
        if st.button("ບັນທຶກສິນຄ້າ"):
            # จำลองการเพิ่มโดยสร้างรายการขายหลอกๆ เพื่อให้ชื่อสินค้าปรากฏในระบบ
            add_p = pd.DataFrame([{'transaction_date': df['transaction_date'].min(), 'product_detail': new_p, 'unit_price': new_price, 'transaction_qty': 0, 'total_sales': 0}])
            df = pd.concat([df, add_p], ignore_index=True)
            save_to_excel(df)
            st.success(f"ເພີ່ມ {new_p} ແລ້ວ!")
            st.rerun()

# 4.5 ຄາດຄະເນ AI (Forecasting)
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Forecasting (7 Days)")
    daily = df.groupby('transaction_date')['total_sales'].sum().reset_index()
    hist = list(daily['total_sales'].tail(7))
    forecast = []
    for i in range(1, 8):
        f_date = daily['transaction_date'].max() + timedelta(days=i)
        inp = pd.DataFrame([{'day_of_week': f_date.dayofweek, 'month': f_date.month, 'is_weekend': 1 if f_date.dayofweek >= 5 else 0, 'sales_lag1': hist[-1], 'sales_lag7': hist[0], 'rolling_mean_7': np.mean(hist)}])
        pred = model.predict(inp[features_list])[0]
        forecast.append({'ວັນທີ': f_date.date(), 'ຍອດຄາດຄະເນ': round(pred, 2)})
        hist.append(pred); hist.pop(0)
    st.table(pd.DataFrame(forecast))
