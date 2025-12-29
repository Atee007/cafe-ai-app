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
    if st.session_state['role'] == 'admin':
        menu = st.radio("Menu", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("Menu", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    
    if st.button("🚪 Logout"): st.session_state.clear(); st.rerun()

# --- 4. Dashboard (ສະບັບປັບປຸງ: ແຈ້ງເຕືອນພ້ອມໂຊ % ຄວາມແຕກຕ່າງ) ---
if menu == "📊 Dashboard":
    st.header("📊 Dashboard ພາບລວມ")
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    avg_daily = sales_30d / 30 if sales_30d > 0 else 0
    
    # 🔔 [Automation] ແຈ້ງເຕືອນພ້ອມຄຳນວນ %
    if avg_daily > 0:
        diff_from_avg = ((today_sales - avg_daily) / avg_daily) * 100
        
        if today_sales < avg_daily:
            # ຖ້າຍອດຕ່ຳກວ່າຄ່າສະເລ່ຍ
            st.warning(f"⚠️ **ແຈ້ງເຕືອນ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ຕ່ຳກວ່າ** ຄ່າສະເລ່ຍຢູ່ {abs(diff_from_avg):.1f}% (ຄ່າສະເລ່ຍ: ฿{avg_daily:,.0f})")
        elif today_sales > avg_daily:
            # ຖ້າຍອດສູງກວ່າຄ່າສະເລ່ຍ
            st.success(f"🎉 **ຂ່າວດີ:** ຍອດຂາຍມື້ນີ້ (฿{today_sales:,.0f}) **ສູງກວ່າ** ຄ່າສະເລ່ຍເຖິງ {diff_percent:.1f}%!")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ບິນມື້ນີ້", f"{len(df[df['transaction_date'] == today])}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{sales_30d:,.0f}")
    c4.metric("ສະເລ່ຍ/ວັນ", f"฿{avg_daily:,.0f}")

    st.divider()
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🏆 ຂາຍດີ 30 ວັນ")
        st.bar_chart(df.groupby('product_detail')['transaction_qty'].sum().nlargest(5))
    with col_r:
        st.subheader("🕒 ລາຍການຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(10), use_container_width=True)

# --- 5. ບັນທຶກການຂາຍ ---
elif menu == "📝 ບັນທຶກການຂາຍ":
    st.header("🛒 ບັນທຶກການຂາຍ")
    cat_filter = st.selectbox("📂 ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
    all_prods = df[['product_detail', 'product_category', 'unit_price']].drop_duplicates('product_detail')
    filtered_prods = all_prods[all_prods['product_category'] == cat_filter]
    
    if filtered_prods.empty:
        st.warning(f"⚠️ ຍັງບໍ່ມີສິນຄ້າໃນໝວດ {cat_filter}")
    else:
        p_name = st.selectbox(f"🛍️ ເລືອກສິນຄ້າ ({cat_filter})", filtered_prods['product_detail'])
        u_price = float(filtered_prods[filtered_prods['product_detail'] == p_name]['unit_price'].values[0])
        qty = st.number_input("ຈຳນວນຊິ້ນ", min_value=1, step=1, value=1)
        total_bill = qty * u_price
        
        st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #ff4b4b;">
            <h4 style="margin:0;">💰 ລາຄາຕໍ່ໜ່ວຍ: {u_price:,.2f} ฿</h4>
            <h2 style="margin:10px 0; color:#ff4b4b;">💵 ຍອດລວມທີ່ຕ້ອງເກັບ: {total_bill:,.2f} ฿</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ ຢືນຢັນການຂາຍ", use_container_width=True, type="primary"):
            conn = sqlite3.connect(DB_NAME)
            conn.execute("""INSERT INTO sales (transaction_date, transaction_time, product_detail, 
                            product_category, transaction_qty, unit_price, total_sales) 
                            VALUES (?,?,?,?,?,?,?)""",
                         (pd.Timestamp.now().strftime('%Y-%m-%d'), pd.Timestamp.now().strftime('%H:%M:%S'), 
                          p_name, cat_filter, qty, u_price, total_bill))
            conn.commit(); conn.close()
            st.success("🎉 ບັນທຶກສຳເລັດ!"); st.balloons(); st.rerun()

# --- 6. ປະຫວັດການຂາຍ ---
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

# --- 7. ຈັດການສິນຄ້າ ---
elif menu == "☕ ຈັດການສິນຄ້າ":
    st.header("☕ ຈັດການເມນູສິນຄ້າ")
    with st.expander("➕ ເພີ່ມສິນຄ້າໃໝ່"):
        new_cat = st.selectbox("ເລືອກໝວດໝູ່", ["☕ ເຄື່ອງດື່ມ", "🍰 ເບເກີລີ້", "🍽️ ອາຫານ"])
        new_p = st.text_input("ຊື່ສິນຄ້າ")
        new_price = st.number_input("ລາຄາຕໍ່ໜ່ວຍ", min_value=0.0)
        if st.button("💾 ບັນທຶກ"):
            if new_p:
                conn = sqlite3.connect(DB_NAME)
                conn.execute("INSERT INTO sales (transaction_date, transaction_time, product_detail, product_category, transaction_qty, unit_price, total_sales) VALUES (?,?,?,?,?,?,?)",
                             (pd.Timestamp.now().strftime('%Y-%m-%d'), '00:00:00', new_p, new_cat, 0, new_price, 0))
                conn.commit(); conn.close(); st.success("ເພີ່ມສຳເລັດ!"); st.rerun()

# --- 8. AI Forecasting (ເພີ່ມ Automation ແຈ້ງເຕືອນແນວໂນ້ມ AI) ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.header("🔮 ວິເຄາະແນວໂນ້ມ ແລະ ຄາດຄະເນຍອດຂາຍ")
    daily_sales = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
    
    if len(daily_sales) < 7:
        st.warning("⚠️ ຂໍ້ມູນຍັງບໍ່ພໍສຳລັບການວິເຄາະແນວໂນ້ມ (ຕ້ອງການຂໍ້ມູນຢ່າງໜ້ອຍ 7 ວັນ)")
    else:
        avg_past_7 = daily_sales['total_sales'].tail(7).mean()
        hist = list(daily_sales['total_sales'].tail(7))
        forecast_values = []
        last_date = pd.to_datetime(daily_sales['transaction_date'].max())
        
        for i in range(1, 8):
            f_date = pd.Timestamp(last_date + timedelta(days=i))
            inp = pd.DataFrame([{'day_of_week': f_date.dayofweek, 'month': f_date.month, 'is_weekend': 1 if f_date.dayofweek >= 5 else 0, 'sales_lag1': hist[-1], 'sales_lag7': hist[0], 'rolling_mean_7': np.mean(hist)}])
            pred = model.predict(inp[features_list])[0]
            forecast_values.append(pred); hist.append(pred); hist.pop(0)
            
        avg_future_7 = np.mean(forecast_values)
        diff_percent = ((avg_future_7 - avg_past_7) / avg_past_7) * 100
        trend_label = "ເພີ່ມຂຶ້ນ 📈" if diff_percent > 0 else "ຫຼຸດລົງ 📉"

        # 🔔 [Automation] ແຈ້ງເຕືອນແນວໂນ້ມຈາກ AI
        if diff_percent < -5:
            st.error(f"🚨 **AI ເຕືອນ:** ແນວໂນ້ມ 7 ວັນຂ້າງໜ້າຈະຫຼຸດລົງ {abs(diff_percent):.1f}%. ລອງຫາແນວທາງກະຕຸ້ນຍອດຂາຍ!")
        elif diff_percent > 5:
            st.info(f"📈 **AI ວິເຄາະ:** ຍອດຂາຍມີແນວໂນ້ມຈະເພີ່ມຂຶ້ນ {diff_percent:.1f}%!")

        st.markdown("### 📊 ສຫຼຸບການວິເຄາະແນວໂນ້ມ")
        col1, col2, col3 = st.columns(3)
        col1.metric("ສະເລ່ຍ 7 ວັນຜ່ານມາ", f"฿{avg_past_7:,.2f}")
        col2.metric("ສະເລ່ຍ 7 ວັນຂ້າງໜ້າ (AI)", f"฿{avg_future_7:,.2f}", delta=f"{diff_percent:.1f}% {trend_label}")
        col3.metric("ແນວໂນ້ມການຂາຍ", trend_label)

        st.divider()
        f_df = pd.DataFrame({'ວັນທີ': [(last_date + timedelta(days=i)).date() for i in range(1, 8)], 'ຍອດຄາດຄະເນ (฿)': [round(v, 2) for v in forecast_values]})
        st.subheader("📅 ເສັ້ນສະແດງການຄາດຄະເນ 7 ວັນລ່ວງໜ້າ")
        fig = px.line(f_df, x='ວັນທີ', y='ຍອດຄາດຄະເນ (฿)', markers=True, text='ຍອດຄາດຄະເນ (฿)', title="ແນວໂນ້ມຍອດຂາຍໃນອະນາຄົດ")
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)
        st.table(f_df)
