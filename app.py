import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าจอ
# ---------------------------------------------------------
st.set_page_config(page_title="ระบบติดตามสัญญา & ของสนับสนุน LTC", page_icon="🩺", layout="wide")

DB_NAME = "ltc_contracts_v2.db"

# ---------------------------------------------------------
# 2. เตรียมฐานข้อมูล SQLite (ผู้ป่วย & บัญชีผู้ใช้)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # ตารางข้อมูลผู้ป่วย
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            cg_name TEXT NOT NULL,
            nurse_name TEXT NOT NULL,
            phone TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            item_type TEXT NOT NULL,
            diaper_size TEXT,
            last_received_date DATE NOT NULL,
            notes TEXT
        )
    """)
    
    # ตารางบัญชีผู้ใช้งาน
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # สร้างบัญชีเริ่มต้น (admin / 1234) ถ้ายังไม่มีในระบบ
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "1234"))
        
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 3. ระบบ Log-in & Register
# ---------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

def authentication_page():
    st.markdown("<h2 style='text-align: center;'>🔒 ระบบจัดการข้อมูลผู้ป่วย LTC</h2>", unsafe_allow_html=True)
    st.caption("<p style='text-align: center;'>กรุณาเข้าสู่ระบบ หรือลงทะเบียนบัญชีผู้ใช้งานใหม่</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 เข้าสู่ระบบ (Log-in)", "📝 ลงทะเบียน (Register)"])
        
        # --- แท็บ Log-in ---
        with tab_login:
            with st.form("login_form"):
                username = st.text_input("ชื่อผู้ใช้งาน (Username)")
                password = st.text_input("รหัสผ่าน (Password)", type="password")
                submit_login = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)
                
                if submit_login:
                    if username and password:
                        conn = sqlite3.connect(DB_NAME)
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                        user = cursor.fetchone()
                        conn.close()
                        
                        if user:
                            st.session_state['logged_in'] = True
                            st.session_state['user_name'] = username
                            st.success("เข้าสู่ระบบสำเร็จ!")
                            st.rerun()
                        else:
                            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
                    else:
                        st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")
                        
        # --- แท็บ Register ---
        with tab_register:
            with st.form("register_form"):
                reg_username = st.text_input("ตั้งชื่อผู้ใช้งาน (Username)")
                reg_password = st.text_input("ตั้งรหัสผ่าน (Password)", type="password")
                reg_confirm_password = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password")
                submit_reg = st.form_submit_button("ลงทะเบียนบัญชีใหม่", use_container_width=True)
                
                if submit_reg:
                    if reg_username and reg_password and reg_confirm_password:
                        if reg_password != reg_confirm_password:
                            st.error("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
                        else:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            try:
                                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_username, reg_password))
                                conn.commit()
                                st.success("ลงทะเบียนสำเร็จ! สามารถสลับไปหน้า Log-in เพื่อเข้าสู่ระบบได้เลยครับ")
                            except sqlite3.IntegrityError:
                                st.error("ชื่อผู้ใช้งานนี้มีในระบบแล้ว กรุณาใช้ชื่ออื่น")
                            finally:
                                conn.close()
                    else:
                        st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['user_name'] = ""
    st.rerun()

if not st.session_state['logged_in']:
    authentication_page()
    st.stop()

# ---------------------------------------------------------
# 4. ส่วนแสดงผลหลัก (หลัง Log-in)
# ---------------------------------------------------------
with st.sidebar:
    st.write(f"👤 ผู้ใช้งานปัจจุบัน: **{st.session_state['user_name']}**")
    if st.button("🚪 ออกจากระบบ (Logout)", use_container_width=True):
        logout()

st.title("🩺 ระบบติดตามสัญญา LTC & ประวัติของสนับสนุนผู้ป่วย")
st.caption("ระบบบันทึก แก้ไข ลบข้อมูลการต่อสัญญา และการได้รับ นม / ผ้าอ้อมผู้ใหญ่ สำหรับเคส LTC")

tab_add, tab_edit, tab_delete = st.tabs(["➕ เพิ่มข้อมูลใหม่", "✏️ แก้ไขข้อมูล", "🗑️ ลบข้อมูล"])

# --- TAB 1: เพิ่มข้อมูลผู้ป่วยใหม่ ---
with tab_add:
    with st.form("add_patient_form", clear_on_submit=True):
        st.subheader("📋 บันทึกข้อมูลผู้ป่วยใหม่")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("ชื่อ-นามสกุล ผู้ป่วย LTC *", placeholder="เช่น นายสมชาย ใจดี")
            cg_name = st.text_input("ชื่อ CG ที่ดูแล *", placeholder="เช่น นางสมศรี (CG)")
            nurse_name = st.text_input("พยาบาลผู้รับผิดชอบ (เคสเมเนเจอร์) *", placeholder="เช่น พว.กานดา")
            
        with col2:
            phone = st.text_input("เบอร์โทรศัพท์ติดต่อ", placeholder="081-xxx-xxxx")
            start_date = st.date_input("วันเริ่มสัญญา LTC", datetime.now().date(), key="add_start")
            end_date = st.date_input("วันหมดอายุสัญญา LTC", datetime.now().date() + timedelta(days=365), key="add_end")

        with col3:
            st.markdown("**📦 ของสนับสนุนที่ได้รับครั้งล่าสุด**")
            item_type = st.radio(
                "รายการของที่ได้รับ *",
                ["นม", "ผ้าอ้อมผู้ใหญ่"],
                horizontal=True,
                key="add_item"
            )
            
            diaper_size = "-"
            if item_type == "ผ้าอ้อมผู้ใหญ่":
                diaper_size = st.selectbox(
                    "ระบุขนาดผ้าอ้อม (Size) *",
                    ["M", "L", "XL", "XXL", "อื่นๆ (ระบุในหมายเหตุ)"],
                    key="add_size"
                )
            
            last_received_date = st.date_input("วันที่ได้รับของครั้งล่าสุด", datetime.now().date(), key="add_last")

        notes = st.text_area("หมายเหตุเพิ่มเติม", placeholder="เช่น ปรับเปลี่ยนไซส์จาก L เป็น XL / พิกัดบ้าน...", key="add_notes")
        
        submitted = st.form_submit_button("💾 บันทึกข้อมูลใหม่", use_container_width=True)
        
        if submitted:
            if patient_name and cg_name and nurse_name:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patients (patient_name, cg_name, nurse_name, phone, start_date, end_date, item_type, diaper_size, last_received_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (patient_name, cg_name, nurse_name, phone, 
                      start_date.strftime("%Y-%m-%d"), 
                      end_date.strftime("%Y-%m-%d"), 
                      item_type, diaper_size, 
                      last_received_date.strftime("%Y-%m-%d"), notes))
                conn.commit()
                conn.close()
                st.success(f"บันทึกข้อมูลคุณ {patient_name} เรียบร้อยแล้ว!")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบถ้วน")

# ดึงข้อมูลมาเตรียมสำหรับ แก้ไข / ลบ / แสดงผล
conn = sqlite3.connect(DB_NAME)
df_all = pd.read_sql_query("SELECT * FROM patients ORDER BY id DESC", conn)
conn.close()

# --- TAB 2: แก้ไขข้อมูลผู้ป่วย ---
with tab_edit:
    if not df_all.empty:
        patient_options = {f"ID {row['id']}: {row['patient_name']}": row['id'] for _, row in df_all.iterrows()}
        selected_patient_str = st.selectbox("เลือกรายชื่อผู้ป่วยที่ต้องการแก้ไข:", list(patient_options.keys()))
        selected_id = patient_options[selected_patient_str]
        
        p_data = df_all[df_all['id'] == selected_id].iloc[0]
        
        with st.form("edit_patient_form"):
            st.subheader(f"✏️ แก้ไขข้อมูล: {p_data['patient_name']}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                edit_patient_name = st.text_input("ชื่อ-นามสกุล ผู้ป่วย LTC *", value=p_data['patient_name'])
                edit_cg_name = st.text_input("ชื่อ CG ที่ดูแล *", value=p_data['cg_name'])
                edit_nurse_name = st.text_input("พยาบาลผู้รับผิดชอบ *", value=p_data['nurse_name'])
                
            with col2:
                edit_phone = st.text_input("เบอร์โทรศัพท์ติดต่อ", value=p_data['phone'] if p_data['phone'] else "")
                edit_start_date = st.date_input("วันเริ่มสัญญา LTC", datetime.strptime(p_data['start_date'], "%Y-%m-%d").date())
                edit_end_date = st.date_input("วันหมดอายุสัญญา LTC", datetime.strptime(p_data['end_date'], "%Y-%m-%d").date())

            with col3:
                st.markdown("**📦 ของสนับสนุนที่ได้รับครั้งล่าสุด**")
                item_idx = 0 if p_data['item_type'] == "นม" else 1
                edit_item_type = st.radio("รายการของที่ได้รับ *", ["นม", "ผ้าอ้อมผู้ใหญ่"], index=item_idx, horizontal=True)
                
                size_options = ["M", "L", "XL", "XXL", "อื่นๆ (ระบุในหมายเหตุ)"]
                default_size_idx = size_options.index(p_data['diaper_size']) if p_data['diaper_size'] in size_options else 0
                
                edit_diaper_size = "-"
                if edit_item_type == "ผ้าอ้อมผู้ใหญ่":
                    edit_diaper_size = st.selectbox("ระบุขนาดผ้าอ้อม (Size) *", size_options, index=default_size_idx)
                
                edit_last_received_date = st.date_input("วันที่ได้รับของครั้งล่าสุด", datetime.strptime(p_data['last_received_date'], "%Y-%m-%d").date())

            edit_notes = st.text_area("หมายเหตุเพิ่มเติม", value=p_data['notes'] if p_data['notes'] else "")
            
            update_submitted = st.form_submit_button("🔄 อัปเดตข้อมูล", use_container_width=True)
            
            if update_submitted:
                if edit_patient_name and edit_cg_name and edit_nurse_name:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE patients 
                        SET patient_name=?, cg_name=?, nurse_name=?, phone=?, start_date=?, end_date=?, item_type=?, diaper_size=?, last_received_date=?, notes=?
                        WHERE id=?
                    """, (edit_patient_name, edit_cg_name, edit_nurse_name, edit_phone,
                          edit_start_date.strftime("%Y-%m-%d"), 
                          edit_end_date.strftime("%Y-%m-%d"), 
                          edit_item_type, edit_diaper_size, 
                          edit_last_received_date.strftime("%Y-%m-%d"), edit_notes, selected_id))
                    conn.commit()
                    conn.close()
                    st.success(f"อัปเดตข้อมูลคุณ {edit_patient_name} เรียบร้อยแล้ว!")
                    st.rerun()
                else:
                    st.error("กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบถ้วน")
    else:
        st.info("ยังไม่มีข้อมูลผู้ป่วยในระบบสำหรับแก้ไข")

