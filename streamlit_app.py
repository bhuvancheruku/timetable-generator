from datetime import time
import tempfile
import random
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_timetable(num_classes, num_days, subjects, faculty_members, start_time, end_time, morning_break_time, afternoon_break_time, lab_sessions):
    timetable = []
    for day in range(num_days):
        daily_schedule = []
        used_faculty = set()
        used_subjects = set()
        
        current_datetime = datetime.combine(datetime.today(), start_time)
        classes_added = 0

        while classes_added < num_classes:
            # Check for morning break
            if current_datetime.time() == morning_break_time:
                daily_schedule.append("Break (10 mins)")
                current_datetime += timedelta(minutes=10)
                continue

            # Check for afternoon break
            if current_datetime.time() == afternoon_break_time:
                daily_schedule.append("Lunch Break (1 hr)")
                current_datetime += timedelta(hours=1)
                continue

            # Check if lab session should be added
            if lab_sessions[day] and classes_added < 3:
                lab_subject = random.choice(subjects)
                lab_faculty = random.choice(faculty_members[lab_subject])
                daily_schedule.append(f"Lab - {lab_subject} ({lab_faculty})")
                used_faculty.add(lab_faculty)
                used_subjects.add(lab_subject)
                current_datetime += timedelta(minutes=60)
                classes_added += 1
                continue

            # Choose a subject and faculty ensuring no overlaps
            subject = random.choice([subj for subj in subjects if subj not in used_subjects])
            available_faculty = [fac for fac in faculty_members[subject] if fac not in used_faculty]

            if available_faculty:  # Check if there are available faculty members
                faculty = random.choice(available_faculty)
                daily_schedule.append(f"{subject} - {faculty}")

                used_faculty.add(faculty)
                used_subjects.add(subject)
                current_datetime += timedelta(minutes=60)
                classes_added += 1
            else:
                daily_schedule.append("Free")
                
            # Reset if all subjects or faculty are used up
            if len(used_subjects) == len(subjects):
                used_subjects.clear()
            if len(used_faculty) == len(faculty_members[subject]):
                used_faculty.clear()

            # Stop if we reach end time
            if current_datetime.time() >= end_time:
                break

        # Fill the rest of the day with "Free" if not enough classes were added
        while len(daily_schedule) < num_classes:
            daily_schedule.append("Free")

        # Debug: Print daily schedule to check its length
        print(f"Day {day + 1} schedule: {daily_schedule}")  # Print the daily schedule

        timetable.append(daily_schedule)

    # Create DataFrame for easier viewing and PDF export
    columns = [f"Class {i + 1}" for i in range(num_classes)]
    
    # Ensure all days have the same number of classes
    if all(len(day) == num_classes for day in timetable):
        return pd.DataFrame(timetable, columns=columns)
    else:
        raise ValueError("Not all days have the same number of classes")




# Streamlit UI code
st.title("College Timetable Generator")

# Get user input for basic settings
num_days = st.sidebar.number_input("Enter number of days (6 for Mon-Sat)", min_value=1, max_value=6, value=6)
num_classes = st.sidebar.number_input("Enter number of classes per day", min_value=1, max_value=10, value=8)

# Input start and end times for college day
start_time = st.sidebar.time_input("College Start Time", value=time(9, 0))
end_time = st.sidebar.time_input("College End Time", value=time(17, 0))

# Input break times
morning_break_time = st.sidebar.time_input("Morning Break Time", value=time(11, 0))
afternoon_break_time = st.sidebar.time_input("Lunch Break Time", value=time(13, 0))

# **Faculty and Subject Input Options**

# Option 1: Using individual inputs
subjects = {}
st.subheader("Enter Subjects and Faculty")

num_subjects = st.sidebar.number_input("Enter the number of subjects", min_value=1, max_value=10, value=5)

for i in range(num_subjects):
    subject_name = st.text_input(f"Subject {i + 1} Name", key=f"subject_{i}")
    faculty_1 = st.text_input(f"Faculty 1 for {subject_name}", key=f"faculty1_{i}")
    faculty_2 = st.text_input(f"Faculty 2 for {subject_name}", key=f"faculty2_{i}")
    subjects[subject_name] = [faculty_1, faculty_2]

# Option 2: Using bulk input (uncomment to use)
# st.subheader("Bulk Entry for Subjects and Faculty")
# st.write("Enter subjects and faculty in the following format:")
# st.code("Subject Name - Faculty1, Faculty2\nExample:\nMath - John Doe, Jane Doe")
# bulk_input = st.text_area("Enter Subjects and Faculty Members (one per line)")
# if bulk_input:
#     subjects = {}
#     lines = bulk_input.split('\n')
#     for line in lines:
#         if '-' in line:
#             subject, faculty_str = line.split('-')
#             subject = subject.strip()
#             faculty_list = [name.strip() for name in faculty_str.split(',')]
#             subjects[subject] = faculty_list

# Input lab sessions
lab_sessions = [st.checkbox(f"Lab session on Day {i + 1}") for i in range(num_days)]

# Generate the timetable
if st.button("Generate Timetable"):
    timetable_df = generate_timetable(
        num_classes, num_days, list(subjects.keys()), subjects, 
        start_time, end_time, morning_break_time, afternoon_break_time, lab_sessions
    )
    st.subheader("Generated Timetable")
    st.dataframe(timetable_df)

    # Export to PDF
    if st.button("Export to PDF"):
        pdf_path = "/tmp/timetable.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.drawString(100, 800, "Generated Timetable")
        
        y_position = 750
        for index, row in timetable_df.iterrows():
            row_text = f"Day {index + 1}: " + ", ".join(row)
            c.drawString(100, y_position, row_text)
            y_position -= 20
        
        c.save()
        with open(pdf_path, "rb") as pdf_file:
            st.download_button(label="Download Timetable as PDF", data=pdf_file, file_name="timetable.pdf")

