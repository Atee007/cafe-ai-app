import streamlit as st
import pandas as pd
import sqlite3
import joblib
import numpy as np
from datetime import timedelta
import plotly.express as px
import os

# --- [ເພີ່ມສ່ວນ CSS ເພື່ອຄວາມທັນສະໄໝ] ---
st.set_page_config(page_title="Cafe AI Pro", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Lao:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto+Sans+Lao', sans-serif; }
    
    /* ປັບແຕ່ງ Card Metrics */
    div[data-testid="stMetricValue"] { font-size: 28px; color: #1e293b; font-weight: bold; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        border: 1px solid #f1f5f9;
    }
    
    /* ປັບແຕ່ງແຖບແຈ້ງເຕືອນໃຫ້ເບິ່ງ Minimal */
    .stAlert { border-radius: 12px; border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 1. ການຕັ້ງຄ່າ Database SQLite (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
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

# --- 2. ລະບົບ Login (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h2 style='text-align: center; color: #4338ca;'>🔐 Login Cafe AI Pro</h2>", unsafe_allow_html=True)
    u, p = st.text_input("Username"), st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if (u == "mycafe" and p == "cafe999") or (u == "staff" and p == "1111"):
            st.session_state['logged_in'], st.session_state['role'] = True, ('admin' if u == "mycafe" else 'staff')
            st.rerun()
        else: st.error("ລະຫັດບໍ່ຖືກຕ້ອງ")
    st.stop()

# --- 3. Sidebar (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
with st.sidebar:
    st.markdown("<h1 style='color: #4338ca;'>☕ Cafe Manager</h1>", unsafe_allow_html=True)
    st.write(f"Status: :blue[{st.session_state['role'].upper()}]")
    if st.session_state['role'] == 'admin':
        menu = st.radio("Menu", ["📊 Dashboard", "📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ", "☕ ຈັດການສິນຄ້າ", "🔮 ຄາດຄະເນ AI"])
    else:
        menu = st.radio("Menu", ["📝 ບັນທຶກການຂາຍ", "📜 ປະຫວັດການຂາຍ"])
    
    if st.button("🚪 Logout", use_container_width=True): st.session_state.clear(); st.rerun()

# --- 4. Dashboard (ປັບ UI ໃໝ່ໃຫ້ Modern) ---
if menu == "📊 Dashboard":
    st.markdown("<h2 style='color: #1e293b;'>📊 ພາບລວມທຸລະກິດ</h2>", unsafe_allow_html=True)
    today = df['transaction_date'].max()
    today_sales = df[df['transaction_date'] == today]['total_sales'].sum()
    sales_30d = df[df['transaction_date'] > (today - timedelta(days=30))]['total_sales'].sum()
    avg_daily = sales_30d / 30 if sales_30d > 0 else 0
    
    # 🔔 [Smart Alert แบบใหม่]
    if avg_daily > 0:
        diff_percent = ((today_sales - avg_daily) / avg_daily) * 100
        if today_sales < avg_daily:
            st.warning(f"💡 **Insight:** ຍອດຂາຍມື້ນີ້ຕ່ຳກວ່າຄ່າສະເລ່ຍ **{abs(diff_percent):.1f}%**. ລອງຈັດໂປຣໂມຊັ່ນຊ່ວງບ່າຍເບິ່ງບໍ່?")
        else:
            st.success(f"🌟 **Insight:** ຍອດຂາຍມື້ນີ້ສູງກວ່າຄ່າສະເລ່ຍ **{diff_percent:.1f}%**! ຮັກສາມາດຕະຖານນີ້ໄວ້ເດີ້.")

    # Display Metrics in Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ຍອດມື້ນີ້", f"฿{today_sales:,.0f}")
    c2.metric("ບິນມື້ນີ້", f"{len(df[df['transaction_date'] == today])}")
    c3.metric("ຍອດລວມ 30 ວັນ", f"฿{sales_30d:,.0f}")
    c4.metric("ສະເລ່ຍ/ວັນ", f"฿{avg_daily:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns([6, 4])
    with col_l:
        st.subheader("🏆 ສິນຄ້າຂາຍດີ (30 ວັນ)")
        top_data = df.groupby('product_detail')['transaction_qty'].sum().nlargest(5).reset_index()
        fig_top = px.bar(top_data, x='transaction_qty', y='product_detail', orientation='h', 
                         color='transaction_qty', color_continuous_scale='Viridis', template='plotly_white')
        fig_top.update_layout(showlegend=False, height=350, margin=dict(t=10, b=10))
        st.plotly_chart(fig_top, use_container_width=True)
    with col_r:
        st.subheader("🕒 10 ລາຍການຫຼ້າສຸດ")
        st.dataframe(df.sort_values('id', ascending=False).head(10)[['product_detail', 'total_sales']], use_container_width=True)

# --- 5. ບັນທຶກການຂາຍ (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
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
        <div style="background-color:#f8fafc; padding:20px; border-radius:15px; border-left: 5px solid #6366f1; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h4 style="margin:0; color:#64748b;">💰 ລາຄາຕໍ່ໜ່ວຍ: {u_price:,.2f} ฿</h4>
            <h2 style="margin:10px 0; color:#4338ca;">💵 ຍອດລວມ: {total_bill:,.2f} ฿</h2>
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

# --- 6. ປະຫວັດການຂາຍ (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
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

# --- 7. ຈັດການສິນຄ້າ (ຄືເກົ່າ ບໍ່ປ່ຽນແປງ) ---
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

# --- 8. AI Forecasting (ປັບກາຟໃຫ້ Premium) ---
elif menu == "🔮 ຄາດຄະເນ AI":
    st.markdown("<h2 style='color: #1e293b;'>🔮 ວິເຄາະ ແລະ ພະຍາກອນ AI</h2>", unsafe_allow_html=True)
    daily_sales = df.groupby(df['transaction_date'].dt.date)['total_sales'].sum().reset_index()
    
    if len(daily_sales) < 7:
        st.warning("⚠️ ຂໍ້ມູນຍັງບໍ່ພໍສຳລັບການວິເຄາະ (ຕ້ອງການຂໍ້ມູນຢ່າງໜ້ອຍ 7 ວັນ)")
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

        # AI Smart Alert
        if diff_percent < -5:
            st.error(f"🚨 **AI Alert:** ແນວໂນ້ມອາທິດໜ້າອາດຫຼຸດລົງ **{abs(diff_percent):.1f}%**. ກຽມແຜນການຕະຫຼາດດ່ວນ!")
        elif diff_percent > 5:
            st.info(f"🚀 **AI Alert:** ແນວໂນ້ມອາທິດໜ້າຈະເພີ່ມຂຶ້ນ **{diff_percent:.1f}%**! ກຽມວັດຖຸດິບໃຫ້ພໍເດີ້.")

        col1, col2, col3 = st.columns(3)
        col1.metric("ສະເລ່ຍ 7 ວັນຜ່ານມາ", f"฿{avg_past_7:,.2f}")
        col2.metric("ສະເລ່ຍ 7 ວັນຂ້າງໜ້າ (AI)", f"฿{avg_future_7:,.2f}", delta=f"{diff_percent:.1f}% {trend_label}")
        col3.metric("ແນວໂນ້ມ", trend_label)

        st.markdown("<br>", unsafe_allow_html=True)
        f_df = pd.DataFrame({'ວັນທີ': [(last_date + timedelta(days=i)).date() for i in range(1, 8)], 'ຍອດຄາດຄະເນ (฿)': [round(v, 2) for v in forecast_values]})
        
        # ปรับแต่งกราฟให้สวยงาม (Modern Line Chart)
        fig = px.line(f_df, x='ວັນທີ', y='ຍອດຄາດຄະເນ (฿)', markers=True, text='ຍອດຄາດຄະເນ (฿)', title="📈 ແນວໂນ້ມຍອດຂາຍ 7 ວັນຂ້າງໜ້າ")
        fig.update_traces(line_color='#6366f1', line_width=4, marker=dict(size=10, color='#4338ca'), textposition="top center")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#f1f5f9'))
        st.plotly_chart(fig, use_container_width=True)
        
        st.table(f_df)