# --- TAB 3: ลบข้อมูลผู้ป่วย ---
with tab_delete:
    if not df_all.empty:
        patient_del_options = {f"ID {row['id']}: {row['patient_name']} (สัญญาหมด: {row['end_date']})": row['id'] for _, row in df_all.iterrows()}
        selected_del_str = st.selectbox("เลือกรายชื่อผู้ป่วยที่ต้องการลบ:", list(patient_del_options.keys()), key="del_select")
        selected_del_id = patient_del_options[selected_del_str]
        
        del_p_name = df_all[df_all['id'] == selected_del_id].iloc[0]['patient_name']
        
        st.warning(f"⚠️ คุณกำลังจะลบข้อมูลของ: **{del_p_name}** (การลบจะไม่สามารถย้อนกลับได้)")
        
        col_del1, col_del2 = st.columns([1, 4])
        with col_del1:
            if st.button("❌ ยืนยันการลบข้อมูล", type="primary", use_container_width=True):
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM patients WHERE id=?", (selected_del_id,))
                conn.commit()
                conn.close()
                st.success(f"ลบข้อมูลคุณ {del_p_name} เรียบร้อยแล้ว!")
                st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลผู้ป่วยในระบบสำหรับลบ")

# ---------------------------------------------------------
# 5. ส่วนแสดงตารางข้อมูลและระบบคำนวณการแจ้งเตือน
# ---------------------------------------------------------
if not df_all.empty:
    today = datetime.now().date()
    df_all['end_dt'] = pd.to_datetime(df_all['end_date']).dt.date
    df_all['จำนวนวันคงเหลือ'] = df_all['end_dt'].apply(lambda x: (x - today).days)
    
    def get_status(days):
        if days < 0:
            return "🔴 หมดอายุแล้ว"
        elif days <= 30:
            return "🟡 ต้องต่อสัญญา (<= 30 วัน)"
        elif days <= 60:
            return "🟠 เฝ้าระวัง (31-60 วัน)"
        else:
            return "🟢 ปกติ (> 60 วัน)"
            
    df_all['สถานะสัญญา'] = df_all['จำนวนวันคงเหลือ'].apply(get_status)
    
    st.divider()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ผู้ป่วย LTC ทั้งหมด", f"{len(df_all)} ราย")
    c2.metric("🔴 หมดอายุสัญญาแล้ว", f"{len(df_all[df_all['จำนวนวันคงเหลือ'] < 0])} ราย")
    c3.metric("🟡 ต้องต่อสัญญา (<= 30 วัน)", f"{len(df_all[(df_all['จำนวนวันคงเหลือ'] >= 0) & (df_all['จำนวนวันคงเหลือ'] <= 30)])} ราย")
    c4.metric("📦 รับผ้าอ้อมผู้ใหญ่", f"{len(df_all[df_all['item_type'] == 'ผ้าอ้อมผู้ใหญ่'])} ราย")

    st.subheader("📋 รายชื่อผู้ป่วย ประวัติรับของสนับสนุน และสถานะต่อสัญญา")
    
    filter_item = st.radio("กรองตามของที่ได้รับ:", ["ทั้งหมด", "นม", "ผ้าอ้อมผู้ใหญ่"], horizontal=True, key="filter_radio")
    
    filtered_df = df_all.copy()
    if filter_item != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df['item_type'] == filter_item]
        
    display_df = filtered_df[[
        'id', 'patient_name', 'cg_name', 'nurse_name', 'phone', 
        'start_date', 'end_date', 'จำนวนวันคงเหลือ', 'สถานะสัญญา',
        'item_type', 'diaper_size', 'last_received_date', 'notes'
    ]].rename(columns={
        'id': 'ID',
        'patient_name': 'ชื่อผู้ป่วย LTC',
        'cg_name': 'CG ผู้ดูแล',
        'nurse_name': 'พยาบาลเคสเมเนเจอร์',
        'phone': 'เบอร์โทร',
        'start_date': 'วันเริ่มสัญญา',
        'end_date': 'วันหมดสัญญา',
        'item_type': 'ของที่ได้รับ',
        'diaper_size': 'ขนาดผ้าอ้อม (Size)',
        'last_received_date': 'วันที่รับของล่าสุด',
        'notes': 'หมายเหตุ'
    })
    
    st.dataframe(
        display_df,
        column_config={
            "จำนวนวันคงเหลือ": st.column_config.NumberColumn(
                "จำนวนวันคงเหลือ",
                format="%d วัน"
            ),
            "ขนาดผ้าอ้อม (Size)": st.column_config.TextColumn(
                "ขนาดผ้าอ้อม (Size)",
                help="แสดงไซส์เฉพาะกรณีเลือกรับผ้าอ้อมผู้ใหญ่"
            )
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("ยังไม่มีข้อมูลในระบบ สามารถกรอกแบบฟอร์มด้านบนเพื่อเพิ่มรายชื่อแรกได้เลยครับ")