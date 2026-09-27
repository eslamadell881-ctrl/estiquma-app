import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date
import re

# ==========================================
# إعدادات الواجهة الفاتحة النظيفة (بدون لون أسود)
# ==========================================
st.set_page_config(page_title="نظام استقامة - متابعة العبادات", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc !important; color: #0f172a !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3, h4 { color: #1e3a8a !important; font-weight: 700 !important; }
    p, label, span { color: #334155 !important; }
    input, textarea, select { 
        background-color: #ffffff !important; 
        color: #0f172a !important; 
        border: 1px solid #cbd5e1 !important; 
        border-radius: 8px !important; 
    }
    .stButton>button { 
        background-color: #16a34a !important; 
        color: #ffffff !important; 
        border-radius: 8px !important; 
        border: none !important; 
        font-weight: bold !important; 
        padding: 10px 24px; 
    }
    .stButton>button:hover { background-color: #15803d !important; }
    [data-testid="stSidebar"] { background-color: #f1f5f9 !important; border-right: 1px solid #e2e8f0; }
    hr { border-color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

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
# نظام الدخول والتسجيل
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🌙 نظام استقامة</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>رفيقك اليومي لتتبع العبادات ومحاسبة النفس</p>", unsafe_allow_html=True)
        
        mode = st.radio("اختر العملية", ["تسجيل الدخول", "إنشاء حساب جديد"], horizontal=True)
        
        if mode == "تسجيل الدخول":
            with st.form("login_form"):
                mobile = st.text_input("رقم الموبايل")
                password = st.text_input("كلمة المرور", type="password")
                submit_login = st.form_submit_button("دخول", use_container_width=True)
                
                if submit_login:
                    try:
                        res = supabase.table('istiqama_users').select('*').eq('mobile', mobile).eq('password', password).execute()
                        if res.data:
                            user = res.data[0]
                            st.session_state.logged_in = True
                            st.session_state.user_id = user['id']
                            st.session_state.user_name = user['name']
                            st.rerun()
                        else:
                            st.error("رقم الموبايل أو كلمة المرور غير صحيحة.")
                    except Exception as err:
                        st.error(f"خطأ: {err}")
        else:
            with st.form("reg_form"):
                name = st.text_input("الاسم الكامل")
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
                            supabase.table('istiqama_users').insert({
                                'name': name,
                                'mobile': mobile,
                                'password': password
                            }).execute()
                            st.success("✅ تم إنشاء الحساب بنجاح! انتقل لتبويب 'تسجيل الدخول'.")
                        except Exception as e:
                            st.error("رقم الموبايل مسجل مسبقاً أو حدث خطأ.")
    st.stop()

# ==========================================
# الواجهة الرئيسية بعد تسجيل الدخول
# ==========================================
user_name = st.session_state.user_name
user_id = st.session_state.user_id

with st.sidebar:
    st.markdown(f"### 🌙 أهلاً بك")
    st.markdown(f"**ازيك يا {user_name}** 😊")
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.markdown(f"<h1>🌙 لوحة متابعة العبادات - ازيك يا {user_name}</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b;'>سجل وردك اليومي ومحاسبتك بدقة. الأيام الفائتة مقفلة للأرشفة فقط.</p>", unsafe_allow_html=True)

today = date.today()

tab_today, tab_history = st.tabs(["📅 ورد اليوم الحالي (متاح للتسجيل)", "📈 الأرشيف والسجل السابق (عرض فقط)"])

prayer_options = [
    'لم تُسجل',
    'صلاة في المسجد (3 نقاط)',
    'صلاة في البيت أول الأذان (نقطة)',
    'صلاة في آخر الوقت (نقطة)',
    'فائتة / لم تُصلى (0 نقاط)'
]

def calculate_prayer_score(status_str):
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
        st.markdown("#### 🕌 نظام تقييم الصلوات الخمس")
        
        def get_index(val):
            try:
                return prayer_options.index(val)
            except:
                return 0

        p_fajr = st.selectbox("صلاة الفجر", prayer_options, index=get_index(log_data['fajr_status']) if log_data else 0)
        p_dhuhr = st.selectbox("صلاة الظهر", prayer_options, index=get_index(log_data['dhuhr_status']) if log_data else 0)
        p_asr = st.selectbox("صلاة العصر", prayer_options, index=get_index(log_data['asr_status']) if log_data else 0)
        p_maghrib = st.selectbox("صلاة المغرب", prayer_options, index=get_index(log_data['maghrib_status']) if log_data else 0)
        p_isha = st.selectbox("صلاة العشاء", prayer_options, index=get_index(log_data['isha_status']) if log_data else 0)
        
        st.markdown("---")
        st.markdown("#### 📖 الورد القرآني المنظم")
        col_h1, col_h2 = st.columns(2)
        hifz_j = col_h1.number_input("ورد الحفظ - رقم الجزء", min_value=1, max_value=30, value=log_data['hifz_juz'] if log_data else 1)
        hifz_p = col_h2.number_input("ورد الحفظ - رقم الصفحة", min_value=1, max_value=604, value=log_data['hifz_page'] if log_data else 1)
        
        col_r1, col_r2 = st.columns(2)
        read_from = col_r1.number_input("ورد القراءة - من صفحة", min_value=1, max_value=604, value=log_data['read_from_page'] if log_data else 1)
        read_to = col_r2.number_input("ورد القراءة - إلى صفحة", min_value=1, max_value=604, value=log_data['read_to_page'] if log_data else 1)
        
        st.markdown("---")
        st.markdown("#### 📿 الأذكار والقيام")
        c_a1, c_a2 = st.columns(2)
        adhkar_s = c_a1.checkbox("أذكار الصباح والمساء", value=log_data['adhkar_sabah_masaa'] if log_data else False)
        adhkar_p = c_a2.checkbox("أذكار بعد الصلاة", value=log_data['adhkar_after_prayer'] if log_data else False)
        
        c_a3, c_a4 = st.columns(2)
        adhkar_sl = c_a3.checkbox("أذكار النوم", value=log_data['adhkar_sleep'] if log_data else False)
        qiyam = c_a4.checkbox("قيام الليل", value=log_data['qiyam_al_layl'] if log_data else False)
        
        st.markdown("---")
        st.markdown("#### 🛡️ محاسبة النفس والجهاد (الشهوات والتوبة)")
        had_desire = st.checkbox("⚠️ هل حدث ضعف أو وقوع في شهوة اليوم؟", value=log_data['had_desire_struggle'] if log_data else False)
        returned = st.checkbox("🤲 هل تبت ورجعت إلى الله سريعاً؟", value=log_data['returned_to_allah'] if log_data else False)
        tawba_txt = st.text_area("خواطر تزكية النفس وملاحظات اليوم", value=log_data['tawba_notes'] if log_data else "")
        
        submit_log = st.form_submit_button("💾 حفظ ورد اليوم ومحاسبة النفس", use_container_width=True)
        
        if submit_log:
            try:
                total_pts = (calculate_prayer_score(p_fajr) + 
                             calculate_prayer_score(p_dhuhr) + 
                             calculate_prayer_score(p_asr) + 
                             calculate_prayer_score(p_maghrib) + 
                             calculate_prayer_score(p_isha))
                
                payload = {
                    'user_id': user_id,
                    'log_date': str(today),
                    'fajr_status': p_fajr,
                    'dhuhr_status': p_dhuhr,
                    'asr_status': p_asr,
                    'maghrib_status': p_maghrib,
                    'isha_status': p_isha,
                    'total_prayer_points': total_pts,
                    'hifz_juz': hifz_j,
                    'hifz_page': hifz_p,
                    'read_from_page': read_from,
                    'read_to_page': read_to,
                    'adhkar_sabah_masaa': adhkar_s,
                    'adhkar_after_prayer': adhkar_p,
                    'adhkar_sleep': adhkar_sl,
                    'qiyam_al_layl': qiyam,
                    'had_desire_struggle': had_desire,
                    'returned_to_allah': returned,
                    'tawba_notes': tawba_txt
                }
                
                if log_data:
                    supabase.table('istiqama_logs').update(payload).eq('id', log_data['id']).execute()
                    st.success(f"✅ تم تحديث ورد اليوم بنجاح! مجموع نقاط الصلوات: {total_pts} نقطة.")
                else:
                    supabase.table('istiqama_logs').insert(payload).execute()
                    st.success(f"🎉 تقبل الله طاعاتك! تم حفظ السجل. مجموع نقاط الصلوات: {total_pts} نقطة.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")

with tab_history:
    st.markdown("### 📊 الأرشيف والسجل السابق (مقفل - عرض فقط)")
    try:
        history_res = supabase.table('istiqama_logs').select('*').eq('user_id', user_id).order('log_date', desc=True).execute()
        if history_res.data:
            df_hist = pd.DataFrame(history_res.data)
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("لا توجد سجلات سابقة للأرشيف حتى الآن.")
    except Exception as ex:
        st.error(f"خطأ في جلب الأرشيف: {ex}")
