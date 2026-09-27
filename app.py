import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date
import re

# ==========================================
# إعدادات الواجهة الفاتحة النظيفة (بدون لون أسود)
# ==========================================
st.set_page_config(page_title="نظام استقامة - تتبع العبادات", page_icon="🌙", layout="wide")

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
# شاشة تسجيل الدخول وإنشاء الحساب
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🌙 نظام استقامة</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>رفيقك اليومي لتتبع العبادات والارتقاء الروحي</p>", unsafe_allow_html=True)
        
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
                            st.success("تم تسجيل الدخول بنجاح!")
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
st.markdown("<p style='color: #64748b;'>سجل طاعاتك لليوم الحالي. لاحظ أن الأيام الفائتة مقفلة للأرشفة فقط.</p>", unsafe_allow_html=True)

today = date.today()

tab_today, tab_history = st.tabs(["📅 ورد اليوم الحالي (متاح للتسجيل)", "📈 الأرشيف والسجل السابق (مقفل للعرض فقط)"])

with tab_today:
    st.markdown(f"### تسجيل عبادات تاريخ اليوم: **{today}**")
    
    # جلب سجل اليوم إن وجد مسبقاً
    try:
        existing_log = supabase.table('istiqama_logs').select('*').eq('user_id', user_id).eq('log_date', str(today)).execute()
        log_data = existing_log.data[0] if existing_log.data else None
    except:
        log_data = None

    with st.form("daily_worship_form"):
        st.markdown("#### 🕌 الصلوات في المسجد")
        c1, c2, c3, c4, c5 = st.columns(5)
        fajr = c1.checkbox("الفجر", value=log_data['fajr_mosque'] if log_data else False)
        dhuhr = c2.checkbox("الظهر", value=log_data['dhuhr_mosque'] if log_data else False)
        asr = c3.checkbox("العصر", value=log_data['asr_mosque'] if log_data else False)
        maghrib = c4.checkbox("المغرب", value=log_data['maghrib_mosque'] if log_data else False)
        isha = c5.checkbox("العشاء", value=log_data['isha_mosque'] if log_data else False)
        
        st.markdown("---")
        st.markdown("#### 📖 الورد القرآني والأذكار")
        quran_p = st.number_input("عدد صفحات القرآن اليومية", min_value=0, value=log_data['quran_pages'] if log_data else 0)
        adhkar_val = st.checkbox("أذكار الصباح والمساء", value=log_data['adhkar'] if log_data else False)
        
        tazkiya_val = st.text_area("تزكية النفس / خواطر اليوم", value=log_data['tazkiya'] if log_data else "")
        
        submit_log = st.form_submit_button("💾 حفظ ورد اليوم", use_container_width=True)
        
        if submit_log:
            try:
                log_payload = {
                    'user_id': user_id,
                    'log_date': str(today),
                    'fajr_mosque': fajr,
                    'dhuhr_mosque': dhuhr,
                    'asr_mosque': asr,
                    'maghrib_mosque': maghrib,
                    'isha_mosque': isha,
                    'quran_pages': quran_p,
                    'adhkar': adhkar_val,
                    'tazkiya': tazkiya_val
                }
                
                if log_data:
                    supabase.table('istiqama_logs').update(log_payload).eq('id', log_data['id']).execute()
                    st.success("✅ تم تحديث عبادات اليوم بنجاح!")
                else:
                    supabase.table('istiqama_logs').insert(log_payload).execute()
                    st.success("🎉 تقبل الله طاعاتك! تم حفظ سجل اليوم بنجاح.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")

with tab_history:
    st.markdown("### 📊 سجلك الروحي للأيام السابقة (مقفل - عرض فقط)")
    try:
        history_res = supabase.table('istiqama_logs').select('*').eq('user_id', user_id).order('log_date', desc=True).execute()
        if history_res.data:
            df_hist = pd.DataFrame(history_res.data)
            st.dataframe(df_hist, use_container_width=True)
        else:
            st.info("لا توجد سجلات سابقة حتى الآن.")
    except Exception as ex:
        st.error(f"خطأ في جلب الأرشيف: {ex}")
