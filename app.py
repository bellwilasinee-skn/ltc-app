import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าจอ
# ---------------------------------------------------------
st.set_page_config(page_title="ระบบติดตามสัญญา LTC & ประวัติประเมิน ADL", page_icon="🩺", layout="wide")

DB_NAME = "ltc_contracts_v3.db"

# ---------------------------------------------------------
# 2. เตรียมฐานข้อมูล SQLite (ผู้ป่วย, สัญญา/ADL รายปี, ผู้ใช้งาน)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. ตารางข้อมูลหลักของผู้ป่วย
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            phone TEXT,
            cg_name TEXT NOT NULL,
            nurse_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. ตารางประวัติสัญญา & การประเมิน ADL / ของสนับสนุน (1 ผู้ป่วย มีได้หลายสัญญา)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            contract_year INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            adl_score INTEGER,
            adl_group TEXT,
            item_type TEXT NOT NULL,
            diaper_size TEXT,
            last_received_date DATE NOT NULL,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    """)
    
    # 3. ตารางบัญชีผู้ใช้งาน
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # บัญชีเริ่มต้น (admin / 1234)
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
    st.caption("<p style='text-align: center;'>รพ.สต.ตลุกเทียม - กรุณาเข้าสู่ระบบ หรือลงทะเบียนบัญชีผู้ใช้งานใหม่</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 เข้าสู่ระบบ (Log-in)", "📝 ลงทะเบียน (Register)"])
        
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
                        
        with tab_register:
            with st.form("register_form"):
                reg_username = st.text_input("ตั้งชื่อผู้ใช้งาน (Username)")
                reg_password = st.text_input("ตั้งรหัสผ่าน (Password)", type="password")
                reg_confirm = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password")
                submit_reg = st.form_submit_button("ลงทะเบียนบัญชีใหม่", use_container_width=True)
                
                if submit_reg:
                    if reg_username and reg_password and reg_confirm:
                        if reg_password != reg_confirm:
                            st.error("รหัสผ่านไม่ตรงกัน")
                        else:
                            conn = sqlite3.connect(DB_NAME)
                            cursor = conn.cursor()
                            try:
                                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_username, reg_password))
                                conn.commit()
                                st.success("ลงทะเบียนสำเร็จ! สามารถเข้าสู่ระบบได้เลย")
                            except sqlite3.IntegrityError:
                                st.error("ชื่อผู้ใช้งานนี้มีในระบบแล้ว")
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
    st.write(f"👤 ผู้ใช้งาน: **{st.session_state['user_name']}**")
    if st.button("🚪 ออกจากระบบ", use_container_width=True):
        logout()

st.title("🩺 ระบบติดตามสัญญา LTC & ประวัติประเมิน ADL ย้อนหลัง")
st.caption("โรงพยาบาลส่งเสริมสุขภาพตำบลตลุกเทียม - บันทึกสัญญา 1 ปี และเปรียบเทียบประวัติประเมินรายปี")

tab_add, tab_renew, tab_history = st.tabs(["➕ ลงทะเบียนผู้ป่วยใหม่", "🔄 ต่อสัญญาปีถัดไป / ประเมิน ADL", "📜 ดูประวัติย้อนหลัง"])

# --- TAB 1: เพิ่มผู้ป่วยใหม่ (สัญญาปีที่ 1) ---
with tab_add:
    with st.form("add_patient_form", clear_on_submit=True):
        st.subheader("📋 ลงทะเบียนผู้ป่วยใหม่ (สัญญาปีที่ 1)")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            patient_name = st.text_input("ชื่อ-นามสกุล ผู้ป่วย LTC *", placeholder="นายสมชาย ใจดี")
            phone = st.text_input("เบอร์โทรศัพท์ติดต่อ", placeholder="081-xxx-xxxx")
            cg_name = st.text_input("ชื่อ CG ที่ดูแล *", placeholder="นางสมศรี (CG)")
            nurse_name = st.text_input("พยาบาลเคสเมเนเจอร์ *", placeholder="พว.กานดา")
            
        with col2:
            start_date = st.date_input("วันเริ่มสัญญา", datetime.now().date(), key="add_start")
            default_end = start_date + timedelta(days=365)
            end_date = st.date_input("วันหมดสัญญา (1 ปี)", default_end, key="add_end")
            
            adl_score = st.number_input("คะแนน ADL", min_value=0, max_value=20, value=10)
            adl_group = st.selectbox("กลุ่มติดบ้าน/ติดเตียง", ["ติดสังคม (12-20)", "ติดบ้าน (5-11)", "ติดเตียง (0-4)"])

        with col3:
            item_type = st.radio("รายการของสนับสนุน *", ["นม", "ผ้าอ้อมผู้ใหญ่"], horizontal=True, key="add_item")
            diaper_size = "-"
            if item_type == "ผ้าอ้อมผู้ใหญ่":
                diaper_size = st.selectbox("ขนาดผ้าอ้อม (Size) *", ["M", "L", "XL", "XXL", "อื่นๆ"], key="add_size")
            
            last_received_date = st.date_input("วันที่รับของล่าสุด", datetime.now().date(), key="add_last")

        notes = st.text_area("หมายเหตุเพิ่มเติม", placeholder="ข้อความบันทึกเพิ่มเติม...", key="add_notes")
        submitted = st.form_submit_button("💾 บันทึกผู้ป่วยและสัญญาปีที่ 1", use_container_width=True)
        
        if submitted:
            if patient_name and cg_name and nurse_name:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                # 1. บันทึกผู้ป่วย
                cursor.execute("INSERT INTO patients (patient_name, phone, cg_name, nurse_name) VALUES (?, ?, ?, ?)",
                               (patient_name, phone, cg_name, nurse_name))
                patient_id = cursor.lastrowid
                
                # 2. บันทึกสัญญาปีที่ 1
                cursor.execute("""
                    INSERT INTO contracts (patient_id, contract_year, start_date, end_date, adl_score, adl_group, item_type, diaper_size, last_received_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (patient_id, 1, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"),
                      adl_score, adl_group, item_type, diaper_size, last_received_date.strftime("%Y-%m-%d"), notes))
                
                conn.commit()
                conn.close()
                st.success(f"บันทึกข้อมูลคุณ {patient_name} (สัญญาปีที่ 1) เรียบร้อยแล้ว!")
                st.rerun()
            else:
                st.error("กรุณากรอกข้อมูลที่มีเครื่องหมาย * ให้ครบถ้วน")

