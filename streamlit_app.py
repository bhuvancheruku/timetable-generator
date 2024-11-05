from datetime import time, datetime, timedelta
import random
import streamlit as st
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# Ensure session state variables are initialized
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if "faculty_members" not in st.session_state:
    st.session_state.faculty_members = {}

# Function to generate the timetable for one section
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
    if end_time <= start_time:
        st.error("End time must be later than start time.")
        return pd.DataFrame()

    total_available_minutes = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute) - total_break_duration
    if total_available_minutes <= 0 or num_classes <= 0:
        st.error("Insufficient time available for the classes.")
        return pd.DataFrame()

    class_duration = total_available_minutes // num_classes
    if class_duration <= 0:
        st.error("Class duration must be greater than zero.")
        return pd.DataFrame()

    timetable = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    current_time = datetime.combine(datetime.today(), start_time)
    end_datetime = datetime.combine(datetime.today(), end_time)

    for day in timetable:
        used_subjects = set()
        used_faculty = set()
        
        for _ in range(num_classes):
            if current_time >= end_datetime:
                break

            available_subjects = [subj for subj in subjects if subj not in used_subjects]
            if not available_subjects:
                break

            subject = random.choice(available_subjects)
            faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
            timetable[day].append({"Time": current_time.strftime("%I:%M %p"), "Subject": subject, "Faculty": faculty})
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)
            
        for break_time, duration in breaks:
            timetable[day].append({"Time": break_time.strftime("%I:%M %p"), "Subject": "Break", "Faculty": ""})
            current_time += timedelta(minutes=duration)
    
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        timetable[day].append({"Time": "Lab Session", "Subject": "Lab", "Faculty": ""})
    
    return pd.DataFrame.from_dict({day: timetable[day] for day in timetable}, orient='index')

# Sidebar inputs for college timings and configuration for subjects, faculty, etc.
start_time_hour = st.sidebar.number_input("College Start Hour", min_value=1, max_value=12, value=9)
start_time_minute = st.sidebar.number_input("College Start Minute", min_value=0, max_value=59, value=0)
start_time_am_pm = st.sidebar.radio("Start Time AM/PM", options=["AM", "PM"])
start_time = time(start_time_hour % 12 + (12 if start_time_am_pm == "PM" else 0), start_time_minute)

end_time_hour = st.sidebar.number_input("College End Hour", min_value=1, max_value=12, value=5)
end_time_minute = st.sidebar.number_input("College End Minute", min_value=0, max_value=59, value=0)
end_time_am_pm = st.sidebar.radio("End Time AM/PM", options=["AM", "PM"])
end_time = time(end_time_hour % 12 + (12 if end_time_am_pm == "PM" else 0), end_time_minute)

# Group name and number of sections
group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

# Capture subjects and faculty details
num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=5)

# Reset session state for subjects and faculty members if the number of subjects changes
if len(st.session_state.subjects) != num_subjects:
    st.session_state.subjects = [""] * num_subjects
    st.session_state.faculty_members = {f"Subject {i+1}": [] for i in range(num_subjects)}

# Input fields for each subject and its faculty members
for i in range(num_subjects):
    subject_name = st.sidebar.text_input(f"Subject Name {i + 1}", value=st.session_state.subjects[i], key=f"subject_{i}")
    if subject_name:
        st.session_state.subjects[i] = subject_name

        # Initialize faculty members for the subject if not present in session state
        if subject_name not in st.session_state.faculty_members:
            st.session_state.faculty_members[subject_name] = []

        # Input number of faculty for this subject
        num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, value=1, key=f"faculty_count_{i}")
        
        # Adjust the number of faculty members for this subject in session state
        if len(st.session_state.faculty_members[subject_name]) != num_faculty:
            st.session_state.faculty_members[subject_name] = [""] * num_faculty
        
        # Input each faculty member's name for this subject
        for j in range(num_faculty):
            faculty_name = st.sidebar.text_input(f"Faculty Name {j + 1} for {subject_name}", value=st.session_state.faculty_members[subject_name][j], key=f"faculty_{i}_{j}")
            st.session_state.faculty_members[subject_name][j] = faculty_name

# Break timings and durations
breaks = []
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=time(11, 0))
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=time(13, 0))
    lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
    breaks.append((lunch_break_time, lunch_break_duration))

if st.button("Generate Timetable"):
    if not group_name:
        st.error("Please enter a group name.")
    else:
        # Logic to create the timetable structure
        timetable_data = []
        for subject, faculty in st.session_state.faculty_members.items():
            timetable_data.append([subject] + faculty)

        # Convert timetable_data to a DataFrame for better presentation
        df = pd.DataFrame(timetable_data)

        # Display timetable in Streamlit
        st.dataframe(df)

        # PDF export functionality
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        
        # Draw the timetable to PDF (simple example)
        y_position = height - 50
        for subject in df.columns:
            subject_text = str(subject) if subject is not None else"Unknown"
            p.drawString(100, y_position, subject)
            y_position -= 20
            
        p.showPage()
        p.save()
        output.seek(0)

        st.download_button("Download Timetable PDF", output, "timetable.pdf", "application/pdf")
