import streamlit as st
import pandas as pd
import io
# from utils import *

helper = Helper()

# Initialize session state variables if they don't exist
if 'initial_render' not in st.session_state:
    st.session_state.initial_render = True
if 'doctor' not in st.session_state:
    st.session_state.doctor = False
if 'patient' not in st.session_state:
    st.session_state.patient = False
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient_data" not in st.session_state:
    st.session_state.patient_data = {}

def set_patient_mode():
    st.session_state.patient = True
    st.session_state.doctor = False
    st.session_state.initial_render = False
    st.session_state.form_submitted = False
    st.session_state.messages = []
    st.session_state.patient_data = {}

def set_doctor_mode():
    st.session_state.doctor = True
    st.session_state.patient = False
    st.session_state.initial_render = False

def validate_form_data():
    required_fields = {
        "name": st.session_state.name,
        "age": st.session_state.age,
        "gender": st.session_state.gender,
        "blood_group": st.session_state.blood_group,
        "symptoms": st.session_state.symptoms
    }
    
    return all([
        bool(required_fields["name"]),
        required_fields["age"] > 0,
        required_fields["gender"] != "Select",
        required_fields["blood_group"] != "Select",
        bool(required_fields["symptoms"].strip())
    ])

def submit_form():
    try:
        st.session_state.patient_data = {
            "name": st.session_state.name,
            "age": st.session_state.age,
            "gender": st.session_state.gender,
            "height": st.session_state.height if st.session_state.height else "Not Provided",
            "weight": st.session_state.weight if st.session_state.weight else "Not Provided",
            "blood_group": st.session_state.blood_group,
            "symptoms": st.session_state.symptoms,
            "medical_history": st.session_state.medical_history if st.session_state.medical_history else "None",
            "medications": st.session_state.medications if st.session_state.medications else "None",
            "extra_details": st.session_state.extra_details if st.session_state.extra_details else "None"
        }
        st.session_state.form_submitted = True
        st.session_state.messages = []
        
        # Get initial AI response
        initial_response = helper.ask_doctor(
            patient_data=st.session_state.patient_data, 
            conversation=[]
        )
        st.session_state.messages.append({
            "role": "assistant", 
            "content": initial_response
        })
        return True
    except Exception as e:
        st.error(f"Error submitting form: {str(e)}")
        return False

# Page configuration
st.set_page_config(page_title="DOCTOR-AI")

