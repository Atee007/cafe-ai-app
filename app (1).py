import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os
import gspread  # เพิ่มสำหรับ Google Sheets
from oauth2client.service_account import ServiceAccountCredentials # เพิ่มสำหรับ Google Sheets

# --- [ส่วนที่เพิ่มใหม่: ฟังก์ชันเชื่อมต่อ Google Sheets] ---
def save_to_google_sheets(row_data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # ดึงข้อมูลจาก Streamlit Secrets ที่คุณเพิ่งตั้งค่าไป
        # ต้องมั่นใจว่าในหน้า Secrets คุณพิมพ์หัวข้อว่า [gcp_service_account]
        creds_info = st.secrets["gcp_service_account"]
        
        # ใช้ dict แทนการอ่านไฟล์ .json
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        
        client = gspread.authorize(creds)
        # ตรวจสอบชื่อไฟล์ Google Sheets ต้องตรงกับ "Cafe_Sales_Data" เป๊ะๆ
        sheet = client.open("Cafe_Sales_Data").sheet1
        sheet.append_row(row_data)
        return True
    except Exception as e:
        # พิมพ์ Error ออกมาดูที่หน้าแอปเลยถ้าบันทึกไม่ได้
        st.error(f"ระบบ Online ขัดข้อง: {e}")
        return False

# --- [ส่วนที่ 1: ความสวยงามเดิมของคุณ] ---
st.set_page_config(page_title="Cafe AI Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600&family=Sarabun:wght@400;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Prompt', 'Sarabun', sans-serif; 
        background-color: #FDFCFB; 
    }
    
    [data-testid="stSidebar"] {
        background-color: #3D2B1F !important;
        border-right: 1px solid #E0E0E0;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05) !important;
        border: 1px solid #F0F0F0 !important;
    }
    
    .stButton>button {
        border-radius: 12px !important;
        background: linear-gradient(145deg, #8B5A2B, #6F4E37) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 0.6rem 1rem !important;
        width: 100% !important;
    }
    
    .stAlert { border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. การตั้งค่าและโหลดข้อมูลเดิม ---
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
    
    c.execute("SELECT COUNT(*) FROM sales")
    if c.fetchone()[0] == 0 and os.path.exists('Coffee Shop Sales.xlsx'):
        try:
            ex_df = pd.read_excel('Coffee Shop Sales.xlsx')
            ex_df['transaction_date'] = pd.to_datetime(ex_df['transaction_date']).dt.strftime('%Y-%m-%d')
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
    try:
        model = joblib.load('coffee_model.pkl')
        features = joblib.load('features.pkl')
        return model, features
    except:
        return None, None
        
df = get_data()
model, features_list = load_ai()

# --- 2. ระบบ Login & Session เดิม ---
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
    
# --- 3. Sidebar Menu เดิม ---
with st.sidebar:
    st.title("☕ Cafe Management")
    st.write(f"ສະຖານະ: **{st.session_state['role'].upper()}**")
    if st.session_state['role'] == 'admin':
        menu = st.radio("ເມນູຫຼັກ", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("ເມນູຫຼັກ", ["📝 ບັນທຶກการขาย", "📜 ประวัติการขาย"])
        
    st.divider()
    if st.button("🚪 Logout"): 
        st.session_state.clear()
        st.rerun()
        
# --- 4. Dashboard เดิม ---
if menu == "📊 Dashboard":
    st.header("📊 ພາບລວມທຸລະກິດ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum() 
    days_with_data = df[df['transaction_date'] > (today - timedelta(days=30))]['transaction_date'].dt.date.nunique()
    avg_daily = sales_30d / days_with_data if days_with_data > 0 else 0
    
    if avg_daily > 0:
        diff_percent = ((today_sales - avg_daily) / avg_daily) * 100
        if today_sales < avg_daily:
            st.warning(f"⚠️ **ແຈ້ງເຕືອນ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ຕ່ຳກວ່າ** ຄ່າສະເລ່ຍຢູ່ {abs(diff_percent):.1f}%")
        else:
            st.success(f"🎉 **ຂ່າວດີ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ສູງກວ່າ** ຄ່າສະເລ່ຍເຖິງ {diff_percent:.1f}%!")
            
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
        fig_bar = px.bar(top_5, x='transaction_qty', y='product_detail', orientation='h', 
                         color='transaction_qty', color_continuous_scale='Viridis')
        st.plotly_chart(fig_bar, use_container_width=True)
    with col_r:
        st.subheader("🕒 ລາຍການຂາຍຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(8), use_container_width=True)
        
# --- 5. AI Forecasting เดิม ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Business Intelligence")
    if model is None:
        st.error("❌ ບໍ່ພົບໄຟລ໌ Model AI")
    else:
        daily_sales = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
        if len(daily_sales) < 7:
            st.warning("⚠️ ຕ້ອງການຂໍ້ມູນຢ່າງໜ້ອຍ 7 ວັນ")
        else:
            avg_past_7 = daily_sales['total_sales'].tail(7).mean()
            hist = list(daily_sales['total_sales'].tail(7))
            forecast_values = []
            forecast_dates = []
            last_date = pd.to_datetime(daily_sales['transaction_date'].max())
            
            for i in range(1, 8):
                f_date = last_date + timedelta(days=i)
                inp = pd.DataFrame([{
                    'day_of_week': f_date.dayofweek, 'month': f_date.month, 
                    'is_weekend': 1 if f_date.dayofweek >= 5 else 0, 
                    'sales_lag1': hist[-1], 'sales_lag7': hist[0], 'rolling_mean_7': np.mean(hist)
                }])
                pred = model.predict(inp[features_list])[0]
                forecast_values.append(pred)
                forecast_dates.append(f_date.date())
                hist.append(pred)
                hist.pop(0)
                
            avg_future_7 = np.mean(forecast_values)
            diff_percent = ((avg_future_7 - avg_past_7) / avg_past_7) * 100

            m1, m2, m3 = st.columns(3)
            m1.markdown(f"""<div style="background:white; padding:20px; border-radius:15px; border:1px solid #F0F0F0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <small style="color:gray;">ສະເລ່ຍ 7 ວັນຜ່ານມາ</small><br>
                <strong style="font-size:20px;">฿{avg_past_7:,.2f}</strong></div>""", unsafe_allow_html=True)
            
            m2.markdown(f"""<div style="background:white; padding:20px; border-radius:15px; border:1px solid #F0F0F0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <small style="color:gray;">ຄາດຄະເນ 7 ວັນຂ້າງໜ້າ</small><br>
                <strong style="font-size:20px; color:#8B5A2B;">฿{avg_future_7:,.2f}</strong></div>""", unsafe_allow_html=True)
            
            trend_color = "#22c55e" if diff_percent > 0 else "#ef4444"
            m3.markdown(f"""<div style="background:white; padding:20px; border-radius:15px; border:1px solid #F0F0F0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <small style="color:gray;">ແນວໂນ້ມຕະຫຼາດ</small><br>
                <strong style="font-size:20px; color:{trend_color};">{diff_percent:+.1f}%</strong></div>""", unsafe_allow_html=True)

            st.write("") 
            st.markdown("### 💡 AI Strategic Advice")
            if diff_percent > 5:
                st.info(f"📈 **ແນວໂນ້ມຂາຂຶ້ນ:** ຄາດວ່າອາທິດໜ້າຍອດຂາຍຈະເພີ່ມຂຶ້ນ {diff_percent:.1f}%.")
            elif diff_percent < -5:
                st.error(f"📉 **ແນວໂນ້ມຂາລົງ:** ຍອດຂາຍອາດຫຼຸດລົງ {abs(diff_percent):.1f}%.")
            else:
                st.success("⚖️ **ສະຖານະຄົງທີ່:** ຍອດຂາຍມີແນວໂນ້ມຊົງຕົວ.")

            import plotly.graph_objects as go
            actual_df = daily_sales.tail(7)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=actual_df['transaction_date'], y=actual_df['total_sales'], mode='lines+markers', name='ຍອດຂາຍຈິງ', line=dict(color='#8B5A2B', width=4)))
            fig.add_trace(go.Scatter(x=forecast_dates, y=forecast_values, mode='lines+markers', name='ຄາດຄະເນ', line=dict(color='#8B5A2B', width=4, dash='dash')))
            fig.update_layout(title="ການວິເຄາະແນວໂນ້ມຍອດຂາຍ", xaxis_title="ວັນທີ", yaxis_title="ຍອດຂาย (฿)", hovermode="x unified", plot_bgcolor='white')
            st.plotly_chart(fig, use_container_width=True)
            
# --- 6. บันทึกการขาย (จุดที่มีการรวม Google Sheets เข้าไป) ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍໃໝ່")
    cat_filter = st.selectbox("📂 ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
    all_prods = df[['product_detail', 'product_category', 'unit_price']].drop_duplicates('product_detail')
    filtered_prods = all_prods[all_prods['product_category'] == cat_filter]
    
    if filtered_prods.empty:
        st.warning(f"⚠️ ຍັງບໍ່ມີຂໍ້ມູນສินค้าในหมวด {cat_filter}")
    else:
        p_name = st.selectbox("🛍️ ເລືອກສິນຄ້າ", filtered_prods['product_detail'])
        u_price = float(filtered_prods[filtered_prods['product_detail'] == p_name]['unit_price'].values[0])
        qty = st.number_input("ຈຳນວນ", min_value=1, value=1)
        total = qty * u_price
        
        st.info(f"💰 ລາຄາຕໍ່ໜ່ວຍ: {u_price:,.2f} ฿ | **ยอดรวม: {total:,.2f} ฿**")
        
        # --- [ปรับปรุงปุ่มยืนยันเพื่อให้ส่งข้อมูลไป 2 ที่] ---
        if st.button("✅ ຢືນຢັນການຂາຍ", type="primary"):
            lao_time = pd.Timestamp.now() + timedelta(hours=7)
            current_date = lao_time.strftime('%Y-%m-%d')
            current_time = lao_time.strftime('%H:%M:%S')
            
            # 1. บันทึกลงเครื่อง (SQLite - โค้ดเดิม)
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                         (current_date, current_time, p_name, cat_filter, qty, u_price, total))
            conn.commit(); conn.close()
            
            # 2. บันทึกลง Google Sheets (โค้ดใหม่ที่รวมเข้าไป)
            new_record = [current_date, current_time, p_name, cat_filter, int(qty), float(u_price), float(total)]
            gs_success = save_to_google_sheets(new_record)
            
            if gs_success:
                st.success(f"ບັນທຶກສຳເລັດທັງໃນເຄື່ອງ ແລະ Online! (ເວລາ: {current_time})")
            else:
                st.warning(f"ບັນທຶກในเครื่องสำเเร็จ แต่ Online ผิดพลาด (ตรวจสอบอินเทอร์เน็ต)")
                
            st.balloons(); st.rerun()
            
# --- 7. ประวัติการขาย เดิม ---
elif menu == "📜 ປະຫວັດການຂาย":
    st.header("📜 ປະຫວັດການຂາຍ")
    d_search = st.date_input("ຄົ້ນຫາວັນທີ", df['transaction_date'].max())
    filtered = df[df['transaction_date'].dt.date == d_search]
    st.metric("ຍອດລວມວັນນີ້", f"฿{filtered['total_sales'].sum():,.0f}")
    st.dataframe(filtered.sort_values('id', ascending=False), use_container_width=True)
    
# --- 8. จัดการสินค้า เดิม ---
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດการเมนูสินค้า")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        n_cat = st.selectbox("ໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເเบເກີລີ້", "🍽️ อาหาร"])
        n_p = st.text_input("ຊື່ສินค้า")
        n_pr = st.number_input("ราคา", min_value=0.0)
        if st.button("💾 Save Product"):
            lao_time = pd.Timestamp.now() + timedelta(hours=7)
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                         (lao_time.strftime('%Y-%m-%d'), '00:00:00', n_p, n_cat, 0, n_pr, 0))
            conn.commit(); conn.close(); st.rerun()
