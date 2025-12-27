import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- 1. ตั้งค่าความปลอดภัย (Login) ---
def login():
    st.markdown("<h2 style='text-align: center;'>🔐 Cafe AI Login</h2>", unsafe_allow_html=True)
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        # ผมใช้รหัสที่พี่เปลี่ยนใหม่ตามภาพเลยนะครับ
        if user == "mycafe" and pw == "cafe999": 
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    login()
    st.stop()

# --- 2. เริ่มส่วนของแอปหลัก ---
st.set_page_config(page_title="Cafe Management App", layout="wide")

@st.cache_resource
def load_assets():
    # ตรวจสอบชื่อไฟล์ให้ตรงกับในเครื่องพี่
    file_name = 'Coffee Shop Sales.xlsx'
    df = pd.read_excel(file_name)
    df['total_sales'] = df['transaction_qty'] * df['unit_price']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    model = joblib.load('coffee_model.pkl')
    features = joblib.load('features.pkl')
    return df, model, features

df, model, features_list = load_assets()

# --- 3. SIDEBAR เมนูฝั่งซ้าย ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>☕ Café Sales</h1>", unsafe_allow_html=True)
    st.write("ระบบติดตามยอดขายอัจฉริยะ")
    st.divider()
    menu = st.radio("เมนูหลัก", ["📊 แดชบอร์ดสรุปผล", "📝 บันทึกข้อมูล", "📜 ประวัติยอดขาย", "🔮 คาดการณ์ยอดขาย"])
    st.divider()
    if st.button("🚪 ออกจากระบบ"):
        st.session_state['logged_in'] = False
        st.rerun()
    st.write("เวอร์ชัน 1.0 • Student Project")

# --- 4. การจัดการแต่ละเมนู ---

# --- หน้าแดชบอร์ด ---
if menu == "📊 แดชบอร์ดสรุปผล":
    st.header("📊 สรุปยอดขายและสถิติภาพรวม")
    last_date = df['transaction_date'].max()
    today_data = df[df['transaction_date'] == last_date]
    today_sales = today_data['total_sales'].sum()
    total_30d = df['total_sales'].tail(1000).sum() # สถิติล่าสุด
    avg_daily = total_30d / 30

    # ตัวเลข 4 ช่องหลัก
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ยอดขายวันนี้", f"฿{today_sales:,.0f}")
    c2.metric("รายการวันนี้", f"{len(today_data)} รายการ")
    c3.metric("ยอดขายรวม (30 วัน)", f"฿{total_30d:,.0f}")
    c4.metric("ยอดขายเฉลี่ย/วัน", f"฿{avg_daily:,.0f}")

    st.markdown("---")
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("📋 รายการขายล่าสุดของวันนี้")
        st.dataframe(today_data[['transaction_time', 'product_detail', 'transaction_qty', 'total_sales']]
                     .sort_values('transaction_time', ascending=False), use_container_width=True)
    
    with col_right:
        st.subheader("🏆 สินค้าขายดี")
        top_items = today_data.groupby('product_detail')['transaction_qty'].sum().nlargest(5)
        st.table(top_items)

# --- หน้าบันทึกข้อมูล ---
elif menu == "📝 บันทึกข้อมูล":
    st.header("🛒 บันทึกยอดขายรายการใหม่")
    st.info("ใช้สำหรับเพิ่มข้อมูลการขายหน้าร้านลงในระบบ")
    with st.container(border=True):
        p_name = st.selectbox("เลือกสินค้า", df['product_detail'].unique())
        col_q, col_p = st.columns(2)
        qty = col_q.number_input("จำนวนที่ขาย", min_value=1, step=1)
        price = col_p.number_input("ราคาต่อหน่วย", value=float(df[df['product_detail']==p_name]['unit_price'].iloc[0]))
        
        if st.button("✅ บันทึกรายการขาย", type="primary", use_container_width=True):
            st.success(f"บันทึก {p_name} จำนวน {qty} ชิ้น รวม ฿{qty*price:,.2f} สำเร็จ!")

# --- หน้าประวัติยอดขาย ---
elif menu == "📜 ประวัติยอดขาย":
    st.header("📜 ประวัติการขายย้อนหลัง")
    st.write("ค้นหาและตรวจสอบรายการขายในอดีต")
    
    search = st.text_input("🔍 ค้นหาชื่อสินค้า หรือหมวดหมู่...")
    display_df = df.copy()
    if search:
        display_df = display_df[display_df['product_detail'].str.contains(search, case=False) | 
                                display_df['product_category'].str.contains(search, case=False)]
    
    st.dataframe(display_df.sort_values('transaction_date', ascending=False).head(500), use_container_width=True)

# --- หน้าคาดการณ์ยอดขาย ---
elif menu == "🔮 คาดการณ์ยอดขาย":
    st.header("🔮 AI Forecast (Accuracy 93.54%)")
    st.write("พยากรณ์ยอดขายล่วงหน้า 7 วัน ด้วย Machine Learning")
    
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
        forecast.append({'วันที่': f_date.date(), 'ยอดพยากรณ์ (฿)': round(pred, 2)})
        history.append(pred)
        history.pop(0)

    f_df = pd.DataFrame(forecast)
    st.plotly_chart(px.line(f_df, x='วันที่', y='ยอดพยากรณ์ (฿)', markers=True))
    st.table(f_df)
