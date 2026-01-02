import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection  # เพิ่มตัวนี้ใน requirements.txt ด้วย
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- [ส่วนที่ 1: ความสวยงาม CSS คงไว้เหมือนเดิมทุกประการ] ---
st.set_page_config(page_title="Cafe AI Pro", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&family=Sarabun:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Prompt', 'Sarabun', sans-serif; background-color: #FDFCFB; }
    [data-testid="stSidebar"] { background-color: #3D2B1F !important; border-right: 1px solid #E0E0E0; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    div[data-testid="stMetric"] { background-color: white !important; padding: 20px !important; border-radius: 20px !important; box-shadow: 0 10px 20px rgba(0,0,0,0.05) !important; border: 1px solid #F0F0F0 !important; }
    .stButton>button { border-radius: 12px !important; background: linear-gradient(145deg, #8B5A2B, #6F4E37) !important; color: white !important; font-weight: 600 !important; border: none !important; padding: 0.6rem 1rem !important; width: 100% !important; }
    .stAlert { border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- [ส่วนที่ 2: การเชื่อมต่อ Google Sheets - แทนที่ SQLite เดิม] ---
# 🚩 นำลิงก์ Google Sheets ของคุณมาวางที่นี่
URL = "https://docs.google.com/spreadsheets/d/161Xpwx3u0t-bDuxIbw-lMEISjYVpV2pjuPBMNfXRGFE/edit?usp=sharing"

# สร้างการเชื่อมต่อ
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    # ดึงข้อมูลจาก Google Sheets แทนการดึงจาก SQLite
    data = conn.read(spreadsheet=URL)
    df = pd.DataFrame(data)
    df.dropna(subset=['transaction_date'], inplace=True) # ป้องกันบรรทัดว่าง
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

@st.cache_resource
def load_ai():
    try:
        model = joblib.load('coffee_model.pkl')
        features = joblib.load('features.pkl')
        return model, features
    except: return None, None

# โหลดข้อมูลเข้าตัวแปรหลัก
df = get_data()
model, features_list = load_ai()

# --- [ส่วนที่ 3: ระบบ Login & Session - เหมือนเดิม 100%] ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'role' not in st.session_state: st.session_state['role'] = 'guest'

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Cafe AI Pro</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login"):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
        else: st.error("ລະຫັດບໍ່ຖືກຕ້ອງ")
    st.stop()

# --- [ส่วนที่ 4: Sidebar Menu - เหมือนเดิม 100%] ---
with st.sidebar:
    st.title("☕ Cafe Management")
    st.write(f"ສະຖານະ: **{st.session_state['role'].upper()}**")
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("ເມນູຫຼັກ", ["📝 ບັນທຶກการขขาย", "📜 ປະຫວັດການຂາຍ"])
    st.divider()
    if st.button("🚪 Logout"): 
        st.session_state.clear()
        st.rerun()

# --- [ส่วนที่ 5: Dashboard - คง Logic การคำนวณที่ถูกต้องไว้] ---
if menu == "📊 Dashboard":
    st.header("📊 ພາບລວມທຸລະກິດ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    days_with_data = df[df['transaction_date'] > (today - timedelta(days=30))]['transaction_date'].dt.date.nunique()
    avg_daily = sales_30d / days_with_data if days_with_data > 0 else 0
    
    if avg_daily > 0:
        diff_percent = ((today_sales - avg_daily) / avg_daily) * 100
        if today_sales < avg_daily: st.warning(f"⚠️ **ແຈ້ງເຕືອນ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) ຕ່ຳກວ່າຄ່າສະເລ່ຍ {abs(diff_percent):.1f}%")
        else: st.success(f"🎉 **ຂ່າວດີ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) ສູງກວ່າຄ່າສະເລ່ຍ {diff_percent:.1f}%!")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດມື້ນີ້", f"฿{today_sales:,.0f}", delta=f"{diff_percent:.1f}%" if avg_daily > 0 else None)
    c2.metric("ບິນມື້ນີ້", f"{len(df[df['transaction_date'] == today])}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{sales_30d:,.0f}")
    c4.metric("ສະເລ່ຍ/ວັນ", f"฿{avg_daily:,.0f}")

    st.divider()
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.subheader("🏆 5 ອັນດັບສິນຄ້າຂາຍດີ")
        top_5 = df.groupby('product_detail')['transaction_qty'].sum().nlargest(5).reset_index()
        st.plotly_chart(px.bar(top_5, x='transaction_qty', y='product_detail', orientation='h', color_continuous_scale='Viridis'), use_container_width=True)
    with col_r:
        st.subheader("🕒 ລາຍການຂາຍຫຼ້າສຸດ")
        st.dataframe(df.sort_values(by=['transaction_date', 'transaction_time'], ascending=False).head(8), use_container_width=True)

# --- [ส่วนที่ 6: AI Forecasting - เหมือนเดิม ดึงข้อมูลจาก Sheets] ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Business Intelligence")
    if model is None: st.error("❌ ບໍ່ພົບໄຟລ໌ Model AI")
    else:
        daily_sales = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
        if len(daily_sales) < 7: st.warning("⚠️ ຕ້ອງການຂໍ້ມູນຢ່າງໜ້ອຍ 7 ວັນ")
        else:
            avg_past_7 = daily_sales['total_sales'].tail(7).mean()
            hist = list(daily_sales['total_sales'].tail(7))
            forecast_values = []
            last_date = pd.to_datetime(daily_sales['transaction_date'].max())
            for i in range(1, 8):
                f_date = last_date + timedelta(days=i)
                inp = pd.DataFrame([{'day_of_week': f_date.dayofweek, 'month': f_date.month, 'is_weekend': 1 if f_date.dayofweek >= 5 else 0, 'sales_lag1': hist[-1], 'sales_lag7': hist[0], 'rolling_mean_7': np.mean(hist)}])
                pred = model.predict(inp[features_list])[0]
                forecast_values.append(pred); hist.append(pred); hist.pop(0)
            
            avg_future_7 = np.mean(forecast_values)
            diff_percent = ((avg_future_7 - avg_past_7) / avg_past_7) * 100
            m1, m2, m3 = st.columns(3)
            m1.metric("ສະເລ່ຍ 7 ວັນຜ່ານມາ", f"฿{avg_past_7:,.0f}")
            m2.metric("ຄາດຄະເນ 7 ວັນຂ້າງໜ້າ", f"฿{avg_future_7:,.0f}", delta=f"{diff_percent:.1f}%")
            m3.metric("ສະຖານະຕະຫຼາດ", "📈 ກໍາລັງເຕີบໂຕ" if diff_percent > 0 else "📉 ຊະລໍຕົວ")
            f_df = pd.DataFrame({'ວັນທີ': [(last_date + timedelta(days=i)).date() for i in range(1, 8)], 'ຍອດພະຍາກອນ': forecast_values})
            st.plotly_chart(px.line(f_df, x='ວັນທີ', y='ຍອດພະຍາກອນ', markers=True), use_container_width=True)

# --- [ส่วนที่ 7: บันทึกการขาย - เปลี่ยนให้ Update ลง Google Sheets] ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍໃໝ່ (ระบบออนไลน์)")
    cat_filter = st.selectbox("📂 ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
    all_prods = df[['product_detail', 'product_category', 'unit_price']].drop_duplicates('product_detail')
    filtered_prods = all_prods[all_prods['product_category'] == cat_filter]
    
    if filtered_prods.empty: st.warning(f"⚠️ ຍັງບໍ່ມີຂໍ້ມູນສິນຄ້າໃນໝວດ {cat_filter}")
    else:
        p_name = st.selectbox("🛍️ ເລືອກສິນຄ້າ", filtered_prods['product_detail'])
        u_price = float(filtered_prods[filtered_prods['product_detail'] == p_name]['unit_price'].values[0])
        qty = st.number_input("ຈຳນວນ", min_value=1, value=1)
        total = qty * u_price
        st.info(f"💰 ลาคาต่อหน่วย: {u_price:,.2f} ฿ | **ยอดรวม: {total:,.2f} ฿**")
        
        if st.button("✅ ຢືນຢັນການຂາຍ", type="primary"):
            lao_time = pd.Timestamp.now() + timedelta(hours=7)
            # สร้างแถวข้อมูลใหม่
            new_row = pd.DataFrame([{
                "transaction_date": lao_time.strftime('%Y-%m-%d'),
                "transaction_time": lao_time.strftime('%H:%M:%S'),
                "product_detail": p_name,
                "product_category": cat_filter,
                "transaction_qty": int(qty),
                "unit_price": float(u_price),
                "total_sales": float(total)
            }])
            # รวมข้อมูลเดิมกับข้อมูลใหม่
            updated_df = pd.concat([df, new_row], ignore_index=True)
            # ส่งกลับไปที่ Google Sheets
            conn.update(spreadsheet=URL, data=updated_df)
            st.success(f"ບັນທຶກລົງ Google Sheets สำเร็จ!"); st.balloons(); st.rerun()

# --- [ส่วนที่ 8: ประวัติการขาย - ดึงข้อมูลล่าสุดจาก Sheets] ---
elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ (Online Database)")
    d_search = st.date_input("ຄົ້ນຫາວັນທີ", df['transaction_date'].max())
    # กรองข้อมูล
    filtered = df[df['transaction_date'].dt.date == d_search]
    st.metric("ຍອດລວມວັນນີ້", f"฿{filtered['total_sales'].sum():,.0f}")
    st.dataframe(filtered.sort_values(by='transaction_time', ascending=False), use_container_width=True)

# --- [ส่วนที่ 9: จัดการสินค้า - เหมือนบันทึกการขายแต่เพิ่มแถวสินค้า] ---
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດการเมนูสินค้า")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        n_cat = st.selectbox("ໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ อาหาร"])
        n_p = st.text_input("ຊື່สินค้า")
        n_pr = st.number_input("ราคา", min_value=0.0)
        if st.button("💾 Save Product"):
            lao_time = pd.Timestamp.now() + timedelta(hours=7)
            new_item = pd.DataFrame([{
                "transaction_date": lao_time.strftime('%Y-%m-%d'),
                "transaction_time": '00:00:00',
                "product_detail": n_p,
                "product_category": n_cat,
                "transaction_qty": 0,
                "unit_price": n_pr,
                "total_sales": 0
            }])
            updated_df = pd.concat([df, new_item], ignore_index=True)
            conn.update(spreadsheet=URL, data=updated_df)
            st.success("เพิ่มสินค้าสำเร็จ!"); st.rerun()