# Custom CSS (same as before)
st.markdown("""
    <style>
    .box-container {
        background-color: transparent;
        border-radius: 10px;
        padding: 30px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px #a2a2a2 solid;
    }
    .box-header {
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 15px;
        color: red;
        transition: color 0.3s ease;
    }
    .box-description {
        font-size: 18px;
        color: #fff;
        line-height: 1.5;
        transition: color 0.3s ease;
    }
    .stTextInput > div > div > input {
        max-width: 100%;
    }
    .stTextArea > div > div > textarea {
        max-width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Main interface
if st.session_state.initial_render:
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("For Individual Patients", key="patient_button", use_container_width=True, on_click=set_patient_mode):
            pass
        st.markdown("""
            <div class="box-container">
                <div class="box-description">
                    Diagonose your disease and generate a prescription
                    with medications for that before consulting a doctor. 
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("For Doctors", key="doctor_button", use_container_width=True, on_click=set_doctor_mode):
            pass
        st.markdown("""
            <div class="box-container">
                <div class="box-description">
                    Get a Differential Diagonosis for the Patient profile
                    along with probable medications.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("""
        <div class="box-header">
            Do not consume any medicine prescribed by the ai without consulting a doctor.
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.patient:
    st.title("DOCTOR-AI Chat")
    

    if not st.session_state.form_submitted:
        with st.form(key='patient_form'):
            st.markdown("### Please fill in your details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.text_input("Full Name", key="name")
                st.number_input("Age", min_value=0, max_value=120, key="age")
                st.selectbox("Gender", ["Select", "Male", "Female", "Other"], key="gender")
                
            with col2:
                st.text_input("Height (in cm)", key="height", placeholder="optional")
                st.text_input("Weight (in kg)", key="weight", placeholder="optional")
                st.selectbox("Blood Group", ["Select", "A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Not Known"], key="blood_group")
            
            st.markdown("### Medical Information")
            st.text_area("Current Symptoms", key="symptoms")
            st.text_area("Medical History", key="medical_history", placeholder="optional")
            st.text_area("Current Medications", key="medications", placeholder="optional")
            st.text_area("Extra Details", key="extra_details", placeholder="optional")
            
            submit_button = st.form_submit_button("Continue to Chat")
            
            if submit_button:
                if validate_form_data():
                    if submit_form():
                        st.rerun()
                else:
                    st.error("Please fill in all required fields.")

    else:
        # Patient Details Expander
        with st.expander("Patient Details", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Full Name:** {st.session_state.patient_data['name']}")
                st.markdown(f"**Age:** {st.session_state.patient_data['age']} years")
                st.markdown(f"**Gender:** {st.session_state.patient_data['gender']}")
            with col2:
                st.markdown(f"**Height:** {st.session_state.patient_data['height']}")
                st.markdown(f"**Weight:** {st.session_state.patient_data['weight']}")
                st.markdown(f"**Blood Group:** {st.session_state.patient_data['blood_group']}")

        with st.expander("Patient Issues", expanded=False):
            st.markdown("**Current Symptoms:**")
            st.text(st.session_state.patient_data['symptoms'])

            st.markdown("---")
            st.markdown("**Medical History:**")
            st.text(st.session_state.patient_data['medical_history'])

            st.markdown("---")
            st.markdown("**Current Medications:**")
            st.text(st.session_state.patient_data['medications'])

            st.markdown("---")
            st.markdown("**Extra Details:**")
            st.text(st.session_state.patient_data['extra_details'])

        # Chat Interface
        st.markdown("### Chat with Medical Assistant")
        st.markdown("---")

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Type your message here..."):
            with st.chat_message("user"):
                st.markdown(prompt)
            
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                ai_response = helper.ask_doctor(
                    patient_data=st.session_state.patient_data, 
                    conversation=st.session_state.messages
                )
                
                with st.chat_message("assistant"):
                    st.markdown(ai_response)
                
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                st.rerun()
            except Exception as e:
                st.error(f"Error getting AI response: {str(e)}")

        st.markdown("---")
        st.markdown("*Disclaimer: This is a demonstration medical chat assistant. Please consult with a qualified healthcare professional for actual medical advice.*")
        
        

elif st.session_state.doctor:
    # Title and introduction
    st.title("Patient Information Form")
    st.write("Please fill in your details")

    # Create a form
    with st.form("patient_form"):
        # Personal Information Section
        st.subheader("Personal Information")
        full_name = st.text_input("Full Name")
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=150, value=0)
        with col2:
            gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"])

        # Physical Characteristics Section
        st.subheader("Physical Characteristics")
        col3, col4 = st.columns(2)
        with col3:
            height = st.number_input("Height (in cm)", min_value=0.0, placeholder="Optional")
        with col4:
            weight = st.number_input("Weight (in kg)", min_value=0.0, placeholder="Optional")
        
        blood_group = st.selectbox("Blood Group", 
                                ["Select", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Not Known"])

        # Medical Information Section
        st.subheader("Medical Information")
        current_symptoms = st.text_area("Current Symptoms")
        medical_history = st.text_area("Medical History", placeholder="Optional")
        current_medications = st.text_area("Current Medications", placeholder="Optional")
        extra_details = st.text_area("Extra Details", placeholder="Optional")

        # File Upload Section
        st.subheader("Medical Reports")
        uploaded_files = st.file_uploader("Upload medical reports", 
                                        type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
                                        accept_multiple_files=True,
                                        help="Drag and drop your medical reports here")

        # Submit button
        submitted = st.form_submit_button("Generate Diagnosis")

    # Display uploaded files information
    if uploaded_files:
        st.subheader("Uploaded Files")
        for uploaded_file in uploaded_files:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"📄 {uploaded_file.name}")
            with col2:
                file_size = len(uploaded_file.getvalue()) / 1024  # Size in KB
                if file_size < 1024:
                    st.write(f"Size: {file_size:.1f} KB")
                else:
                    st.write(f"Size: {file_size/1024:.1f} MB")
            with col3:
                st.write(f"Type: {uploaded_file.type}")

    # Process the form data when submitted
    if submitted:
        # Validate required fields
        if not full_name or gender == "Select" or blood_group == "Select" or not current_symptoms:
            st.error("Please fill in all required fields.")
        else:
            # Prepare data for LLM analysis
            patient_data = {
                "full_name": full_name,
                "age": age,
                "gender": gender,
                "height": str(height)+"cm" if height > 0 else None,
                "weight": str(weight)+"kg" if weight > 0 else None,
                "blood_group": blood_group,
                "current_symptoms": current_symptoms,
                "medical_history": medical_history if medical_history else None,
                "current_medications": current_medications if current_medications else None,
                "extra_details": extra_details if extra_details else None,
            }

            # Handle uploaded files
            if uploaded_files:
                files_data = []
                for uploaded_file in uploaded_files:
                    file_data = {
                        "filename": uploaded_file.name,
                        "content": uploaded_file.read(),
                        "type": uploaded_file.type
                    }
                    files_data.append(file_data)
                patient_data["medical_reports"] = files_data
            else:
                patient_data["medical_reports"] = []

            # Display processing message
            with st.spinner("Analyzing patient information..."):
                try:
                    response = helper.Generate_differential_Diagonosis(patient_data=patient_data)

                    st.success("Analysis complete!")
                    
                    # Display results section
                    st.subheader("Differential Diagnosis")
                    st.info(response)

                except Exception as e:
                    st.error(f"An error occurred during analysis: {str(e)}")