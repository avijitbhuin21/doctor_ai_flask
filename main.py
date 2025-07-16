from flask import Flask, render_template, request, jsonify
import json
from flask import request
from dotenv import load_dotenv

#Local imports
from static.helper_files.PROMPTS import *
from static.helper_files.universal_functions import *
from static.helper_files.B2b import B2b
from static.helper_files.B2c import B2c
from static.helper_files.supabase import *



load_dotenv()


patient_agent = B2c()
doctor_agent = B2b()
app = Flask(__name__)

# ALL GET ROUTES

#Homepage
@app.route("/")
def index():
    return render_template("homepage.html")
# Patient Use Case
@app.route("/redirect_patient")
def redirect_patient():
    return render_template("redirect_patient.html")
# Doctor Use Case
@app.route("/redirect_doctor")
def redirect_doctor():
    return render_template("redirect_doctor.html")



#ALL POST ROUTES

#Check login status
@app.route("/check_login_status", methods=["POST"])
def check_login_status():
    data = request.json
    email = data.get("email")
    log_debug(email)
    xx = get_login_status(email)
    log_debug(xx)
    return xx

#Submit feedback
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.json
        email = data.get('email')
        feedback = data.get('feedback')
        
        # Print to console for debugging
        log_debug("Feedback Submission:")
        log_debug(f"Email: {email}")
        log_debug(f"Feedback: {feedback}")
        
        return store_feedback(email, feedback)
    except Exception as e:
        log_debug(f"Error submitting feedback: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
#B2b -------------------------------------------------------------------------------------------------------------------------------------------->

#Upload patient details and files
@app.route("/upload", methods=["POST"])
def upload():
    patient_details = {
        "fullName": request.form.get("fullName"),
        "age": request.form.get("age"),
        "gender": request.form.get("gender"),
        "height": request.form.get("height"),
        "weight": request.form.get("weight"),
        "bloodGroup": request.form.get("bloodGroup"),
        "symptoms": request.form.get("symptoms"),
        "medicalHistory": request.form.get("medicalHistory"),
        "medications": request.form.get("medications"),
        "extraDetails": request.form.get("extraDetails"),
        "country": request.form.get("country")
    }
    report = None
    log_debug(json.dumps(patient_details, indent=4), name='Patient Details (JSON):')

    if "files" in request.files:
        files = request.files.getlist("files")
        file_data = []
        for file in files:
            # Correct tuple syntax for append
            file_data.append((file.filename, file.read()))
            file.seek(0) 

        report = process_file_with_gemini(file_data= file_data, sys=REPORT_GENERATION_PROMPT_FILE)
        log_debug(report)

    questions = doctor_agent.get_initial_questions(patient_data= patient_details, reports= report)
    log_debug(questions)
    return jsonify({"questions": questions, "report": report})

#Generate Differential Diagnosis report 
@app.route('/generate_report', methods=['POST'])
def generate_report():
    patient_info = request.json.get('patientInfo')
    report = request.json.get('report')
    follow_up_questions = request.json.get('followUpQuestions')
    email= request.json.get('email')

    log_debug(f"Patient Info: {patient_info}")
    log_debug(f"Report: {report}")
    log_debug(f"Follow-up Questions: {follow_up_questions}")
    log_debug(f"Email: {email}")

    differential_diagonosis = doctor_agent.generate_report(patient_data= patient_info, report= report, follow_up_questions= follow_up_questions)
    log_debug(differential_diagonosis)
    data = {"email": email, "patient_info": str(patient_info), "report": str(report), "follow_up": str(follow_up_questions), "diagnosis": str(differential_diagonosis)}
    print("\n\n\n\n"+str(data))
    # store_B2b_data(data)
    return {"report": differential_diagonosis}

#B2c  ------------------------------------------------------------------------------------------------------------------------------------------->

#Get AI response(patient chat)
@app.route("/get_ai_response", methods=["POST"])
def get_ai_response():
    data = request.json
    log_debug(data, name="Data")
    user_message = data["message"]
    chat_history = data["history"]
    patient_info = data["patientInfo"]

    log_debug(user_message, name="User Message")
    log_debug(chat_history, name="Chat History")
    log_debug(patient_info, name="Patient Info")
    
    ai_response = patient_agent.get_a_question(patient_data= patient_info, conversation= chat_history)
    log_debug(("ai_response",ai_response))

    store_B2c_data({"email": data["email"], "conversation": str({"role": "patient", "message": user_message})})
    store_B2c_data({"email": data["email"], "conversation": str({"role": "AI", "message": ai_response})})

    return jsonify({"response": ai_response})

# Greet the user
@app.route("/get_greetings", methods=["POST"])
def get_greetings():
    data = request.json
    patient_info = data["patientInfo"]

    log_debug(patient_info)
    store_patient_info({"email": data["email"], "patient_info": str(patient_info)})

    greetings = patient_agent.greet(patient_data = patient_info)
    log_debug(greetings)

    return jsonify({"response": greetings})


if __name__ == "__main__":
    app.run(debug=True)



