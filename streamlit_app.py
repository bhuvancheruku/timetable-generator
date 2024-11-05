from datetime import time, datetime, timedelta
import random
import streamlit as st
import pandas as pd
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# Ensure session state variables are initialized
if "subjects" not in st.session_state:
    st.session_state.subjects = []
if "faculty_members" not in st.session_state:
    st.session_state.faculty_members = {}

# Function to generate the timetable for one section
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    total_break_duration = sum(break_duration for _, break_duration in breaks)
    
    if end_time <= start_time:
        st.error("End time must be later than start time.")
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
            timetable[day].append({"Time": current_time.strftime("%I:%M %p"), "Subject": subject, "Faculty": faculty})
            used_subjects.add(subject)
            used_faculty.add(faculty)
            current_time += timedelta(minutes=class_duration)
            
        for break_time, duration in breaks:
            timetable[day].append({"Time": break_time.strftime("%I:%M %p"), "Subject": "Break", "Faculty": ""})
            current_time += timedelta(minutes=duration)
    
    lab_days = random.sample(list(timetable.keys()), lab_sessions)
    for day in lab_days:
        timetable[day].append({"Time": "Lab Session", "Subject": "Lab", "Faculty": ""})
    
    return pd.DataFrame.from_dict({day: timetable[day] for day in timetable}, orient='index')

# Function to generate unique timetables for each section
def generate_multiple_timetables(num_sections, start_time, end_time, subjects, faculty_members, breaks, num_classes=8, lab_sessions=3):
    all_timetables = []
    faculty_schedule = {day: {} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]}

    for section in range(num_sections):
        unique_timetable_generated = False
        attempts = 0
        while not unique_timetable_generated and attempts < 10:
            attempts += 1
            timetable_df = generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes, lab_sessions)
            if not timetable_df.empty:
                conflict = False
                for day in faculty_schedule:
                    for entry in timetable_df.loc[day]:
                        time_slot = entry['Time']
                        faculty = entry['Faculty']
                        if faculty and time_slot in faculty_schedule[day] and faculty in faculty_schedule[day][time_slot]:
                            conflict = True
                            break
                    if conflict:
                        break
                
                if not conflict:
                    all_timetables.append(timetable_df)
                    for day in faculty_schedule:
                        for entry in timetable_df.loc[day]:
                            time_slot = entry['Time']
                            faculty = entry['Faculty']
                            if faculty:
                                if time_slot not in faculty_schedule[day]:
                                    faculty_schedule[day][time_slot] = set()
                                faculty_schedule[day][time_slot].add(faculty)
                    unique_timetable_generated = True

    if len(all_timetables) < num_sections:
        st.error("Could not generate unique timetables for all sections.")
    return all_timetables

# Function to export multiple timetables as a PDF
def export_to_pdf(timetables, num_sections):
    buffer = io.BytesIO()
    pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    pdf_canvas.setFont("Helvetica-Bold", 12)
    pdf_canvas.drawString(100, height - 40, "IV Year B. Tech-I Sem Timetable for Academic Year 2024-2025")

    y_offset = 100
    for section_idx, timetable_df in enumerate(timetables):
        pdf_canvas.setFont("Helvetica-Bold", 10)
        pdf_canvas.drawString(50, height - y_offset, f"Timetable for Section {section_idx + 1}")
        y_offset += 20

        for day in timetable_df.index:
            pdf_canvas.setFont("Helvetica", 10)
            pdf_canvas.drawString(50, height - y_offset, f"Day: {day}")

            table_data = [["Time", "Subject", "Faculty"]]
            for row in timetable_df.loc[day]:
                table_data.append([row["Time"], row["Subject"], row["Faculty"]])
            
            table = Table(table_data, colWidths=[1.5*inch, 2*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            table.wrapOn(pdf_canvas, 50, height - y_offset - 20)
            table.drawOn(pdf_canvas, 50, height - y_offset - 20 - len(table_data)*18)
            y_offset += len(table_data) * 20 + 40

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

# Breaks and subjects/faculty input (similar to previous code, omitted for brevity)

# Generate timetables and export to PDF
if st.button("Generate Timetables"):
    timetables = generate_multiple_timetables(num_sections, start_time, end_time, st.session_state.subjects, st.session_state.faculty_members, breaks)
    if timetables:
        if st.button("Export to PDF"):
            pdf_buffer = export_to_pdf(timetables, num_sections)
            st.download_button(label="Download PDF", data=pdf_buffer, file_name="timetables.pdf", mime="application/pdf")

