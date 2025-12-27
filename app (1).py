import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ການຕັ້ງຄ່າຄວາມປອດໄພ ແລະ ແຍກສິດ (Admin/Staff) ---
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

# --- 2. ໂຫລດຂໍ້ມູນ ແລະ ໂມເດລ AI ---
@st.cache_resource
def load_assets():
    df = pd.read_excel('Coffee Shop Sales.xlsx')
    df['total_sales'] = df['transaction_qty'] * df['unit_price']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    model = joblib.load('coffee_model.pkl')
    features = joblib.load('features.pkl')
    return df, model, features

df, model, features_list = load_assets()

# --- 3. Sidebar ແຍກເມນູຕາມສິດການໃຊ້ງານ ---
with st.sidebar:
    st.markdown(f"### 👤 ສະຖານະ: `{st.session_state['role'].upper()}`")
    st.divider()
    
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ (Admin)", ["📊 ແຜງຄວບຄຸມ", "🔮 ຄາດຄະເນຍອດຂາຍ", "📜 ປະຫວັດການຂາຍ", "📝 ບັນທຶກການຂາຍ"])
    else:
        menu = st.radio("ເມນູຫຼັກ (Staff)", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
        
    st.divider()
    if st.button("🚪 ອອກຈາກລະບົບ"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 4. ສ່ວນສະແດງຜົນແຕ່ລະເມນູ ---

# 4.1 ໜ້າແຜງຄວບຄຸມ (Admin Only)
if menu == "📊 ແຜງຄວບຄຸມ":
    st.title("📊 ແຜງຄວບຄຸມຍອດຂາຍ (Admin)")
    last_date = df['transaction_date'].max()
    today_data = df[df['transaction_date'] == last_date]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ຍອດຂາຍມື້ນີ້", f"฿{today_data['total_sales'].sum():,.0f}")
    c2.metric("ຈຳນວນບິນ", f"{len(today_data)}")
    c3.metric("ສະເລ່ຍຕໍ່ບິນ", f"฿{today_data['total_sales'].mean():,.0f}")
    
    st.plotly_chart(px.line(df.groupby('transaction_date')['total_sales'].sum().reset_index(), 
                             x='transaction_date', y='total_sales', title="ແນວໂນ້ມຍອດຂາຍລວມ"))

# 4.2 ໜ້າຄາດຄະເນຍອດຂາຍ (Admin Only)
elif menu == "🔮 ຄາດຄະເນຍອດຂາຍ":
    st.title("🔮 AI Forecast (ຄວາມແມ້ນຍຳ 93.54%)")
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
    
    st.plotly_chart(px.bar(pd.DataFrame(forecast), x='ວັນທີ', y='ຍອດຄາດຄະເນ (฿)', color='ຍອດຄາດຄະເນ (฿)'))
    st.table(pd.DataFrame(forecast))

# 4.3 ໜ້າບັນທຶກການຂາຍ (Both Roles)
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.title("📝 ບັນທຶກການຂາຍໃໝ່")
    with st.form("sale_form"):
        product = st.selectbox("ເລືອກສິນຄ້າ", df['product_detail'].unique())
        qty = st.number_input("ຈຳນວນ", min_value=1, step=1)
        # ດຶງລາຄາອັດຕະໂນມັດ
        unit_price = float(df[df['product_detail']==product]['unit_price'].iloc[0])
        
        submitted = st.form_submit_button("✅ ບັນທຶກລາຍການຂาย", use_container_width=True)
        
        if submitted:
            # ສ້າງຂໍ້ມູນແຖວໃໝ່
            new_data = {
                'transaction_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                'transaction_time': pd.Timestamp.now().strftime('%H:%M:%S'),
                'product_detail': product,
                'transaction_qty': qty,
                'unit_price': unit_price
            }
            # ເພີ່ມລົງໃນ DataFrame ແລະ ເຊັບລົງ Excel
            new_row = pd.DataFrame([new_data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            updated_df.to_excel('Coffee Shop Sales.xlsx', index=False)
            
            st.success(f"🎉 ບັນທຶກ {product} ສຳເລັດແລ້ວ! ຍອດລວມ: ฿{qty * unit_price:,.2f}")
            st.info("ກະລຸນາ Refresh ໜ້າເວັບເພື່ອອັບເດດຕົວເລກໃນ Dashboard")

# 4.4 ໜ້າປະຫວັດການຂາຍ (Both Roles)
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.title("📜 ປະຫວັດການຂາຍ")
    search = st.text_input("🔍 ຄົ້ນຫາຊື່ສິນຄ້າ...")
    res = df[df['product_detail'].str.contains(search, case=False)] if search else df
    st.dataframe(res.sort_values('transaction_date', ascending=False).head(100), use_container_width=True)
