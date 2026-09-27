import streamlit as st
from supabase import create_client
import re

# ==========================================
# إعدادات الواجهة الفاتحة النظيفة (بدون لون أسود)
# ==========================================
st.set_page_config(page_title="نظام استقامة", page_icon="🌙", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f8fafc !important; color: #0f172a !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    h1, h2, h3 { color: #1e3a8a !important; font-weight: 700 !important; }
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
    st.session_state.user_name = None

# شاشة تسجيل الدخول وإنشاء الحساب
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🌙 نظام استقامة</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b;'>تسجيل الدخول وحسابات المستخدمين</p>", unsafe_allow_html=True)
        
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
                    # فحص تعقيد الباسورد
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

# الشاشة الرئيسية بعد تسجيل الدخول الناجح
st.markdown(f"<h1>🌙 أهلاً بك.. ازيك يا {st.session_state.user_name}</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b;'>تم تسجيل الدخول بنجاح. الخطوة القادمة هي إضافة جدول العبادات اليومية وقفل الأيام السابقة.</p>", unsafe_allow_html=True)

if st.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()
