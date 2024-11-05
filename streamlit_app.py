import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Function to generate the timetable
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=5, num_sections=1, half_day=False):
    # Initialize the timetable structure with days and sections
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    timetables = {f"Section {i+1}": {day: [] for day in days} for i in range(num_sections)}
    
    today = datetime.now().date()
    start_datetime = datetime.combine(today, start_time)
    end_datetime = datetime.combine(today, end_time)

    # Calculate total available time minus breaks
    total_minutes = (end_datetime - start_datetime).total_seconds() / 60 - sum(break_info[1] for break_info in breaks)
    class_duration = total_minutes // num_classes

    # Generate time slots
    time_slots = []
    current_time = start_datetime
    for _ in range(num_classes):
        end_time = current_time + timedelta(minutes=class_duration)
        time_slots.append((current_time.strftime("%I:%M %p"), end_time.strftime("%I:%M %p")))
        current_time = end_time

    # Include breaks in time slots
    if not half_day:
        for break_time, duration in breaks:
            time_slots.append((break_time.strftime("%I:%M %p"), "BREAK"))

    # Sort and structure the time slots
    time_slots = sorted(set(time_slots))

    # Fill the timetable with subjects and faculty for each section
    for section in timetables:
        for day in days:
            used_faculty = set()

            for time_slot in time_slots:
                if time_slot[1] == "BREAK":
                    timetables[section][day].append((time_slot, "BREAK", ""))
                    continue
                
                # Randomly select subject and ensure no faculty overlaps
                subject = random.choice(subjects)
                available_faculty = [fac for fac in faculty_members[subject] if fac not in used_faculty]
                if not available_faculty:
                    timetables[section][day].append((time_slot, subject, "No Faculty Available"))
                    continue
                
                faculty = random.choice(available_faculty)
                used_faculty.add(faculty)
                
                # Store in the timetable
                timetables[section][day].append((time_slot, subject, faculty))

    return timetables, time_slots

# Function to export timetable as PDF
def export_to_pdf(timetables, time_slots):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf_canvas.setFont("Helvetica", 10)

    start_x, start_y = 50, height - 40
    row_height = 20

    for section, timetable in timetables.items():
        pdf_canvas.drawString(start_x, start_y, f"Timetable for {section}")
        start_y -= 30

        # Draw header row with time slots
        pdf_canvas.drawString(start_x, start_y, "Day")
        for i, (start, end) in enumerate(time_slots):
            slot_text = f"{start} - {end}" if end != "BREAK" else "BREAK"
            pdf_canvas.drawString(start_x + 100 + i * 100, start_y, slot_text)

        # Populate each day with classes
        for day, classes in timetable.items():
            start_y -= row_height
            pdf_canvas.drawString(start_x, start_y, day)

            for i, (time_slot, subject, faculty) in enumerate(classes):
                class_text = f"{subject} - {faculty}" if subject != "BREAK" else "BREAK"
                pdf_canvas.drawString(start_x + 100 + i * 100, start_y, class_text)

            start_y -= 10

        start_y -= 40

    pdf_canvas.save()
    buffer.seek(0)
    return buffer

# Streamlit app
st.title("Timetable Generator")

# Sidebar inputs for college timings
start_time = st.sidebar.time_input("College Start Time", value=datetime.strptime("09:00 AM", "%I:%M %p").time())
end_time = st.sidebar.time_input("College End Time", value=datetime.strptime("03:00 PM", "%I:%M %p").time())
group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)

# Break configuration
breaks = []
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=datetime.strptime("11:00 AM", "%I:%M %p").time())
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=datetime.strptime("1:00 PM", "%I:%M %p").time())
    lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
    breaks.append((lunch_break_time, lunch_break_duration))

# Subjects and faculty inputs
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

# Generate timetable button
if st.button("Generate Timetable"):
    timetable_data, time_slots = generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=5, num_sections=num_sections)
    for section, timetable in timetable_data.items():
        st.write(f"### {section}")
        st.dataframe(pd.DataFrame(timetable))

    # Button to export timetable to PDF
    if st.button("Export to PDF"):
        pdf_buffer = export_to_pdf(timetable_data, time_slots)
        st.download_button("Download Timetable PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
