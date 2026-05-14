import streamlit as st
import requests
import pandas as pd
import io
from datetime import datetime
import time

st.set_page_config(
    page_title="Bihar Matric Result Fetcher",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
body {background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1b2e 100%);}
.stApp {background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1b2e 100%);}
[data-testid="stHeader"] {background: transparent;}
h1, h2, h3 {background: linear-gradient(135deg, #00d4ff, #0099ff);-webkit-background-clip: text;-webkit-text-fill-color: transparent;}
.stButton > button {background: linear-gradient(135deg, #00d4ff, #0099ff);color: white;border: none;padding: 12px 30px;font-weight: bold;}
</style>
""", unsafe_allow_html=True)

API_URLS = [
    'https://api.matricbiharboard.com/result?roll_code={rc}&roll_no={rn}',
    'https://examapi.biharboardonline.org/result?roll_code={rc}&roll_no={rn}',
    'https://resultapi.biharboardonline.org/result?roll_code={rc}&roll_no={rn}',
]

SESSION = requests.Session()
SESSION.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})

@st.cache_data
def fetch_student(roll_code, roll_no):
    for url_template in API_URLS:
        url = url_template.format(rc=roll_code, rn=roll_no)
        try:
            response = SESSION.get(url, timeout=10)
            json_data = response.json()

            if not (json_data.get('success') and json_data.get('data')):
                continue

            d = json_data['data']
            subjects = d.get('subjects', [])
            sub_marks = {}
            sci_prac = ''
            sst_prac = ''

            for subject in subjects:
                name = subject.get('sub_name', '').upper().strip()
                sub_marks[name] = subject.get('sub_total', '')

                if 'SCIENCE' in name and 'SOCIAL' not in name:
                    sci_prac = subject.get('ia_sci', '')

                if 'SOCIAL' in name:
                    p1 = subject.get('project_work', '')
                    p2 = subject.get('literacy_activity', '')
                    sst_prac = f'{p1}+{p2}' if p1 and p2 else (p1 or p2)

            return {
                'RollCode': roll_code,
                'RollNo': roll_no,
                'Name': d.get('name', ''),
                'Father': d.get('father_name', ''),
                'School': d.get('school_name', ''),
                'RegNo': d.get('reg_no', ''),
                'Total': d.get('total', ''),
                'Division': d.get('division', ''),
                'M.I.L': next((v for k, v in sub_marks.items() if 'M.I.L' in k), ''),
                'English': next((v for k, v in sub_marks.items() if 'ENGLISH' in k), ''),
                'Math': next((v for k, v in sub_marks.items() if 'MATH' in k), ''),
                'Science': next((v for k, v in sub_marks.items() if 'SCIENCE' in k and 'SOCIAL' not in k), ''),
                'Sci Practical': sci_prac,
                'Social Science': next((v for k, v in sub_marks.items() if 'SOCIAL' in k), ''),
                'SST Practical': sst_prac,
                'S.I.L': next((v for k, v in sub_marks.items() if 'S.I.L' in k), '')
            }

        except Exception:
            continue

    return None

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("### 📋 Bihar Matric Result Fetcher")
    st.markdown("**By Shiksha Sathee**")
    st.markdown("[🔴 Subscribe on YouTube](https://youtube.com/@ShikhaSathee)")

st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.markdown("### 🎓 Enter School Details")
    
    with st.form("fetch_form", clear_on_submit=False):
        roll_code = st.text_input(
            "Roll Code",
            placeholder="e.g., 31445",
            max_chars=10,
            help="Your school's unique roll code"
        )
        
        num_students = st.number_input(
            "Number of Students",
            min_value=1,
            max_value=500,
            value=50,
            help="Roll numbers start from 2600001"
        )
        
        submitted = st.form_submit_button("▶ Fetch Results", use_container_width=True)

    if submitted:
        if not roll_code:
            st.error("❌ Please enter a Roll Code")
        elif num_students < 1:
            st.error("❌ Please enter a valid number of students")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.empty()
            
            results = []
            logs = []
            
            for idx in range(num_students):
                roll_no = str(2600001 + idx)
                status_text.markdown(f"**⏳ Fetching {idx + 1} of {num_students}...**")
                
                row = fetch_student(roll_code, roll_no)
                
                if row:
                    results.append(row)
                    log_msg = f"✓ {row['Name']} | {row['Total']} marks | {row['Division']}"
                    logs.append(f"<span style='color: #00ff88'>{log_msg}</span>")
                else:
                    results.append({
                        'RollCode': roll_code,
                        'RollNo': roll_no,
                        'Name': 'No Data',
                        'Father': '', 'School': '', 'RegNo': '', 'Total': '',
                        'Division': '', 'M.I.L': '', 'English': '', 'Math': '',
                        'Science': '', 'Sci Practical': '', 'Social Science': '',
                        'SST Practical': '', 'S.I.L': ''
                    })
                    log_msg = f"⚠ No data for {roll_no}"
                    logs.append(f"<span style='color: #ffaa00'>{log_msg}</span>")
                
                progress = (idx + 1) / num_students
                progress_bar.progress(progress)
                
                with log_container.container():
                    st.markdown(
                        "<div style='background: rgba(0,0,0,0.5); border: 1px solid rgba(0,212,255,0.3); border-radius: 10px; padding: 16px; max-height: 300px; overflow-y: auto;'>" +
                        "<br>".join(logs[-15:]) +
                        "</div>",
                        unsafe_allow_html=True
                    )
                
                time.sleep(0.3)
            
            df = pd.DataFrame(results)
            df.fillna('', inplace=True)
            
            pass_count = len(df[df['Division'].astype(str).str.contains('Division|Pass', case=False, na=False)])
            fail_count = len(df[df['Division'].astype(str).str.contains('Fail|Comp', case=False, na=False)])
            no_data = len(df[df['Name'] == 'No Data'])
            fetched_ok = num_students - no_data
            
            topper_name = ''
            topper_marks = ''
            nums = pd.to_numeric(df['Total'], errors='coerce')
            if not nums.isna().all():
                i = nums.idxmax()
                topper_name = str(df.loc[i, 'Name'])
                topper_marks = str(df.loc[i, 'Total'])
            
            progress_bar.empty()
            status_text.empty()
            log_container.empty()
            
            st.markdown("---")
            st.markdown("### 📊 Results Summary")
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total", num_students)
            with col2:
                st.metric("Fetched", fetched_ok)
            with col3:
                st.metric("Passed", pass_count)
            with col4:
                st.metric("Failed", fail_count)
            with col5:
                st.metric("No Data", no_data)
            
            if topper_name:
                st.success(f"🏆 **School Topper:** {topper_name} ({topper_marks} marks)")
            
            fn = f"{roll_code}_Matric_Result_2026.xlsx"
            buf = io.BytesIO()
            
            with pd.ExcelWriter(buf, engine='openpyxl') as w:
                df.to_excel(w, sheet_name='Results', index=False)
                pd.DataFrame([{
                    'Roll Code': roll_code,
                    'Total Students': num_students,
                    'Records Fetched': fetched_ok,
                    'Pass': pass_count,
                    'Fail': fail_count,
                    'Topper': topper_name,
                    'Topper Marks': topper_marks,
                    'Generated On': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }]).to_excel(w, sheet_name='Summary', index=False)
            
            buf.seek(0)
            excel_data = buf.getvalue()
            
            st.download_button(
                label="📥 Download Excel Report",
                data=excel_data,
                file_name=fn,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.markdown("### 📋 Student Data (First 10)")
            st.dataframe(df.head(10), use_container_width=True)
            
            st.success(f"✅ Complete! {fetched_ok} records fetched.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #7a7a7a;'><p><b>Made with 💙 by Shiksha Sathee</b></p><p>Educational tools for Bihar teachers</p></div>", unsafe_allow_html=True)
