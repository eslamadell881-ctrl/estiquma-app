import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import numpy as np
import os

# ==========================================
# 1. Database Setup & ORM (SQLite)
# ==========================================
DB_NAME = "estiqama_v6.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            date TEXT PRIMARY KEY,
            fajr INTEGER, dhuhr INTEGER, asr INTEGER, maghrib INTEGER, isha INTEGER,
            rawatib INTEGER, duha INTEGER, qiyam INTEGER,
            quran INTEGER, azkar_m INTEGER, azkar_e INTEGER, azkar_s INTEGER,
            gaze INTEGER, tongue INTEGER, tawba INTEGER,
            total_score INTEGER, percentage REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_log(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    columns = ', '.join(data.keys())
    placeholders = ':'+', :'.join(data.keys())
    query = f'INSERT OR REPLACE INTO daily_logs ({columns}) VALUES ({placeholders})'
    c.execute(query, data)
    conn.commit()
    conn.close()

def get_all_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM daily_logs ORDER BY date ASC", conn)
    conn.close()
    return df

# ==========================================
# 2. Scoring Engine
# ==========================================
def calculate_score(data):
    prayer_score = data['fajr'] + data['dhuhr'] + data['asr'] + data['maghrib'] + data['isha']
    nawafil_score = (data['rawatib'] + data['duha'] + data['qiyam']) * 2
    azkar_score = (data['quran'] + data['azkar_m'] + data['azkar_e'] + data['azkar_s']) * 2
    tazkiyah_score = (data['gaze'] + data['tongue'] + data['tawba']) * 2
    
    total = prayer_score + nawafil_score + azkar_score + tazkiyah_score
    max_total = 25 + 6 + 8 + 6 # 45 points
    return total, round((total / max_total) * 100, 1)

# ==========================================
# 3. Smart Alerts
# ==========================================
def generate_alerts(df):
    if len(df) < 3:
        return "ℹ️ سجل بيانات 3 أيام على الأقل ليبدأ النظام في تحليل مسارك وتحذيرك."
    
    recent_avg = df['percentage'].tail(3).mean()
    previous_avg = df['percentage'].iloc[-6:-3].mean() if len(df) >= 6 else df['percentage'].head(len(df)-3).mean()
    
    alert_html = ""
    if recent_avg < previous_avg - 5:
        alert_html += f"⚠️ <b>تحذير مسار:</b> معدلك في آخر 3 أيام ({recent_avg:.1f}%) أقل من معدلك السابق. استعن بالله ولا تعجز!<br>"
    elif recent_avg > previous_avg + 5:
        alert_html += f"🚀 <b>تقدم ممتاز:</b> معدلك يرتفع! حافظ على هذا الزخم.<br>"
    
    recent_fajr = df['fajr'].tail(3).values
    if (recent_fajr < 5).all():
        alert_html += "🔴 <b>تنبيه دقيق:</b> لم تصلِ الفجر في المسجد لـ 3 أيام متتالية. اضبط المنبه اليوم!<br>"
        
    return alert_html if alert_html else "✅ مسارك مستقر. استمر على طاعة الله."

# ==========================================
# 4. App UI & Logic
# ==========================================
st.set_page_config(page_title="نظام استقامة", page_icon="🕌", layout="wide")
init_db()

st.sidebar.title("🧭 القائمة")
tab = st.sidebar.radio("اختر الصفحة:", ["📝 تسجيل اليوم", "📈 تحليل المسار (Flowchart)", "⚙️ الإعدادات والأمان"])

if tab == "📝 تسجيل اليوم":
    st.title("تسجيل العبادات اليومية")
    entry_date = st.date_input("تاريخ اليوم", date.today())
    
    st.markdown("### 🕌 الصلوات الخمس (الفرائض)")
    c1, c2, c3, c4, c5 = st.columns(5)
    options = {"المسجد (5)": 5, "أول الوقت (3)": 3, "آخر الوقت (1)": 1, "لم تصل (0)": 0}
    
    def prayer_sel(label, col):
        val = col.selectbox(label, options.keys())
        return options[val]

    fajr = prayer_sel("الفجر", c1)
    dhuhr = prayer_sel("الظهر", c2)
    asr = prayer_sel("العصر", c3)
    maghrib = prayer_sel("المغرب", c4)
    isha = prayer_sel("العشاء", c5)

    st.markdown("### 📿 السنن والنوافل والأذكار (نقطتان)")
    col_a, col_b, col_c = st.columns(3)
    rawatib = col_a.checkbox("السنن الرواتب")
    duha = col_a.checkbox("صلاة الضحى")
    qiyam = col_b.checkbox("قيام الليل")
    quran = col_b.checkbox("ورد القرآن")
    azkar_m = col_c.checkbox("أذكار الصباح")
    azkar_e = col_c.checkbox("أذكار المساء")
    azkar_s = col_c.checkbox("أذكار النوم")

    st.markdown("### 🛡️ تزكية النفس (نقطتان)")
    c_t1, c_t2, c_t3 = st.columns(3)
    gaze = c_t1.checkbox("غض البصر")
    tongue = c_t2.checkbox("حفظ اللسان")
    tawba = c_t3.checkbox("توبة فورية")

    if st.button("حفظ السجل 💾", use_container_width=True):
        raw_data = {
            'date': str(entry_date), 'fajr': fajr, 'dhuhr': dhuhr, 'asr': asr, 'maghrib': maghrib, 'isha': isha,
            'rawatib': int(rawatib), 'duha': int(duha), 'qiyam': int(qiyam),
            'quran': int(quran), 'azkar_m': int(azkar_m), 'azkar_e': int(azkar_e), 'azkar_s': int(azkar_s),
            'gaze': int(gaze), 'tongue': int(tongue), 'tawba': int(tawba)
        }
        total, pct = calculate_score(raw_data)
        raw_data['total_score'] = total
        raw_data['percentage'] = pct
        
        save_log(raw_data)
        st.success(f"تم الحفظ بنجاح! نسبة إنجازك: {pct}%")

elif tab == "📈 تحليل المسار (Flowchart)":
    st.title("تحليل مسار الاستقامة")
    df = get_all_data()
    
    if df.empty:
        st.info("لا توجد بيانات مسجلة بعد.")
    else:
        st.markdown("### 🔔 الموجه الذكي (Smart Alerts)")
        st.info(generate_alerts(df))
        
        st.markdown("### 📊 المعدل الزمني (التريند)")
        df['Moving_Average'] = df['percentage'].rolling(window=3).mean()
        chart_data = df.set_index('date')[['percentage', 'Moving_Average']]
        st.line_chart(chart_data, color=["#3498DB", "#E74C3C"])
        
        st.markdown("### 📋 سجل البيانات")
        st.dataframe(df[['date', 'percentage', 'total_score', 'fajr', 'quran', 'gaze']], use_container_width=True)

elif tab == "⚙️ الإعدادات والأمان":
    st.title("بيئة الاختبار وحماية البيانات")
    
    st.markdown("### 💾 حماية بياناتك (Backup & Restore)")
    st.info("السيرفر المجاني قد يقوم بمسح قاعدة البيانات أحياناً. قم بتحميل نسخة احتياطية أسبوعياً من هنا.")
    
    # Download Backup
    if os.path.exists(DB_NAME):
        with open(DB_NAME, "rb") as f:
            st.download_button("⬇️ تحميل قاعدة البيانات (Backup)", f, file_name="estiqama_backup.db")
    
    # Upload Backup
    uploaded_file = st.file_uploader("⬆️ استرجاع قاعدة البيانات", type=['db'])
    if uploaded_file is not None:
        if st.button("تأكيد الاسترجاع (سيتم استبدال الداتا الحالية)"):
            with open(DB_NAME, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("تم استرجاع البيانات بنجاح! قم بتحديث الصفحة.")

    st.divider()
    st.markdown("### 🧪 Testing & Automation (للمستثمرين والمطورين)")
    
    if st.button("▶️ تشغيل فحص النظام (Run Unit Tests)"):
        with st.spinner('جاري فحص النظام...'):
            mock_data = {'fajr': 5, 'dhuhr': 5, 'asr': 5, 'maghrib': 5, 'isha': 5, 
                         'rawatib': 1, 'duha': 1, 'qiyam': 1, 'quran': 1, 'azkar_m': 1, 
                         'azkar_e': 1, 'azkar_s': 1, 'gaze': 1, 'tongue': 1, 'tawba': 1}
            tot, pct = calculate_score(mock_data)
            if tot == 45 and pct == 100.0:
                st.success("✅ Test 1 Passed: Scoring Engine works correctly.")
            else:
                st.error("❌ Test 1 Failed.")
                
    if st.button("💉 حقن بيانات اختبار (Inject 10 Days)"):
        for i in range(10):
            d = str(date.today() - timedelta(days=10-i))
            mock_log = {
                'date': d, 'fajr': np.random.choice([5, 3, 1, 0]), 'dhuhr': 5, 'asr': 5, 'maghrib': 5, 'isha': np.random.choice([5, 3]),
                'rawatib': 1, 'duha': 0, 'qiyam': 0, 'quran': 1, 'azkar_m': 1, 'azkar_e': 1, 'azkar_s': 1,
                'gaze': 1, 'tongue': 1, 'tawba': 0
            }
            tot, pct = calculate_score(mock_log)
            mock_log['total_score'], mock_log['percentage'] = tot, pct
            save_log(mock_log)
        st.success("تم حقن البيانات! اذهب لصفحة (تحليل المسار) لرؤية المخطط.")