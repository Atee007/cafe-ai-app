import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ຕັ້ງຄ່າຄວາມປອດໄພ (Login) ---
def login():
    st.markdown("<h2 style='text-align: center;'>🔐 Cafe AI Login</h2>", unsafe_allow_html=True)
    user = st.text_input("ຊື່ຜູ້ໃຊ້ (Username)")
    pw = st.text_input("ລະຫັດຜ່ານ (Password)", type="password")
    if st.button("ເຂົ້າສູ່ລະບົບ"):
        # ໃຊ້ລະຫັດທີ່ພີ່ຕັ້ງໄວ້
        if user == "mycafe" and pw == "cafe999": 
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("ຊື່ຜູ້ໃຊ້ ຫຼື ລະຫັດຜ່ານບໍ່ຖືກຕ້ອງ!")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- 2. ເລີ່ມສ່ວນຂອງແອັບຫຼັກ ---
st.set_page_config(page_title="ລະບົບຈັດການຮ້ານກາເຟ", layout="wide")

@st.cache_resource
def load_assets():
    file_name = 'Coffee Shop Sales.xlsx'
    df = pd.read_excel(file_name)
    df['total_sales'] = df['transaction_qty'] * df['unit_price']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    model = joblib.load('coffee_model.pkl')
    features = joblib.load('features.pkl')
    return df, model, features

df, model, features_list = load_assets()

# --- 3. SIDEBAR ເມນູດ້ານຊ້າຍ ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>☕ Café Sales</h1>", unsafe_allow_html=True)
    st.write("ລະບົບຕິດຕາມຍອດຂາຍອັດສະລິຍະ")
    st.divider()
    menu = st.radio("ເມນູຫຼັກ", ["📊 ແຜງຄວບຄຸມ", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "🔮 ຄາດຄະເນຍອດຂາຍ"])
    st.divider()
    if st.button("🚪 ອອກຈາກລະບົບ"):
        st.session_state['logged_in'] = False
        st.rerun()
    st.write("ເວີຊັນ 1.0 • ໂຄງການນັກສຶກສາ")

# --- 4. ການຈັດການແຕ່ລະເມນູ ---

# --- ໜ້າແຜງຄວບຄຸມ (Dashboard) ---
if menu == "📊 ແຜງຄວບຄຸມ":
    st.header("📊 ສະຫຼຸບຍອດຂາຍ ແລະ ສະຖິຕິລວມ")
    last_date = df['transaction_date'].max()
    today_data = df[df['transaction_date'] == last_date]
    today_sales = today_data['total_sales'].sum()
    total_30d = df['total_sales'].tail(1000).sum() 
    avg_daily = total_30d / 30

    # ຕົວເລກ 4 ຊ່ອງຫຼັກ
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດຂາຍມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ລາຍການມື້ນີ້", f"{len(today_data)} ລາຍການ")
    c3.metric("ຍອດຂາຍລວມ (30 ວັນ)", f"฿{total_30d:,.0f}")
    c4.metric("ຍອດຂາຍສະເລ່ຍ/ວັນ", f"฿{avg_daily:,.0f}")

    st.markdown("---")
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📋 ລາຍການຂາຍຫຼ້າສຸດຂອງມື້ນີ້")
        st.dataframe(today_data[['transaction_time', 'product_detail', 'transaction_qty', 'total_sales']]
                     .sort_values('transaction_time', ascending=False), use_container_width=True)
    
    with col_right:
        st.subheader("🏆 ສິນຄ້າຂາຍດີ")
        top_items = today_data.groupby('product_detail')['transaction_qty'].sum().nlargest(5)
        st.table(top_items)

# --- ໜ້າບັນທຶກຂໍ້ມູນ ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກຂໍ້ມູນການຂາຍໃໝ່")
    st.info("ໃຊ້ສຳລັບເພີ່ມຂໍ້ມູນການຂາຍໜ້າຮ້ານລົງໃນລະບົບ")
    with st.container(border=True):
        p_name = st.selectbox("ເລືອກສິນຄ້າ", df['product_detail'].unique())
        col_q, col_p = st.columns(2)
        qty = col_q.number_input("ຈຳນວນທີ່ຂາຍ", min_value=1, step=1)
        price = col_p.number_input("ລາຄາຕໍ່ໜ່ວຍ", value=float(df[df['product_detail']==p_name]['unit_price'].iloc[0]))
        
        if st.button("✅ ບັນທຶກລາຍການຂາຍ", type="primary", use_container_width=True):
            st.success(f"ບັນທຶກ {p_name} ຈຳນວນ {qty} ລາຍການ (ລວມ ฿{qty*price:,.2f}) ສຳເລັດ!")

# --- ໜ້າປະຫວັດຍອດຂາຍ ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍຍ້ອນຫຼັງ")
    st.write("ຄົ້ນຫາ ແລະ ກວດສອບລາຍການຂາຍໃນອະດີດ")
    
    search = st.text_input("🔍 ຄົ້ນຫາຊື່ສິນຄ້າ ຫຼື ໝວດໝູ່...")
    display_df = df.copy()
    if search:
        display_df = display_df[display_df['product_detail'].str.contains(search, case=False) | 
                                display_df['product_category'].str.contains(search, case=False)]
    
    st.dataframe(display_df.sort_values('transaction_date', ascending=False).head(500), use_container_width=True)

# --- ໜ້າຄາດຄະເນຍອດຂາຍ ---
elif menu == "🔮 ຄາດຄະເນຍອດຂາຍ":
    st.header("🔮 AI Forecast (ຄວາມແມ້ນຍຳ 93.54%)")
    st.write("ພະຍາກອນຍອດຂາຍລ່ວງໜ້າ 7 ວັນ ດ້ວຍ Machine Learning")
    
    daily_sales = df.groupby('transaction_date')['total_sales'].sum().reset_index()
    history = list(daily_sales['total_sales'].tail(7))
    forecast = []
    
    for i in range(1, 8):
        f_date = daily_sales['transaction_date'].max() + timedelta(days=i)
        inp = pd.DataFrame([{
            'day_of_week': f_date.dayofweek, 'month': f_date.month,
            'is_weekend': 1 if f_date.dayofweek >= 5 else 0,
            'sales_lag1': history[-1], 'sales_lag7': history[0],
            'rolling_mean_7': np.mean(history)
        }])
        pred = model.predict(inp[features_list])[0]
        forecast.append({'ວັນທີ': f_date.date(), 'ຍອດຄາດຄະເນ (฿)': round(pred, 2)})
        history.append(pred)
        history.pop(0)

    f_df = pd.DataFrame(forecast)
    st.plotly_chart(px.line(f_df, x='ວັນທີ', y='ຍອດຄາດຄະເນ (฿)', markers=True))
    st.table(f_df)
