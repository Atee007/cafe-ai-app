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
        if user == "mycafe" and pw == "cafe999": # พี่เปลี่ยน User/Pass ตรงนี้ได้ครับ
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
    df = pd.read_excel('Coffee Shop Sales.xlsx')
    df['total_sales'] = df['transaction_qty'] * df['unit_price']
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    model = joblib.load('coffee_model.pkl')
    features = joblib.load('features.pkl')
    return df, model, features

df, model, features_list = load_assets()

# --- 3. SIDEBAR เมนูตามรูปพี่ ---
with st.sidebar:
    st.title("☕ CAFE SYSTEM")
    menu = st.radio("เมนูหลัก", ["📊 แดชบอร์ดสรุปผล", "🔮 คาดการณ์ยอดขาย", "📝 บันทึกข้อมูล", "📜 ประวัติยอดขาย"])
    st.divider()
    if st.button("🚪 ออกจากระบบ"):
        st.session_state['logged_in'] = False
        st.rerun()

# --- 4. หน้าแดชบอร์ด ---
if menu == "📊 แดชบอร์ดสรุปผล":
    st.header("📊 สรุปยอดขายร้านวันนี้")
    last_date = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == last_date]['total_sales'].sum()
    total_30d = df[df['transaction_date'] > (last_date - timedelta(days=30))]['total_sales'].sum()
    avg_daily = total_30d / 30

    c1, c2, c3 = st.columns(3)
    c1.metric("ยอดขายวันนี้", f"฿{today_sales:,.2f}")
    c2.metric("ยอดขายรวม 30 วัน", f"฿{total_30d:,.2f}")
    c3.metric("ยอดขายเฉลี่ยรายวัน", f"฿{avg_daily:,.2f}")

    st.subheader("📋 รายการขายล่าสุดของวันนี้")
    st.dataframe(df[df['transaction_date'] == last_date].sort_values('transaction_time', ascending=False), use_container_width=True)

# --- 5. หน้าคาดการณ์ยอดขาย ---
elif menu == "🔮 คาดการณ์ยอดขาย":
    st.header("🔮 AI Forecast (Accuracy 93.54%)")
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
        forecast.append({'วันที่': f_date.date(), 'พยากรณ์ยอดขาย': round(pred, 2)})
        history.append(pred)
        history.pop(0)

    st.plotly_chart(px.line(pd.DataFrame(forecast), x='วันที่', y='พยากรณ์ยอดขาย', markers=True))
    st.table(pd.DataFrame(forecast))
