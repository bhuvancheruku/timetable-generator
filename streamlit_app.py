import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=5, lab_sessions=3, half_day=False):
    # Check for required inputs
    if not start_time or not end_time:
        st.warning("Please specify both the start and end time.")
        return pd.DataFrame()

    if not subjects:
        st.warning("Please enter at least one subject.")
        return pd.DataFrame()

    if not faculty_members or any(subject not in faculty_members for subject in subjects):
        st.warning("Please provide faculty members for each subject.")
        return pd.DataFrame()

    if not breaks and not half_day:
        st.warning("Please specify break times and durations.")
        return pd.DataFrame()

    # Calculate total break duration
    total_break_duration = sum(break_duration for _, break_duration in breaks if not half_day)
    
    today = datetime.now().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)

    if end_datetime <= start_datetime:
        st.warning("End time must be later than start time.")
        return pd.DataFrame()

    total_available_minutes = (end_datetime - start_datetime).total_seconds() / 60 - total_break_duration
    if total_available_minutes <= 0 or num_classes <= 0:
        st.warning("Insufficient time available for the classes.")
        return pd.DataFrame()

    class_duration = total_available_minutes // num_classes
    if class_duration <= 0:
        st.warning("Class duration must be greater than zero.")
        return pd.DataFrame()

    # Timetable dictionary with days as rows and timings as columns
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    timetable = {day: {f"Class {i+1}": None for i in range(num_classes)} for day in days}
    time_slots = []
    current_time = start_datetime

    # Generate time slots for each class period
    for _ in range(num_classes):
        time_slots.append(current_time.strftime("%I:%M %p"))
        current_time += timedelta(minutes=class_duration)
    
    # Add breaks to time slots if not half-day
    if not half_day:
        for break_time, duration in breaks:
            break_slot = break_time.strftime("%I:%M %p")
            if break_slot not in time_slots:
                time_slots.append(break_slot)

    time_slots = sorted(set(time_slots))  # Sort time slots for proper ordering

    # Fill the timetable with subjects and faculty for each day
    for day in days:
        used_subjects = set()
        used_faculty = set()

        for time_slot in time_slots:
            if time_slot in timetable[day].values():
                continue  # Skip if this time slot is already filled

            if len(used_subjects) < len(subjects):
                subject = random.choice([subj for subj in subjects if subj not in used_subjects])
                faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
                timetable[day][time_slot] = {"Subject": subject, "Faculty": faculty}
                used_subjects.add(subject)
                used_faculty.add(faculty)

    return pd.DataFrame(timetable)

# Function to export the timetable as a PDF
def export_to_pdf(timetable_df):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf_canvas.setFont("Helvetica", 12)

    for i, day in enumerate(timetable_df.index):
        pdf_canvas.drawString(100, height - 50 - (i * 100), f"Timetable for {day}")
        y = height - 70 - (i * 100)
        
        for j, (time_slot, data) in enumerate(timetable_df.loc[day].items()):
            if data is not None:
                subject = data['Subject']
                faculty = data['Faculty']
                pdf_canvas.drawString(100, y - (j * 20), f"{time_slot}: {subject} by {faculty}")

    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

# Sidebar inputs for college timings
start_time_hour = st.sidebar.number_input("College Start Hour", min_value=1, max_value=12, value=9)
start_time_minute = st.sidebar.number_input("College Start Minute", min_value=0, max_value=59, value=0)
start_time_am_pm = st.sidebar.radio("Start Time AM/PM", options=["AM", "PM"])
start_time = datetime.strptime(f"{start_time_hour}:{start_time_minute} {start_time_am_pm}", "%I:%M %p").time()

end_time_hour = st.sidebar.number_input("College End Hour", min_value=1, max_value=12, value=5)
end_time_minute = st.sidebar.number_input("College End Minute", min_value=0, max_value=59, value=0)
end_time_am_pm = st.sidebar.radio("End Time AM/PM", options=["AM", "PM"])
end_time = datetime.strptime(f"{end_time_hour}:{end_time_minute} {end_time_am_pm}", "%I:%M %p").time()

# Group name and number of sections
group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

# Manual input for breaks
no_break = st.sidebar.checkbox("No Break Present")
no_lunch_break = st.sidebar.checkbox("No Lunch Break Present")

breaks = []  # Initialize breaks as an empty list
if not no_break:
    num_breaks = st.sidebar.number_input("Number of Breaks", min_value=0, max_value=2, value=1)

# Collect break timings and durations from user input
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=datetime.strptime("11:00 AM", "%I:%M %p").time())
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=datetime.strptime("1:00 PM", "%I:%M %p").time())
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
                st.download_button(
                    label="Download Timetable PDF",
                    data=pdf_buffer,
                    file_name
