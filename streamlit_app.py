from datetime import time, timedelta
import random
import streamlit as st
import pandas as pd
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

            # Button to export the timetable to PDF
            if st.button("Export to PDF"):
                pdf_buffer = export_to_pdf(timetable_df)
                st.download_button(label="Download Timetable as PDF", data=pdf_buffer, file_name="timetable.pdf", mime="application/pdf")
