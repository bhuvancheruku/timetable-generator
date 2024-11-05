import streamlit as st
import pandas as pd
import random
from collections import deque
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Initialize Streamlit app
st.title("Timetable Generator with Faculty Constraint Check")

# Input configurations
start_time = st.sidebar.time_input("College Start Time", value=datetime.strptime("09:00 AM", "%I:%M %p").time())
end_time = st.sidebar.time_input("College End Time", value=datetime.strptime("03:00 PM", "%I:%M %p").time())
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)
num_classes = st.sidebar.number_input("Number of Classes per Day", min_value=1, value=5)

# Get subjects and faculty information
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

# Break inputs
breaks = []
if st.sidebar.checkbox("Add Breaks"):
    break_time = st.sidebar.time_input("Break Time", value=datetime.strptime("11:00 AM", "%I:%M %p").time())
    break_duration = st.sidebar.number_input("Break Duration (minutes)", min_value=1, value=10)
    breaks.append((break_time, break_duration))

# Timetable generation function with BFS
def generate_timetable_bfs(start_time, end_time, subjects, faculty_members, breaks, num_classes, num_sections):
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    timetables = {f"Section {i+1}": {day: [] for day in days} for i in range(num_sections)}
    queue = deque([(timetables, set())])  # Queue with timetable and used faculty for tracking
    
    today = datetime.now().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)
    class_duration = ((end_datetime - start_datetime).seconds // 60 - sum(duration for _, duration in breaks)) // num_classes
    
    time_slots = []
    current_time = start_datetime
    for _ in range(num_classes):
        end_time_slot = current_time + timedelta(minutes=class_duration)
        time_slots.append((current_time.strftime("%I:%M %p"), end_time_slot.strftime("%I:%M %p")))
        current_time = end_time_slot

    for section in timetables:
        for day in days:
            available_subjects = subjects[:]
            used_faculty = set()
            daily_schedule = []
            
            for time_slot in time_slots:
                while available_subjects:
                    subject = random.choice(available_subjects)
                    available_subjects.remove(subject)
                    possible_faculty = [fac for fac in faculty_members[subject] if fac not in used_faculty]
                    if possible_faculty:
                        faculty = random.choice(possible_faculty)
                        used_faculty.add(faculty)
                        daily_schedule.append((time_slot, subject, faculty))
                        break
                    else:
                        # Reset the subjects if constraints fail and recheck with BFS approach
                        available_subjects = subjects[:]
            timetables[section][day] = daily_schedule

    return timetables, time_slots

# PDF Export Function
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
        timetable_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
        elements.append(timetable_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# Run Timetable Generation
if st.button("Generate Timetable"):
    timetable_data, time_slots = generate_timetable_bfs(
        start_time, end_time, subjects, faculty_members, breaks, num_classes, num_sections
    )
    flat_timetable_df = pd.DataFrame([
        {"Section": section, "Day": day, "Time Slot": f"{start} - {end}", "Subject": subject, "Faculty": faculty}
        for section, days in timetable_data.items()
        for day, classes in days.items()
        for (start, end), subject, faculty in classes
    ])
    st.write("### Timetable")
    st.dataframe(flat_timetable_df)

    if st.button("Export to PDF"):
        pdf_buffer = export_to_pdf(timetable_data, time_slots)
        st.download_button("Download Timetable PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
