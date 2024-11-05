import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import random
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    # Calculate total break duration
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
    # Convert start and end times to datetime objects for easier calculations
    today = datetime.now().date()  # Use today's date for a base datetime
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    
    # Validate that end_time is later than start_time
    if end_datetime <= start_datetime:
        st.error("End time must be later than start time.")
        return pd.DataFrame()  # Return an empty DataFrame if the times are invalid

    # Calculate total available minutes for classes
    total_available_minutes = (end_datetime - start_datetime).total_seconds() / 60 - total_break_duration
    
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
        current_time = start_datetime  # Start from the initial datetime
        
        for _ in range(num_classes):
            if current_time >= end_datetime:
                break
            
            subject = random.choice([subj for subj in subjects if subj not in used_subjects])
            faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
            timetable[day].append({"Time": current_time.strftime("%I:%M %p"), "Subject": subject, "Faculty": faculty})
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)
        
        # Adding breaks
        for break_time, duration in breaks:
            current_time += timedelta(minutes=duration)
            timetable[day].append({"Time": break_time.strftime("%I:%M %p"), "Subject": "Break", "Faculty": ""})
    
    # Add lab sessions
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        timetable[day].append({"Time": "Lab Session", "Subject": "Lab", "Faculty": ""})
    
    # Convert the dictionary to a DataFrame for display
    timetable_df = pd.DataFrame(columns=["Day", "Time", "Subject", "Faculty"])
    for day, entries in timetable.items():
        for entry in entries:
            timetable_df = timetable_df.append({"Day": day, "Time": entry["Time"], "Subject": entry["Subject"], "Faculty": entry["Faculty"]}, ignore_index=True)
    
    return timetable_df

# Function to export the timetable as a PDF
def export_to_pdf(timetable_df):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Write timetable information into the PDF
    y = height - 50
    for day, group in timetable_df.groupby("Day"):
        pdf_canvas.drawString(100, y, f"Timetable for {day}")
        y -= 20
        for _, row in group.iterrows():
            pdf_canvas.drawString(100, y, f"{row['Time']} - {row['Subject']} by {row['Faculty']}")
            y -= 15
            if y < 40:  # Move to a new page if we reach the bottom
                pdf_canvas.showPage()
                y = height - 50
    
    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

# Sidebar inputs for college timings
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

# Manual input for breaks
breaks = []
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=time(11, 0))
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=time(13, 0))
    lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
    breaks.append((lunch_break_time, lunch_break_duration))

# Manual input for subjects and faculty
num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=5)
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if "faculty_members" not in st.session_state:
    st.session_state.faculty_members = {}

# Manage subject and faculty inputs
for i in range(num_subjects):
    subject_name = st.sidebar.text_input(f"Subject Name {i + 1}", key=f"subject_{i}")
    if subject_name:
        st.session_state.subjects.append(subject_name)
    
    num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, value=1, key=f"faculty_count_{i}")
    faculty_list = []
    for j in range(num_faculty):
        faculty_name = st.sidebar.text_input(f"Faculty Name {j + 1} for {subject_name}", key=f"faculty_{i}_{j}")
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
                st.download_button("Download Timetable PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
