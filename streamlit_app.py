import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta, time

def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
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

    if not breaks:
        st.warning("Please specify break times and durations.")
        return pd.DataFrame()

    # Calculate total break duration
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
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

    timetable = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}
    
    for day in timetable:
        used_subjects = set()
        used_faculty = set()
        current_time = start_datetime
        
        for _ in range(num_classes):
            if current_time >= end_datetime:
                break
            
            # Check if all subjects have been used; reset if so
            if len(used_subjects) == len(subjects):
                used_subjects.clear()
                
            # Select a subject that hasn't been used yet
            available_subjects = [subj for subj in subjects if subj not in used_subjects]
            if not available_subjects:
                st.warning("No subjects available to assign.")
                return pd.DataFrame()

            subject = random.choice(available_subjects)
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
    
    timetable_df = pd.DataFrame(columns=["Day", "Time", "Subject", "Faculty"])
    for day, entries in timetable.items():
        for entry in entries:
            timetable_df = timetable_df.append({"Day": day, "Time": entry["Time"], "Subject": entry["Subject"], "Faculty": entry["Faculty"]}, ignore_index=True)
    
    return timetable_df

# Streamlit UI
st.title("Timetable Generator")

# Input fields
start_time = st.time_input("Start Time")
end_time = st.time_input("End Time")

num_subjects = st.sidebar.number_input("Number of Subjects", min_value=1, value=1)
subjects = []
faculty_members = {}
for i in range(num_subjects):
    subject_name = st.sidebar.text_input(f"Subject {i + 1} Name")
    if subject_name:
        subjects.append(subject_name)
        num_faculty = st.sidebar.number_input(f"Number of Faculty for {subject_name}", min_value=1, value=1)
        faculty_members[subject_name] = [st.sidebar.text_input(f"Faculty {j + 1} for {subject_name}") for j in range(num_faculty)]

num_breaks = st.sidebar.number_input("Number of Breaks", min_value=0, value=1)
breaks = []
for i in range(num_breaks):
    break_time = st.sidebar.time_input(f"Break {i + 1} Time")
    break_duration = st.sidebar.number_input(f"Break {i + 1} Duration (minutes)", min_value=1, value=10)
    breaks.append((break_time, break_duration))

if st.button("Generate Timetable"):
    timetable_df = generate_timetable(start_time, end_time, subjects, faculty_members, breaks)
    if not timetable_df.empty:
        st.write("Generated Timetable:")
        st.dataframe(timetable_df)
