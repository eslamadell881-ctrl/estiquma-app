import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
from datetime import date
import re
import hashlib
import os
import binascii

# ==========================================
# 1. إعدادات الصفحة والواجهة الروحية المحترفة
# ==========================================
st.set_page_config(page_title="نظام استقامة - واحة الطاعات والإيمان", page_icon="🕋", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0d1117 !important; color: #e6edf3 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3, h4 { color: #f0b429 !important; font-weight: 700 !important; }
    p, label, span, .stMarkdown { color: #c9d1d9 !important; }
    
    .spiritual-card {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    input, textarea, select, div[data-baseweb="select"] > div { 
        background-color: #0d1117 !important; 
        color: #e6edf3 !important; 
        border: 1px solid #30363d !important; 
        border-radius: 8px !important; 
    }
    
    .stButton>button { 
        background-color: #238636 !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        border: none !important; 
        font-weight: bold !important; 
        padding: 10px 24px; 
    }
    .stButton>button:hover { background-color: #2ea043 !important; }
    
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #e6edf3 !important; }
    hr { border-color: #30363d !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. دوال تشفير والتحقق من كلمات المرور (أمان عالي)
# ==========================================
def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(salt).decode('ascii') + ':' + binascii.hexlify(pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    try:
        salt_str, stored_pwdhash = stored_password.split(':')
        salt = binascii.unhexlify(salt_str.encode('ascii'))
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return stored_pwdhash == binascii.hexlify(pwdhash).decode('ascii')
    except:
        return False

@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None

# ==========================================
# 3. شاشة الدخول والتسجيل الآمنة
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🕋 نظام استقامة</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b949e;'>\"وَالَّذِينَ جَاهَدُوا فِينَا لَنَهْدِيَنَّهُمْ سُبُلَنَا\"</p>", unsafe_allow_html=True)
        
        mode = st.radio("اختر العملية", ["تسجيل الدخول", "إنشاء حساب جديد"], horizontal=True)
        
        if mode == "تسجيل الدخول":
            with st.form("login_form"):
                mobile = st.text_input("رقم الموبايل")
                password = st.text_input("كلمة المرور", type="password")
                submit_login = st.form_submit_button("دخول إلى واحة الطاعات", use_container_width=True)
                
                if submit_login:
                    if not mobile or not password:
                        st.warning("يرجى إدخال رقم الموبايل وكلمة المرور.")
                    else:
                        try:
                            res = supabase.table('istiqama_users').select('*').eq('mobile', mobile).execute()
                            if res.data:
                                user = res.data[0]
                                if verify_password(user['password'], password):
                                    st.session_state.logged_in = True
                                    st.session_state.user_id = user['id']
                                    st.session_state.user_name = user['name']
                                    st.rerun()
                                else:
                                    st.error("رقم الموبايل أو كلمة المرور غير صحيحة.")
                            else:
                                st.error("رقم الموبايل غير مسجل.")
                        except Exception as err:
                            st.error(f"حدث خطأ في النظام: {err}")
        else:
            with st.form("reg_form"):
                name = st.text_input("الاسم الكريم")
                mobile = st.text_input("رقم الموبايل")
                password = st.text_input("كلمة المرور (8 أحرف على الأقل، وتحوي حروفاً وأرقاماً)", type="password")
                submit_reg = st.form_submit_button("تسجيل حساب جديد", use_container_width=True)
                
                if submit_reg:
                    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
                        st.error("كلمة المرور ضعيفة! يجب أن تكون 8 أحرف على الأقل وتحتوي على حروف وأرقام.")
                    elif not name or not mobile:
                        st.warning("يرجى إدخال الاسم ورقم الموبايل.")
                    else:
                        try:
                            hashed_pwd = hash_password(password)
                            supabase.table('istiqama_users').insert({
                                'name': name,
                                'mobile': mobile,
                                'password': hashed_pwd
                            }).execute()
                            st.success("✅ تم إنشاء الحساب بنجاح وبأمان تام! انتقل لتبويب 'تسجيل الدخول'.")
                        except Exception as e:
                            st.error("رقم الموبايل مسجل مسبقاً.")
    st.stop()

# ==========================================
# 4. الواجهة الرئيسية بعد تسجيل الدخول
# ==========================================
user_name = st.session_state.user_name
user_id = st.session_state.user_id

with st.sidebar:
    st.markdown("### 🌙 رفيق الدرب")
    st.markdown(f"**أهلاً بك يا {user_name}** 🤲")
    st.markdown("---")
    st.markdown("✨ *\"إن الله يحب إذا عمل أحدكم عملاً أن يتقنه\"*")
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.markdown(f"<h1>🕋 لوحة محاسبة النفس والطاعات - ازيك يا {user_name}</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>سجل وردك اليومي ومحاسبتك بإخلاص وتجرد. الأيام الفائتة مقفلة للأرشفة والمحاسبة.</p>", unsafe_allow_html=True)

today = date.today()

tab_today, tab_history = st.tabs(["📅 ورد اليوم الحالي ومحاسبة النفس", "📈 الأرشيف والرسوم البيانية الروحية"])

prayer_options = [
    'لم تُسجل',
    'صلاة في المسجد (3 نقاط)',
    'صلاة في البيت أول الأذان (نقطة)',
    'صلاة في آخر الوقت (نقطة)',
    'فائتة / لم تُصلى (0 نقاط)'
]

def get_prayer_score(status_str):
    if 'المسجد' in status_str:
        return 3
    elif 'أول الأذان' in status_str or 'آخر الوقت' in status_str:
        return 1
    return 0

with tab_today:
    st.markdown(f"### سجل عبادات تاريخ اليوم: **{today}**")
    
    try:
        existing_log = supabase.table('istiqama_logs').select('*').eq('user_id', user_id).eq('log_date', str(today)).execute()
        log_data = existing_log.data[0] if existing_log.data else None
    except:
        log_data = None

    with st.form("daily_worship_form"):
        # 1. الصلوات
        st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
        st.markdown("#### 🕌 الصلوات الخمس")
        def get_index(val):
            try: return prayer_options.index(val)
            except: return 0

        p_fajr = st.selectbox("صلاة الفجر", prayer_options, index=get_index(log_data['fajr_status']) if log_data else 0)
        p_dhuhr = st.selectbox("صلاة الظهر", prayer_options, index=get_index(log_data['dhuhr_status']) if log_data else 0)
        p_asr = st.selectbox("صلاة العصر", prayer_options, index=get_index(log_data['asr_status']) if log_data else 0)
        p_maghrib = st.selectbox("صلاة المغرب", prayer_options, index=get_index(log_data['maghrib_status']) if log_data else 0)
        p_isha = st.selectbox("صلاة العشاء", prayer_options, index=get_index(log_data['isha_status']) if log_data else 0)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. القرآن
        st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
        st.markdown("#### 📖 الورد القرآني (الحفظ والقراءة)")
        h_done = st.checkbox("📖 هل أتممت ورد حفظ اليوم؟", value=log_data['hifz_done'] if log_data else False)
        
        col_h1, col_h2 = st.columns(2)
        hifz_j = col_h1.number_input("رقم الجزء المحفوظ", min_value=1, max_value=30, value=log_data['hifz_juz'] if log_data else 1)
        hifz_p = col_h2.number_input("رقم الصفحة المحفوظة", min_value=1, max_value=604, value=log_data['hifz_page'] if log_data else 1)
        
        read_pages = st.number_input("📚 عدد صفحات ورد القراءة اليومية (كل صفحة بنقطة)", min_value=0, max_value=100, value=log_data['read_pages_count'] if log_data else 0)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. الأذكار والقيام
        st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
        st.markdown("#### 📿 الأذكار والقيام")
        c_a1, c_a2 = st.columns(2)
        adhkar_s = c_a1.checkbox("☀️ أذكار الصباح والمساء", value=log_data['adhkar_sabah_masaa'] if log_data else False)
        adhkar_p = c_a2.checkbox("🕌 أذكار بعد الصلوات", value=log_data['adhkar_after_prayer'] if log_data else False)
        
        c_a3, c_a4 = st.columns(2)
        adhkar_sl = c_a3.checkbox("🌙 أذكار النوم", value=log_data['adhkar_sleep'] if log_data else False)
        qiyam = c_a4.checkbox("⭐ قيام الليل", value=log_data['qiyam_al_layl'] if log_data else False)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 4. محاسبة النفس
        st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
        st.markdown("#### 🛡️ محاسبة النفس والجهاد (الشهوات والتوبة)")
        st.markdown("<p style='color: #f0b429; font-size: 13px;'>الصدق مع النفس هو أساس الترقي الروحي.</p>", unsafe_allow_html=True)
        
        had_desire = st.checkbox("⚠️ هل حدث ضعف أو وقوع في شهوة اليوم؟", value=log_data['had_desire_struggle'] if log_data else False)
        returned = st.checkbox("🤲 هل تبت ورجعت إلى الله سريعاً؟", value=log_data['returned_to_allah'] if log_data else False)
        tawba_txt = st.text_area("خواطر وتزكية النفس اليومية", value=log_data['tawba_notes'] if log_data else "")
        st.markdown('</div>', unsafe_allow_html=True)
        
        submit_log = st.form_submit_button("💾 حفظ ورد اليوم في سجل الطاعات", use_container_width=True)
        
        if submit_log:
            try:
                p_pts = (get_prayer_score(p_fajr) + get_prayer_score(p_dhuhr) + 
                         get_prayer_score(p_asr) + get_prayer_score(p_maghrib) + 
                         get_prayer_score(p_isha))
                r_pts = int(read_pages)
                
                adhkar_pts = 0
                if adhkar_s: adhkar_pts += 5
                if adhkar_p: adhkar_pts += 5
                if adhkar_sl: adhkar_pts += 5
                if qiyam: adhkar_pts += 5
                
                struggle_pts = 0
                if had_desire: struggle_pts -= 50
                if returned: struggle_pts += 100
                
                total_pts = p_pts + r_pts + adhkar_pts + struggle_pts
                
                payload = {
                    'user_id': user_id,
                    'log_date': str(today),
                    'fajr_status': p_fajr,
                    'dhuhr_status': p_dhuhr,
                    'asr_status': p_asr,
                    'maghrib_status': p_maghrib,
                    'isha_status': p_isha,
                    'prayer_points': p_pts,
                    'hifz_done': h_done,
                    'hifz_juz': hifz_j,
                    'hifz_page': hifz_p,
                    'read_pages_count': read_pages,
                    'read_points': r_pts,
                    'adhkar_sabah_masaa': adhkar_s,
                    'adhkar_after_prayer': adhkar_p,
                    'adhkar_sleep': adhkar_sl,
                    'qiyam_al_layl': qiyam,
                    'adhkar_qiyam_points': adhkar_pts,
                    'had_desire_struggle': had_desire,
                    'returned_to_allah': returned,
                    'struggle_points': struggle_pts,
                    'total_daily_points': total_pts,
                    'tawba_notes': tawba_txt
                }
                
                if log_data:
                    supabase.table('istiqama_logs').update(payload).eq('id', log_data['id']).execute()
                    st.success("✅ تم تحديث ورد اليوم بنجاح في صحيفة أعمالك.")
                else:
                    supabase.table('istiqama_logs').insert(payload).execute()
                    st.success("🎉 تقبل الله طاعاتك وجاهد نفسك! تم حفظ السجل بنجاح.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")

with tab_history:
    st.markdown("### 📊 الأرشيف والرسوم البيانية الروحية (مقفل ومحفوظ للأرشفة)")
    st.markdown("<p style='color: #8b949e;'>تأمل مسيرتك الإيمانية عبر الرسوم البيانية الدائرية وشريطية الأداء دون الالتفات للأرقام الحرفية.</p>", unsafe_allow_html=True)
    
    try:
        # جلب سجلات المستخدم الحالي فقط (عزل تام للبيانات)
        history_res = supabase.table('istiqama_logs').select('*').eq('user_id', user_id).order('log_date', desc=True).execute()
        if history_res.data:
            df_hist = pd.DataFrame(history_res.data)
            
            c_g1, c_g2 = st.columns(2)
            
            with c_g1:
                st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
                st.markdown("#### 🥧 توزيع الطاعات والأنشطة الإيمانية")
                sum_prayers = df_hist['prayer_points'].sum()
                sum_quran = df_hist['read_points'].sum()
                sum_adhkar = df_hist['adhkar_qiyam_points'].sum()
                
                pie_df = pd.DataFrame({
                    'العبادة': ['الصلوات', 'ورد القراءة', 'الأذكار والقيام'],
                    'النسبة': [max(0, sum_prayers), max(0, sum_quran), max(0, sum_adhkar)]
                })
                
                fig_pie = px.pie(pie_df, names='العبادة', values='النسبة', hole=0.4, color_discrete_sequence=['#238636', '#f0b429', '#1f6feb'])
                fig_pie.update_layout(paper_bgcolor='#161b22', font_color='#e6edf3', margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with c_g2:
                st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
                st.markdown("#### 📈 مؤشر الالتزام والاستمرارية الروحي")
                fig_line = px.line(df_hist, x='log_date', y='total_daily_points', markers=True, line_shape='spline', color_discrete_sequence=['#f0b429'])
                fig_line.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font_color='#e6edf3', margin=dict(t=10, b=10, l=10, r=10))
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="spiritual-card">', unsafe_allow_html=True)
            st.markdown("#### 🗂️ سجل الأيام السابقة (أرشيف الطاعات والتوبة)")
            st.dataframe(df_hist[['log_date', 'fajr_status', 'dhuhr_status', 'asr_status', 'maghrib_status', 'isha_status', 'hifz_done', 'read_pages_count', 'tawba_notes']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            st.info("لا توجد سجلات سابقة في الأرشيف حتى الآن. ابدأ بتسجيل طاعات اليوم.")
    except Exception as ex:
        st.error(f"خطأ في جلب الأرشيف والرسوم البيانية: {ex}")
