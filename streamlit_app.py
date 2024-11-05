from datetime import time, datetime, timedelta
import random
import streamlit as st
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, room_numbers, num_classes=8, lab_sessions=3):
    if not subjects or all(subj == "" for subj in subjects):
        st.error("Please enter at least one subject.")
        return pd.DataFrame()
    
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
    if end_time <= start_time:
        st.error("End time must be later than start_time.")
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
            room = room_numbers.get(subject, "")
            timetable[day].append({"Time": current_time.strftime("%I:%M %p"), "Subject": subject, "Faculty": faculty, "Room": room})
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)
            
        for break_time, duration in breaks:
            timetable[day].append({"Time": break_time.strftime("%I:%M %p"), "Subject": "Break", "Faculty": "", "Room": ""})
            current_time += timedelta(minutes=duration)
    
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        timetable[day].append({"Time": "Lab Session", "Subject": "Lab", "Faculty": "", "Room": ""})
    
    return pd.DataFrame.from_dict({day: timetable[day] for day in timetable}, orient='index')

# Function to export the timetable as a PDF
def export_to_pdf(timetable_df):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(100, height - 40, "IV Year B. Tech-I Sem Timetable for Academic Year 2024-2025")

    for i, day in enumerate(timetable_df.index):
        pdf_canvas.setFont("Helvetica", 10)
        y_position = height - 70 - (i * 120)
        pdf_canvas.drawString(50, y_position, f"Timetable for {day}")

        table_data = [["Time", "Subject", "Faculty", "Room"]]
        for row in timetable_df.loc[day]:
            table_data.append([row["Time"], row["Subject"], row["Faculty"], row["Room"]])
        
        table = Table(table_data, colWidths=[1.5*inch, 2*inch, 2.5*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        table.wrapOn(pdf_canvas, 50, y_position - 20)
        table.drawOn(pdf_canvas, 50, y_position - 20 - len(table_data)*18)
    
    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

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

# Breaks input
no_break = st.sidebar.checkbox("No Break Present")
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

# Subject and faculty inputs
num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=5)
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if "faculty_members" not in st.session_state:
    st.session_state.faculty_members = {}
if "room_numbers" not in st.session_state:
    st.session_state.room_numbers = {}

for i in range(num_subjects):
    subject_name = st.sidebar.text_input(f"Subject Name {i + 1}", key=f"subject_{i}")
    if subject_name:
        st.session_state.subjects.append(subject_name)
    
    num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, key=f"faculty_count_{i}")
    st.session_state.faculty_members[subject_name] = [
        st.sidebar.text_input(f"Faculty Name {j + 1} for {subject_name}", key=f"faculty_{i}_{j}") for j in range(num_faculty)
    ]
    room_number = st.sidebar.text_input(f"Room Number for {subject_name}", key=f"room_{i}")
    st.session_state.room_numbers[subject_name] = room_number

# Generate timetable button
if st.button("Generate Timetable"):
    if not group_name:
        st.error("Please enter a group name.")
    else:
        timetable_df = generate_timetable(start_time, end_time, st.session_state.subjects, st.session_state.faculty_members, breaks, st.session_state.room_numbers)
        if not timetable_df.empty:
            st.write(timetable_df)

            # Export to PDF
            if st.button("Export to PDF"):
                pdf_buffer = export_to_pdf(timetable_df)
                st.download_button(label="Download PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