# ดึงข้อมูลผู้ป่วยและสัญญาล่าสุด
conn = sqlite3.connect(DB_NAME)
query_latest = """
    SELECT p.id as patient_id, p.patient_name, p.phone, p.cg_name, p.nurse_name,
           c.id as contract_id, c.contract_year, c.start_date, c.end_date, 
           c.adl_score, c.adl_group, c.item_type, c.diaper_size, c.last_received_date, c.notes
    FROM patients p
    JOIN contracts c ON p.id = c.patient_id
    WHERE c.id IN (SELECT MAX(id) FROM contracts GROUP BY patient_id)
    ORDER BY c.end_date ASC
"""
df_latest = pd.read_sql_query(query_latest, conn)
conn.close()

# --- TAB 2: ต่อสัญญาปีถัดไป / อัปเดตการประเมิน ADL ---
with tab_renew:
    if not df_latest.empty:
        patient_options = {f"ID {row['patient_id']}: {row['patient_name']} (สัญญาล่าสุด: ปีที่ {row['contract_year']})": row for _, row in df_latest.iterrows()}
        selected_patient_str = st.selectbox("เลือกผู้ป่วยที่ต้องการต่อสัญญา/ประเมิน ADL รอบใหม่:", list(patient_options.keys()))
        selected_row = patient_options[selected_patient_str]
        
        next_year = selected_row['contract_year'] + 1
        st.info(f"💡 กำลังทำรายการ: **ต่อสัญญาปีที่ {next_year}** สำหรับคุณ **{selected_row['patient_name']}** (ข้อมูลเดิมปีที่ {selected_row['contract_year']} จะถูกเก็บเป็นประวัติไว้)")
        
        with st.form("renew_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**ข้อมูลผู้ป่วย**")
                st.write(f"- ชื่อ-สกุล: {selected_row['patient_name']}")
                ren_cg = st.text_input("CG ที่ดูแล", value=selected_row['cg_name'])
                ren_nurse = st.text_input("พยาบาลเคสเมเนเจอร์", value=selected_row['nurse_name'])
                
            with col2:
                # วันเริ่มสัญญาใหม่นับจากวันหมดสัญญาเดิม หรือวันปัจจุบัน
                old_end = datetime.strptime(selected_row['end_date'], "%Y-%m-%d").date()
                ren_start = st.date_input("วันเริ่มสัญญาปีใหม่", old_end)
                ren_end = st.date_input("วันหมดสัญญาปีใหม่ (1 ปี)", ren_start + timedelta(days=365))
                
                ren_adl_score = st.number_input("คะแนน ADL ประเมินใหม่", min_value=0, max_value=20, value=int(selected_row['adl_score'] if selected_row['adl_score'] else 10))
                ren_adl_group = st.selectbox("กลุ่มประเมินใหม่", ["ติดสังคม (12-20)", "ติดบ้าน (5-11)", "ติดเตียง (0-4)"])

            with col3:
                item_idx = 0 if selected_row['item_type'] == "นม" else 1
                ren_item_type = st.radio("รายการของที่ได้รับ", ["นม", "ผ้าอ้อมผู้ใหญ่"], index=item_idx, horizontal=True)
                
                size_opts = ["M", "L", "XL", "XXL", "อื่นๆ"]
                d_idx = size_opts.index(selected_row['diaper_size']) if selected_row['diaper_size'] in size_opts else 0
                ren_diaper_size = "-"
                if ren_item_type == "ผ้าอ้อมผู้ใหญ่":
                    ren_diaper_size = st.selectbox("ขนาดผ้าอ้อม (Size)", size_opts, index=d_idx)
                
                ren_last_date = st.date_input("วันที่รับของรอบใหม่", datetime.now().date())

            ren_notes = st.text_area("หมายเหตุการต่อสัญญา/ประเมิน", placeholder=f"บันทึกประเมิน ADL รอบปีที่ {next_year}...")
            
            renew_submitted = st.form_submit_button(f"🔄 บันทึกการต่อสัญญาปีที่ {next_year}", use_container_width=True)
            
            if renew_submitted:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                
                # อัปเดตข้อมูล CG/Nurse หากมีการเปลี่ยนแปลง
                cursor.execute("UPDATE patients SET cg_name=?, nurse_name=? WHERE id=?", (ren_cg, ren_nurse, selected_row['patient_id']))
                
                # เพิ่มสัญญาฉบับใหม่ลงตาราง contracts (ไม่ทับอันเก่า)
                cursor.execute("""
                    INSERT INTO contracts (patient_id, contract_year, start_date, end_date, adl_score, adl_group, item_type, diaper_size, last_received_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (selected_row['patient_id'], next_year, ren_start.strftime("%Y-%m-%d"), ren_end.strftime("%Y-%m-%d"),
                      ren_adl_score, ren_adl_group, ren_item_type, ren_diaper_size, ren_last_date.strftime("%Y-%m-%d"), ren_notes))
                
                conn.commit()
                conn.close()
                st.success(f"บันทึกการต่อสัญญาปีที่ {next_year} ของคุณ {selected_row['patient_name']} เรียบร้อยแล้ว!")
                st.rerun()
    else:
        st.info("ยังไม่มีข้อมูลผู้ป่วยในระบบ")

# --- TAB 3: ดูประวัติย้อนหลัง (Timeline) ---
with tab_history:
    if not df_latest.empty:
        conn = sqlite3.connect(DB_NAME)
        all_patients = pd.read_sql_query("SELECT * FROM patients", conn)
        conn.close()
        
        selected_hist_id = st.selectbox("เลือกผู้ป่วยเพื่อดูประวัติสัญญาย้อนหลังทุกปี:", 
                                         options=all_patients['id'], 
                                         format_func=lambda x: f"ID {x}: {all_patients[all_patients['id']==x]['patient_name'].values[0]}")
        
        if selected_hist_id:
            conn = sqlite3.connect(DB_NAME)
            df_history = pd.read_sql_query("""
                SELECT contract_year as 'สัญญาปีที่', start_date as 'วันเริ่มสัญญา', end_date as 'วันหมดสัญญา',
                       adl_score as 'คะแนน ADL', adl_group as 'ผลประเมิน ADL', item_type as 'ของสนับสนุน',
                       diaper_size as 'ขนาดผ้าอ้อม', last_received_date as 'วันที่รับของ', notes as 'หมายเหตุ'
                FROM contracts
                WHERE patient_id = ?
                ORDER BY contract_year DESC
            """, conn, params=(selected_hist_id,))
            conn.close()
            
            p_info = all_patients[all_patients['id'] == selected_hist_id].iloc[0]
            st.markdown(f"### 📜 ประวัติสัญญาย้อนหลัง: คุณ **{p_info['patient_name']}**")
            st.write(f"📞 เบอร์โทร: {p_info['phone']} | CG: {p_info['cg_name']} | พยาบาล: {p_info['nurse_name']}")
            
            st.dataframe(df_history, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีประวัติในระบบ")

# ---------------------------------------------------------
# 5. การคำนวณการแจ้งเตือนต่อสัญญา & ประเมิน ADL (45 วัน)
# ---------------------------------------------------------
if not df_latest.empty:
    today = datetime.now().date()
    df_latest['end_dt'] = pd.to_datetime(df_latest['end_date']).dt.date
    df_latest['จำนวนวันคงเหลือ'] = df_latest['end_dt'].apply(lambda x: (x - today).days)
    
    def get_status_adl(days):
        if days < 0:
            return "🔴 สัญญาหมดอายุแล้ว"
        elif days <= 45:
            return "🟡 ต้องประเมิน ADL / ต่อสัญญา (<= 45 วัน)"
        else:
            return "🟢 ปกติ (> 45 วัน)"
            
    df_latest['สถานะสัญญา'] = df_latest['จำนวนวันคงเหลือ'].apply(get_status_adl)
    
    st.divider()
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("ผู้ป่วย LTC ทั้งหมด", f"{len(df_latest)} ราย")
    c2.metric("🟡 ต้องประเมิน ADL (<= 45 วัน)", f"{len(df_latest[(df_latest['จำนวนวันคงเหลือ'] >= 0) & (df_latest['จำนวนวันคงเหลือ'] <= 45)])} ราย")
    c3.metric("🔴 สัญญาหมดอายุแล้ว", f"{len(df_latest[df_latest['จำนวนวันคงเหลือ'] < 0])} ราย")
    c4.metric("📦 รับผ้าอ้อมผู้ใหญ่", f"{len(df_latest[df_latest['item_type'] == 'ผ้าอ้อมผู้ใหญ่'])} ราย")

    adl_urgent = df_latest[(df_latest['จำนวนวันคงเหลือ'] >= 0) & (df_latest['จำนวนวันคงเหลือ'] <= 45)]
    if not adl_urgent.empty:
        st.warning("⚠️ **แจ้งเตือนเคสที่ต้องประเมิน ADL ก่อนต่อสัญญา (ภายใน 45 วัน):**")
        for _, row in adl_urgent.iterrows():
            st.write(f"- **{row['patient_name']}** (สัญญาปีที่ {row['contract_year']}) ➔ หมดสัญญา **{row['end_date']}** (เหลืออีก **{row['จำนวนวันคงเหลือ']} วัน**)")

    st.subheader("📋 สถานะสัญญาล่าสุดของเคสทั้งหมด")
    
    display_df = df_latest[[
        'patient_id', 'patient_name', 'contract_year', 'cg_name', 'nurse_name',
        'start_date', 'end_date', 'จำนวนวันคงเหลือ', 'สถานะสัญญา',
        'adl_score', 'adl_group', 'item_type', 'diaper_size'
    ]].rename(columns={
        'patient_id': 'ID',
        'patient_name': 'ชื่อผู้ป่วย LTC',
        'contract_year': 'สัญญาปีที่',
        'cg_name': 'CG ผู้ดูแล',
        'nurse_name': 'พยาบาล',
        'start_date': 'วันเริ่มสัญญา',
        'end_date': 'วันหมดสัญญา',
        'adl_score': 'คะแนน ADL',
        'adl_group': 'กลุ่ม ADL',
        'item_type': 'ของสนับสนุน',
        'diaper_size': 'ไซส์ผ้าอ้อม'
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
