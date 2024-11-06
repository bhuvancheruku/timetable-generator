import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

# Style adjustments
st.markdown("""
    <style>
    body {
        background-color: #1f2335;
        color: #a9b1d6;
        font-family: Arial, sans-serif;
    }
    .main-title {
        font-size: 3em;
        color: #7aa2f7;
        text-align: center;
        margin-top: 20px;
    }
    .team-section {
        display: flex;
        justify-content: space-around;
        margin: 20px 0;
        background: rgba(35, 38, 55, 0.5);
        padding: 15px;
        border-radius: 8px;
    }
    .team-member {
        text-align: center;
    }
    .team-member img {
        border-radius: 50%;
        width: 100px;
        height: 100px;
        border: 2px solid #7aa2f7;
    }
    .team-member p {
        color: #c3e88d;
        font-size: 1.2em;
    }
    .scroll-frame {
        background: rgba(35, 38, 55, 0.7);
        padding: 20px;
        border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and Home Page with Team Section
st.markdown('<div class="main-title">Timetable Generator</div>', unsafe_allow_html=True)
st.markdown("<div class='team-section'>", unsafe_allow_html=True)

# Team images (Replace these with actual image paths or URLs for each team member)
team_images = ["path_to_image1.jpg", "path_to_image2.jpg", "path_to_image3.jpg", "path_to_image4.jpg", "path_to_image5.jpg"]
team_names = ["Member 1", "Member 2", "Member 3", "Member 4", "Member 5"]

# Display team members horizontally
for img, name in zip(team_images, team_names):
    st.markdown(f"""
    <div class="team-member">
        <img src="{img}" alt="{name}">
        <p>{name}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Scroll down to Timetable Generation Section
st.markdown('<div class="scroll-frame">', unsafe_allow_html=True)

# Timetable Generation Section
st.header("Generate Timetable")

# Sidebar Inputs
branch_name = st.sidebar.text_input("Branch Name")
start_time = st.sidebar.time_input("College Start Time", value=datetime.strptime("09:00 AM", "%I:%M %p").time())
end_time = st.sidebar.time_input("College End Time", value=datetime.strptime("03:00 PM", "%I:%M %p").time())
num_sections = st.sidebar.number_input("Number of Sections", min_value=1, value=1)
num_classes = st.sidebar.number_input("Number of Classes per Day", min_value=1, value=5)

# Allow custom break times
breaks = []
if st.sidebar.checkbox("Add Morning Break"):
    morning_break_time = st.sidebar.time_input("Morning Break Time", value=datetime.strptime("11:00 AM", "%I:%M %p").time())
    morning_break_duration = st.sidebar.number_input("Morning Break Duration (minutes)", min_value=1, value=10)
    breaks.append((morning_break_time, morning_break_duration))

if st.sidebar.checkbox("Add Lunch Break"):
    lunch_break_time = st.sidebar.time_input("Lunch Break Time", value=datetime.strptime("1:00 PM", "%I:%M %p").time())
    lunch_break_duration = st.sidebar.number_input("Lunch Break Duration (minutes)", min_value=1, value=60)
    breaks.append((lunch_break_time, lunch_break_duration))

# Subjects and Faculty Inputs
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

# Timetable Generation Logic
def generate_timetable(start_time, end_time, subjects, faculty_members, breaks, num_classes=5, num_sections=1):
    # Define timetable generation logic here
    # Placeholder function
    timetables = {}  # Generate timetables based on provided logic
    time_slots = []  # Generate time slots based on provided logic
    return timetables, time_slots

if st.button("Generate Timetable"):
    if not branch_name:
        st.warning("Please provide a branch name.")
    elif not subjects:
        st.warning("Please provide at least one subject.")
    elif not all(faculty_members.get(sub) for sub in subjects):
        st.warning("Please ensure all subjects have at least one faculty member.")
    else:
        timetable_data, time_slots = generate_timetable(
            start_time, end_time, subjects, faculty_members, breaks, num_classes=num_classes, num_sections=num_sections
        )

        flat_timetable_df = pd.DataFrame([ 
            {"Branch": branch_name, "Section": section, "Day": day,
             "Time Slot": f"{time_slot[0]} - {time_slot[1]}" if time_slot[1] != "BREAK" else "BREAK",
             "Subject": subject, "Faculty": faculty}
            for section, days in timetable_data.items()
            for day, classes in days.items()
            for time_slot, subject, faculty in classes
        ])

        st.session_state.timetable_data = timetable_data
        st.session_state.time_slots = time_slots
        st.session_state.flat_timetable_df = flat_timetable_df

        st.write("### Timetable")
        st.dataframe(flat_timetable_df)

# PDF Export Function
def export_to_pdf(timetables, time_slots, branch_name):
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

if 'flat_timetable_df' in st.session_state:
    if st.button("Export to PDF"):
        pdf_buffer = export_to_pdf(st.session_state.timetable_data, st.session_state.time_slots, branch_name)
        st.download_button("Download Timetable PDF", data=pdf_buffer, file_name=f"{branch_name}_timetable.pdf", mime="application/pdf")

st.markdown("</div>", unsafe_allow_html=True)
