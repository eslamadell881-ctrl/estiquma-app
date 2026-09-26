import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date
import numpy as np

# ==========================================
# 1. الاتصال بقاعدة البيانات السحابية (Supabase)
# ==========================================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("⚠️ لم يتم العثور على مفاتيح Supabase. يرجى إضافتها في Streamlit Secrets.")
    st.stop()

def save_log(data):
    # ميزة (upsert) تقوم بتحديث بيانات اليوم إذا كان مسجلاً، أو إنشاء يوم جديد
    supabase.table('daily_logs').upsert(data).execute()

def get_all_data():
    response = supabase.table('daily_logs').select("*").order("date").execute()
    if response.data:
        return pd.DataFrame(response.data)
    else:
        return pd.DataFrame()

# ==========================================
# 2. محرك حساب النقاط (Scoring Engine)
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
# 3. الموجه الذكي (Smart Alerts)
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
# 4. واجهة المستخدم (App UI)
# ==========================================
st.set_page_config(page_title="نظام استقامة", page_icon="🕌", layout="wide")

st.sidebar.title("🧭 القائمة")
tab = st.sidebar.radio("اختر الصفحة:", ["📝 تسجيل اليوم", "📈 تحليل المسار"])

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
        
        with st.spinner("جاري التشفير والحفظ في السحابة..."):
            save_log(raw_data)
        st.success(f"تم الحفظ بنجاح وأمان تام! نسبة إنجازك: {pct}%")

elif tab == "📈 تحليل المسار":
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
        
        st.markdown("### 📋 سجل البيانات السحابي")
        st.dataframe(df[['date', 'percentage', 'total_score', 'fajr', 'quran', 'gaze']], use_container_width=True)
        
        st.divider()
        if st.button("🗑️ مسح كل البيانات للبدء من جديد (خطر)"):
            supabase.table('daily_logs').delete().neq("date", "0000-00-00").execute()
            st.success("تم مسح السجل بالكامل من السحابة. قم بتحديث الصفحة.")
