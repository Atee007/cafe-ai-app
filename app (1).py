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
    
    /* ปรับแต่ง Card ยอดขายให้เหมือนในรูป */
    div[data-testid="stMetric"] {
        background-color: white !important;
        padding: 20px !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
        border: 1px solid #EFEFEF !important;
    }
    
    /* ปรับแต่งปุ่มให้ดูแพงขึ้น */
    .stButton>button {
        border-radius: 10px !important;
        background-color: #6F4E37 !important; /* สีน้ำตาลกาแฟ */
        color: white !important;
        border: none !important;
        height: 3em !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ການຕັ້ງຄ່າ ແລະ ໂຫຼດຂໍ້ມູນ ---
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

# --- 2. ລະບົບ Login & Session ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'role' not in st.session_state: st.session_state['role'] = 'guest'

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center;'>🔐 Login Cafe AI Pro</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", width="stretch", type="primary"):
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
        menu = st.radio("ເມນູຫຼັກ", ["📝 ບັນທຶກการขาย", "📜 ประวัติการขาย"])
    
    st.divider()
    if st.button("🚪 Logout", width="stretch"): 
        st.session_state.clear()
        st.rerun()

# --- 4. Dashboard (ภาพรวมธุรกิจ) ---
if menu == "📊 Dashboard":
    st.header("📊 ພາບລວມທຸລະກິດ")
    
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    avg_daily = sales_30d / 30 if sales_30d > 0 else 0
    
    # AI Alert Box
    if avg_daily > 0:
        diff_percent = ((today_sales - avg_daily) / avg_daily) * 100
        if today_sales < avg_daily:
            st.warning(f"⚠️ **ແຈ້ງເຕືອນ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ຕ່ຳກວ່າ** ຄ່າສະເລ່ຍຢູ່ {abs(diff_percent):.1f}%")
        else:
            st.success(f"🎉 **ຂ່າວດີ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ສູງກວ່າ** ຄ່າສະເລ່ຍເຖິງ {diff_percent:.1f}%!")

    # Metrics
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
        st.plotly_chart(fig_bar, width="stretch")
    with col_r:
        st.subheader("🕒 ລາຍການຂາຍຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(8), width="stretch")
        # --- เพิ่ม AI Insight ในหน้า Dashboard ---
    st.divider()
    if avg_daily > 0:
        if today_sales > avg_daily:
            st.success(f"💡 **AI Analysis:** ยอดขายวันนี้สูงกว่าค่าเฉลี่ย {((today_sales-avg_daily)/avg_daily)*100:.1f}% เป็นสัญญาณที่ดีมากครับ!")
        else:
            st.warning(f"💡 **AI Analysis:** ยอดขายวันนี้ต่ำกว่าค่าเฉลี่ยเล็กน้อย ลองพิจารณาจัดโปรโมชั่นช่วงเย็นดูนะครับ")

# --- 5. AI Forecasting (ระบบพยากรณ์อัจฉริยะ) ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 AI Business Intelligence")
    
    if model is None:
        st.error("❌ ບໍ່ພົບໄຟລ໌ Model AI (coffee_model.pkl), ກະລຸນາກວດສອບການ Train Model ກ່ອນ")
    else:
        daily_sales = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
        
        if len(daily_sales) < 7:
            st.warning("⚠️ ຕ້ອງການຂໍ້ມູນຢ່າງໜ້ອຍ 7 ວັນເພື່ອໃຫ້ AI ວິເຄາະໄດ້ແມ້ນຢຳ")
        else:
            # Logic AI Prediction
            avg_past_7 = daily_sales['total_sales'].tail(7).mean()
            hist = list(daily_sales['total_sales'].tail(7))
            forecast_values = []
            last_date = pd.to_datetime(daily_sales['transaction_date'].max())
            
            for i in range(1, 8):
                f_date = last_date + timedelta(days=i)
                inp = pd.DataFrame([{
                    'day_of_week': f_date.dayofweek, 'month': f_date.month, 
                    'is_weekend': 1 if f_date.dayofweek >= 5 else 0, 
                    'sales_lag1': hist[-1], 'sales_lag7': hist[0], 'rolling_mean_7': np.mean(hist)
                }])
                pred = model.predict(inp[features_list])[0]
                forecast_values.append(pred); hist.append(pred); hist.pop(0)
                
            avg_future_7 = np.mean(forecast_values)
            diff_percent = ((avg_future_7 - avg_past_7) / avg_past_7) * 100

            # --- 💡 AI Smart Advice ---
            st.markdown("### 💡 AI Strategic Advice")
            advice_col, trend_col = st.columns([2, 1])
            with advice_col:
                if diff_percent > 5:
                    st.info(f"📈 **ແນວໂນ້ມຂາຂຶ້ນ:** ຄາດວ່າອາທິດໜ້າຍອດຂາຍຈະເພີ່ມຂຶ້ນ {diff_percent:.1f}%. ແນະນຳໃຫ້ກຽມວັດຖຸດິບເພີ່ມ ແລະ ເພີ່ມພະນັກງານໃນຊ່ວງພີກ.")
                elif diff_percent < -5:
                    st.error(f"📉 **ແນວໂນ້ມຂາລົງ:** ຍອດຂາຍອາດຫຼຸດລົງ {abs(diff_percent):.1f}%. ແນະນຳໃຫ້ຈັດໂປຣໂມຊັ່ນ 'Happy Hour' ເພື່ອດຶງດູດລູກຄ້າ.")
                else:
                    st.success("⚖️ **ສະຖານະຄົງທີ່:** ຍອດຂາຍມີແນວໂນ້ມຊົງຕົວ. ເນັ້ນການຮັກສາມາດຕະຖານການບໍລິການ.")

            # Metrics
            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("ສະເລ່ຍ 7 ວັນຜ່ານມາ", f"฿{avg_past_7:,.0f}")
            m2.metric("ຄາດຄະເນ 7 ວັນຂ້າງໜ້າ", f"฿{avg_future_7:,.0f}", delta=f"{diff_percent:.1f}%")
            m3.metric("ສະຖານະຕະຫຼາດ", "📈 ກໍາລັງເຕີບໂຕ" if diff_percent > 0 else "📉 ຊະລໍຕົວ")

            # --- 📦 Stock Recommendation ---
            st.subheader("📦 AI Stock Optimization (ແນະນຳການສະຕັອກສິນຄ້າ)")
            next_day_name = (last_date + timedelta(days=1)).day_name()
            df['day_name'] = df['transaction_date'].dt.day_name()
            rec_items = df[df['day_name'] == next_day_name].groupby('product_detail')['transaction_qty'].sum().nlargest(3)
            
            s1, s2, s3 = st.columns(3)
            cols = [s1, s2, s3]
            for i, (item, val) in enumerate(rec_items.items()):
                cols[i].success(f"**{item}**\n\nກຽມສະຕັອກ: +{int(val*1.2)} ຊິ້ນ")

            # Chart
            f_df = pd.DataFrame({
                'ວັນທີ': [(last_date + timedelta(days=i)).date() for i in range(1, 8)], 
                'ຍອດພະຍາກອນ': forecast_values
            })
            fig_line = px.line(f_df, x='ວັນທີ', y='ຍອດພະຍາກອນ', markers=True, text=[f"{v:,.0f}" for v in forecast_values],
                               title="7-Day Sales Forecast Trend", color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig_line, width="stretch")

# --- (ເມນູອື່ນໆຄົງໄວ້ຕາມເດີມ) ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍໃໝ່")
    cat_filter = st.selectbox("📂 ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
    all_prods = df[['product_detail', 'product_category', 'unit_price']].drop_duplicates('product_detail')
    filtered_prods = all_prods[all_prods['product_category'] == cat_filter]
    
    if filtered_prods.empty:
        st.warning(f"⚠️ ຍັງບໍ່ມີຂໍ້ມູນສິນຄ້າໃນໝວດ {cat_filter}")
    else:
        p_name = st.selectbox("🛍️ ເລືອກສິນຄ້າ", filtered_prods['product_detail'])
        u_price = float(filtered_prods[filtered_prods['product_detail'] == p_name]['unit_price'].values[0])
        qty = st.number_input("ຈຳນວນ", min_value=1, value=1)
        total = qty * u_price
        
        st.info(f"💰 ລາຄາຕໍ່ໜ່ວຍ: {u_price:,.2f} ฿ | **ຍອດລວມ: {total:,.2f} ฿**")
        if st.button("✅ ຢືນຢັນການຂາຍ", width="stretch", type="primary"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), pd.Timestamp.now().strftime('%H:%M:%S'), p_name, cat_filter, qty, u_price, total))
            conn.commit(); conn.close()
            st.success("ບັນທຶກສຳເລັດ!"); st.balloons(); st.rerun()

elif menu == "📜 ປະຫວັດການຂາຍ":
    st.header("📜 ປະຫວັດການຂາຍ")
    d_search = st.date_input("ຄົ້ນຫາວັນທີ", df['transaction_date'].max())
    filtered = df[df['transaction_date'].dt.date == d_search]
    st.metric("ຍອດລວມວັນນີ້", f"฿{filtered['total_sales'].sum():,.0f}")
    st.dataframe(filtered.sort_values('id', ascending=False), width="stretch")

elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການເມນູສິນຄ້າ")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        n_cat = st.selectbox("ໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ อาหาร"])
        n_p = st.text_input("ຊື່ສິນค้า")
        n_pr = st.number_input("ລາຄາ", min_value=0.0)
        if st.button("💾 Save Product"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), '00:00:00', n_p, n_cat, 0, n_pr, 0))
            conn.commit(); conn.close(); st.rerun()
