from datetime import time
import tempfile
import random
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_timetable(num_classes, num_days, subjects, faculty_members, start_time, end_time, morning_break_time, afternoon_break_time):
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

            # Add a lab session (every day has a lab session)
            lab_subject = random.choice(subjects)
            lab_faculty = random.choice(faculty_members[lab_subject])
            daily_schedule.append(f"Lab - {lab_subject} ({lab_faculty})")
            used_faculty.add(lab_faculty)
            used_subjects.add(lab_subject)
            current_datetime += timedelta(minutes=60)  # Assuming a lab takes 1 hour
            classes_added += 1

            # Choose subjects and faculty for the remaining classes
            while classes_added < num_classes:
                subject = random.choice([subj for subj in subjects if subj not in used_subjects])
                available_faculty = [fac for fac in faculty_members[subject] if fac not in used_faculty]

                if available_faculty:  # Check if there are available faculty members
                    faculty = random.choice(available_faculty)
                    daily_schedule.append(f"{subject} - {faculty}")

                    used_faculty.add(faculty)
                    used_subjects.add(subject)
                    current_datetime += timedelta(minutes=60)  # Each class takes 1 hour
                    classes_added += 1
                else:
                    # If no faculty available for selected subject, mark this slot as "Free"
                    daily_schedule.append("Free")

                # Stop if we reach end time
                if current_datetime.time() >= end_time:
                    break

        # Fill the rest of the day with "Free" if not enough classes were added
        while len(daily_schedule) < num_classes:
            daily_schedule.append("Free")

        timetable.append(daily_schedule)

    # Create DataFrame for easier viewing and PDF export
    columns = [f"Class {i + 1}" for i in range(num_classes)]
    
    # Ensure all days have the same number of classes
    if all(len(day) == num_classes for day in timetable):
        return pd.DataFrame(timetable, columns=columns)
    else:
        raise ValueError("Not all days have the same number of classes")

# Streamlit UI
st.title("Timetable Generator")
group_name = st.sidebar.text_input("Group Name")
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)
num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=1)

# Store the subjects and faculty members in session state to maintain state across reruns
if 'subjects' not in st.session_state:
    st.session_state.subjects = []
if 'faculty_members' not in st.session_state:
    st.session_state.faculty_members = {}

# Manually input subjects and their faculty
for i in range(num_subjects):
    if i >= len(st.session_state.subjects):
        st.session_state.subjects.append("")  # Append empty string for new subjects
    
    subject_name = st.sidebar.text_input(f"Subject Name {i + 1}", value=st.session_state.subjects[i])
    
    # Store the subject name
    if subject_name:
        st.session_state.subjects[i] = subject_name
    
    # Manage faculty input
    if subject_name not in st.session_state.faculty_members:
        st.session_state.faculty_members[subject_name] = []

    num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, value=len(st.session_state.faculty_members[subject_name]), key=f"faculty_count_{i}")
    
    faculty_list = []
    for j in range(num_faculty):
        if j >= len(st.session_state.faculty_members[subject_name]):
            st.session_state.faculty_members[subject_name].append("")  # Append empty string for new faculty members

        faculty_name = st.sidebar.text_input(f"Faculty Name {j + 1} for {subject_name}", value=st.session_state.faculty_members[subject_name][j], key=f"faculty_{i}_{j}")
        
        faculty_list.append(faculty_name)

    if subject_name:
        st.session_state.faculty_members[subject_name] = faculty_list

# Timings
start_time = st.sidebar.time_input("College Start Time", value=datetime.strptime("09:00", "%H:%M").time())
end_time = st.sidebar.time_input("College End Time", value=datetime.strptime("17:00", "%H:%M").time())
morning_break_time = st.sidebar.time_input("Morning Break Time", value=datetime.strptime("10:30", "%H:%M").time())
afternoon_break_time = st.sidebar.time_input("Afternoon Break Time", value=datetime.strptime("13:00", "%H:%M").time())

if st.button("Generate Timetables"):
    all_timetables = {}
    for section in range(num_sections):
        timetable_df = generate_timetable(5, 6, st.session_state.subjects, st.session_state.faculty_members, start_time, end_time, morning_break_time, afternoon_break_time)
        all_timetables[f"Section {section + 1}"] = timetable_df

    # Display the timetables
    for section, timetable in all_timetables.items():
        st.subheader(section)
        st.dataframe(timetable)

    # Option to export to PDF can be added here

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

