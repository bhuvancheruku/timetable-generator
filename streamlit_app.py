from datetime import time
import tempfile
import random
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

import pandas as pd
import random
from datetime import timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import streamlit as st
from datetime import time

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    # Calculate total break duration
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
    # Validate that end_time is later than start_time
    if end_time <= start_time:
        st.error("End time must be later than start time.")
        return pd.DataFrame()  # Return an empty DataFrame if the times are invalid

    # Calculate total available minutes for classes
    total_available_minutes = (end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute) - total_break_duration
    
    # Ensure that there are enough minutes for classes
    if total_available_minutes <= 0 or num_classes <= 0:
        st.error("Insufficient time available for the classes.")
        return pd.DataFrame()  # Return an empty DataFrame if the time is insufficient

    class_duration = total_available_minutes // num_classes
    
    if class_duration <= 0:
        st.error("Class duration must be greater than zero.")
        return pd.DataFrame()  # Return an empty DataFrame if class duration is invalid

    timetable = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    
    for day in timetable:
        used_subjects = set()
        used_faculty = set()
        current_time = start_time
        
        for _ in range(num_classes):
            if current_time >= end_time:
                break
            
            subject = random.choice([subj for subj in subjects if subj not in used_subjects])
            faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
            timetable[day].append({"Time": current_time.strftime("%H:%M"), "Subject": subject, "Faculty": faculty})
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)
        
        # Adding breaks
        for break_time in breaks:
            timetable[day].append({"Time": break_time[0].strftime("%H:%M"), "Subject": "Break", "Faculty": ""})
            current_time += timedelta(minutes=break_time[1])
    
    # Add lab sessions
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        timetable[day].append({"Time": "Lab Session", "Subject": "Lab", "Faculty": ""})
    
    return pd.DataFrame.from_dict({day: timetable[day] for day in timetable}, orient='index')

# Function to export the timetable as a PDF
def export_to_pdf(timetable_df):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    for i, day in enumerate(timetable_df.index):
        pdf_canvas.drawString(100, height - 50 - (i * 100), f"Timetable for {day}")
        y = height - 70 - (i * 100)
        for j, row in enumerate(timetable_df.loc[day]):
            pdf_canvas.drawString(100, y - (j * 20), f"{row['Time']} - {row['Subject']} by {row['Faculty']}")
    
    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

# Sidebar inputs for college timings
start_hour = st.sidebar.number_input("College Start Hour", min_value=1, max_value=12, value=9)
start_minute = st.sidebar.number_input("College Start Minute", min_value=0, max_value=59, value=0)
start_am_pm = st.sidebar.radio("Select AM/PM for Start Time", ["AM", "PM"])

end_hour = st.sidebar.number_input("College End Hour", min_value=1, max_value=12, value=5)
end_minute = st.sidebar.number_input("College End Minute", min_value=0, max_value=59, value=0)
end_am_pm = st.sidebar.radio("Select AM/PM for End Time", ["AM", "PM"])

# Convert to 24-hour format
start_time = time(start_hour + (12 if start_am_pm == "PM" and start_hour < 12 else 0),
                  start_minute)
end_time = time(end_hour + (12 if end_am_pm == "PM" and end_hour < 12 else 0),
                end_minute)

# Break timings input
morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
breaks = [(time(11, 0), morning_break_duration), (time(13, 0), lunch_break_duration)]

# Group name and number of sections
group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

# Manual input for subjects and faculty
num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=5)
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if "faculty_members" not in st.session_state:
    st.session_state.faculty_members = {}

# Manage subject and faculty inputs
for i in range(num_subjects):
    if i >= len(st.session_state.subjects):
        st.session_state.subjects.append("")  # Append empty string for new subjects

    subject_name = st.sidebar.text_input(f"Subject Name {i + 1}", value=st.session_state.subjects[i])
    
    # Store the subject name
    if subject_name:
        st.session_state.subjects[i] = subject_name
    
    # Initialize faculty members for the subject
    if subject_name not in st.session_state.faculty_members:
        st.session_state.faculty_members[subject_name] = []

    # Set min value to 1 and default to 1 if no faculty is present
    num_faculty = st.sidebar.number_input(
        f"Number of Faculty for {subject_name}",
        min_value=1,
        value=max(1, len(st.session_state.faculty_members[subject_name])),  # Ensure at least 1
        key=f"faculty_count_{i}"
    )
    
    faculty_list = []
    for j in range(num_faculty):
        if j >= len(st.session_state.faculty_members[subject_name]):
            st.session_state.faculty_members[subject_name].append("")  # Append empty string for new faculty members

        faculty_name = st.sidebar.text_input(
            f"Faculty Name {j + 1} for {subject_name}",
            value=st.session_state.faculty_members[subject_name][j],
            key=f"faculty_{i}_{j}"
        )
        
        faculty_list.append(faculty_name)

    if subject_name:
        st.session_state.faculty_members[subject_name] = faculty_list

# Generate timetable button
if st.button("Generate Timetable"):
    if not group_name:
        st.error("Please enter a group name.")
    else:
        timetable_df = generate_timetable(start_time, end_time, st.session_state.subjects, st.session_state.faculty_members, breaks)
        if not timetable_df.empty:
            st.write(timetable_df)

            # Button to export the timetable to PDF
            if st.button("Export to PDF"):
                pdf_buffer = export_to_pdf(timetable_df)
                st.download_button("Download PDF", pdf_buffer, "timetable.pdf", "application/pdf")









