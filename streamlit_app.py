import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=5, num_sections=1, half_day=False):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    timetables = {f"Section {i+1}": {day: [] for day in days} for i in range(num_sections)}
    
    today = datetime.now().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)

    total_minutes = (end_datetime - start_datetime).total_seconds() / 60 - sum(break_info[1] for break_info in breaks)
    class_duration = total_minutes // num_classes

    time_slots = []
    current_time = start_datetime
    for _ in range(num_classes):
        end_time = current_time + timedelta(minutes=class_duration)
        time_slots.append((current_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")))
        current_time = end_time

    if not half_day:
        for break_time, duration in breaks:
            time_slots.append((break_time.strftime("%I:%M %p"), "BREAK"))

    time_slots = sorted(set(time_slots))

    for section in timetables:
        for day in days:
            used_faculty = set()

            for time_slot in time_slots:
                if time_slot[1] == "BREAK":
                    timetables[section][day].append((time_slot, "BREAK", ""))
                    continue
                
                subject = random.choice(subjects)
                available_faculty = [fac for fac in faculty_members[subject] if fac not in used_faculty]
                if not available_faculty:
                    timetables[section][day].append((time_slot, subject, "No Faculty Available"))
                    continue
                
                faculty = random.choice(available_faculty)
                used_faculty.add(faculty)
                timetables[section][day].append((time_slot, subject, faculty))

    return timetables, time_slots

# Function to export timetable as PDF
def export_to_pdf(timetables, time_slots):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    for section, timetable in timetables.items():
        data = [["Day"] + [f"{start} - {end}" if end != "BREAK" else "BREAK" for start, end in time_slots]]
        
        for day, classes in timetable.items():
            row = [day]
            for time_slot, subject, faculty in classes:
                if subject == "BREAK":
                    row.append("BREAK")
                else:
                    row.append(f"{subject}\n{faculty}")
            data.append(row)

        timetable_table = Table(data, colWidths=[50] + [65] * len(time_slots))
        timetable_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(timetable_table)
        elements.append(Table([[""]], colWidths=[1]))  # Add space between sections

    doc.build(elements)
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

start_time = st.sidebar.time_input("College Start Time", value=datetime.strptime("09:00 AM", "%I:%M %p").time())
end_time = st.sidebar.time_input("College End Time", value=datetime.strptime("03:00 PM", "%I:%M %p").time())
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

breaks = []
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=datetime.strptime("11:00 AM", "%I:%M %p").time())
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=datetime.strptime("1:00 PM", "%I:%M %p").time())
    lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
    breaks.append((lunch_break_time, lunch_break_duration))

num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=5)
subjects = []
faculty_members = {}

for i in range(num_subjects):
    subject = st.sidebar.text_input(f"Subject {i + 1}")
    if subject:
        subjects.append(subject)
        num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject}", min_value=1, value=1)
        faculty = [st.sidebar.text_input(f"Faculty {j + 1} for {subject}") for j in range(num_faculty)]
        faculty_members[subject] = faculty

if st.button("Generate Timetable"):
    timetable_data, time_slots = generate_timetable(
        start_time, end_time, subjects, faculty_members, breaks, num_classes=5, num_sections=num_sections
    )
    flat_timetable_df = pd.DataFrame([
        {"Section": section, "Day": day, "Time Slot": time_slot[0] + " - " + time_slot[1] if time_slot[1] != "BREAK" else "BREAK",
         "Subject": subject, "Faculty": faculty}
        for section, days in timetable_data.items()
        for day, classes in days.items()
        for time_slot, subject, faculty in classes
    ])

    # Store timetable data in session state
    st.session_state.timetable_data = timetable_data
    st.session_state.time_slots = time_slots
    st.session_state.flat_timetable_df = flat_timetable_df

    st.write("### Timetable")
    st.dataframe(flat_timetable_df)

# Export PDF button
if 'flat_timetable_df' in st.session_state:
    if st.button("Export to PDF"):
        pdf_buffer = export_to_pdf(st.session_state.timetable_data, st.session_state.time_slots)
        st.download_button("Download Timetable PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
