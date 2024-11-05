pip install reportlab
import streamlit as st
import pandas as pd
import random
from datetime import timedelta, time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

# Function to generate timetable
def generate_timetable(num_classes, num_days, subjects, faculty_members, morning_break_time, afternoon_break_time, lab_sessions):
    timetable = []
    for day in range(num_days):
        daily_schedule = []
        used_faculty = set()
        used_subjects = set()
        
        # Set start time
        current_time = start_time
        classes_added = 0

        while classes_added < num_classes:
            # Check for morning break
            if current_time == morning_break_time:
                daily_schedule.append("Break (10 mins)")
                current_time += timedelta(minutes=morning_break_duration)
                continue

            # Check for afternoon break
            if current_time == afternoon_break_time:
                daily_schedule.append("Lunch Break (1 hr)")
                current_time += timedelta(minutes=afternoon_break_duration)
                continue

            # Check if lab session should be added
            if lab_sessions[day] and classes_added < 3:  # Assume labs are only in the first 3 slots
                lab_subject = random.choice(subjects)
                lab_faculty = random.choice(faculty_members[lab_subject])
                daily_schedule.append(f"Lab - {lab_subject} ({lab_faculty})")
                used_faculty.add(lab_faculty)
                used_subjects.add(lab_subject)
                current_time += timedelta(minutes=class_duration)
                classes_added += 1
                continue

            # Choose a subject and faculty ensuring no overlaps
            subject = random.choice([subj for subj in subjects if subj not in used_subjects])
            faculty = random.choice([fac for fac in faculty_members[subject] if fac not in used_faculty])
            daily_schedule.append(f"{subject} - {faculty}")

            # Update sets to avoid overlap
            used_faculty.add(faculty)
            used_subjects.add(subject)
            current_time += timedelta(minutes=class_duration)
            classes_added += 1

            # Reset if all subjects or faculty are used up
            if len(used_subjects) == len(subjects):
                used_subjects.clear()
            if len(used_faculty) == len(faculty_members[subject]):
                used_faculty.clear()

            # Stop if we reach end time
            if current_time >= end_time:
                break

        timetable.append(daily_schedule)

    # Create DataFrame for easier viewing and PDF export
    columns = [f"Class {i + 1}" for i in range(num_classes)]
    return pd.DataFrame(timetable, columns=columns)

# PDF export function
def export_to_pdf(timetable_df):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        c = canvas.Canvas(temp_pdf.name, pagesize=A4)
        width, height = A4

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 50, "Generated Timetable")

        # Write each day
        y = height - 80
        for i, day in enumerate(timetable_df.index):
            c.setFont("Helvetica", 12)
            c.drawString(30, y, f"Day {i+1}:")
            y -= 20
            for cls in timetable_df.columns:
                c.drawString(50, y, f"{cls}: {timetable_df.loc[day, cls]}")
                y -= 20
            y -= 10  # Space between days
            if y < 50:
                c.showPage()
                y = height - 50

        c.save()
    return temp_pdf.name

# Streamlit Interface
st.title("College Timetable Generator")

# Sidebar for user inputs
st.sidebar.header("Configure Timetable")
start_time = st.sidebar.time_input("College Start Time", value=time(9, 0))
end_time = st.sidebar.time_input("College End Time", value=time(17, 0))

morning_break_time = st.sidebar.time_input("Morning Break Start", value=time(10, 30))
morning_break_duration = 10  # Fixed 10 minutes

afternoon_break_time = st.sidebar.time_input("Lunch Break Start", value=time(13, 0))
afternoon_break_duration = 60  # Fixed 1 hour

num_classes = st.sidebar.number_input("Number of Classes per Day", min_value=1, max_value=8, value=8)
num_days = 6  # Fixed 6 days a week

# Input subjects and faculty
st.sidebar.write("Subjects and Faculty Members")
subjects = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
faculty_members = {
    "Math": ["Faculty 1", "Faculty 2"],
    "Physics": ["Faculty 3", "Faculty 4"],
    "Chemistry": ["Faculty 5", "Faculty 6"],
    "Biology": ["Faculty 7", "Faculty 8"],
    "Computer Science": ["Faculty 9", "Faculty 10"]
}

# Lab sessions configuration (3 labs per week)
lab_sessions = [True, True, True, False, False, False]  # Lab sessions on first 3 days of the week

class_duration = 50  # Each class duration in minutes

# Generate timetable
timetable_df = generate_timetable(
    num_classes=num_classes,
    num_days=num_days,
    subjects=subjects,
    faculty_members=faculty_members,
    morning_break_time=morning_break_time,
    afternoon_break_time=afternoon_break_time,
    lab_sessions=lab_sessions
)

# Display generated timetable
st.write("## Generated Timetable")
st.dataframe(timetable_df)

# PDF Export Button
if st.button("Export Timetable to PDF"):
    pdf_path = export_to_pdf(timetable_df)
    st.success("Timetable exported to PDF successfully.")
    with open(pdf_path, "rb") as file:
        st.download_button("Download PDF", file, file_name="timetable.pdf")
