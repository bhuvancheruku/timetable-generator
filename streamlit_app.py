from datetime import time, timedelta
import random
import streamlit as st
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    total_break_duration = sum(break_duration for _, break_duration in breaks)

    # Calculate total available minutes for classes
    start_minutes = start_time.hour * 60 + start_time.minute
    end_minutes = end_time.hour * 60 + end_time.minute
    total_available_minutes = end_minutes - start_minutes - total_break_duration

    # Validate the class duration
    if total_available_minutes <= 0 or num_classes <= 0:
        st.error("Insufficient time available for the classes.")
        return pd.DataFrame()

    class_duration = total_available_minutes // num_classes

    timetable = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    
    for day in timetable:
        used_subjects = set()
        used_faculty = set()
        current_time = start_time
        
        # Schedule classes
        for _ in range(num_classes):
            if current_time.hour * 60 + current_time.minute >= end_minutes:
                break
            
            # Randomly assign subject and faculty
            subject = random.choice([subj for subj in subjects if subj not in used_subjects])
            faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
            time_slot = current_time.strftime("%I:%M %p")
            timetable[day][time_slot] = f"{subject} by {faculty}"
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)

        # Insert breaks at specified times
        for break_time, duration in breaks:
            break_slot = break_time.strftime("%I:%M %p")
            timetable[day][break_slot] = "Break"
            current_time += timedelta(minutes=duration)

    # Add lab sessions on random days
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        lab_time = current_time.strftime("%I:%M %p")
        timetable[day][lab_time] = "Lab Session"
    
    # Convert to DataFrame and arrange times as columns
    timetable_df = pd.DataFrame.from_dict(timetable, orient="index").fillna("")
    return timetable_df

# Function to export the timetable as a PDF
def export_to_pdf(timetable_df):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y_offset = 50
    for i, (day, entries) in enumerate(timetable_df.iterrows()):
        pdf_canvas.drawString(100, height - y_offset, f"Timetable for {day}")
        y = height - y_offset - 20
        for time, entry in entries.items():
            pdf_canvas.drawString(100, y, f"{time} - {entry}")
            y -= 20
        y_offset += 120

    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit App
st.title("Timetable Generator")

# Sidebar inputs
start_time_hour = st.sidebar.number_input("Start Hour", min_value=1, max_value=12, value=9)
start_time_minute = st.sidebar.number_input("Start Minute", min_value=0, max_value=59, value=0)
start_time_am_pm = st.sidebar.radio("Start Time AM/PM", options=["AM", "PM"])
start_time = time(start_time_hour % 12 + (12 if start_time_am_pm == "PM" else 0), start_time_minute)

end_time_hour = st.sidebar.number_input("End Hour", min_value=1, max_value=12, value=5)
end_time_minute = st.sidebar.number_input("End Minute", min_value=0, max_value=59, value=0)
end_time_am_pm = st.sidebar.radio("End Time AM/PM", options=["AM", "PM"])
end_time = time(end_time_hour % 12 + (12 if end_time_am_pm == "PM" else 0), end_time_minute)

group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

# Break configuration
no_break = st.sidebar.checkbox("No Breaks")
breaks = []

if not no_break:
    if st.sidebar.checkbox("Add Morning Break"):
        morning_break_time = st.sidebar.time_input("Morning Break Time", value=time(11, 0))
        morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
        breaks.append((morning_break_time, morning_break_duration))

    if st.sidebar.checkbox("Add Lunch Break"):
        lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=time(13, 0))
        lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
        breaks.append((lunch_break_time, lunch_break_duration))

# Subjects and faculty input
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
    
    if subject_name:
        st.session_state.subjects[i] = subject_name
    
    if subject_name not in st.session_state.faculty_members:
        st.session_state.faculty_members[subject_name] = []

    num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, value=1)
    faculty_list = []
    for j in range(num_faculty):
        faculty_name = st.sidebar.text_input(f"Faculty Name {j + 1} for {subject_name}")
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
            st.write("Generated Timetable:")
            st.dataframe(timetable_df)

            # Button to export the timetable to PDF
            if st.button("Export to PDF"):
                pdf_buffer = export_to_pdf(timetable_df)
                st.download_button(label="Download Timetable as PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
