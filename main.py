from flask import Flask, render_template, request, jsonify
from utils import Patient_chat_Helper, File, Doctor_chat_Helper, ECG
import json
from flask import request

patient_agent = Patient_chat_Helper()
doctor_agent = Doctor_chat_Helper()
file_handler = File()
ecg_agent = ECG()
app = Flask(__name__)

DEBUG = True

def log_debug(data):
    if DEBUG:
        print("DEBUG:")
        print(data)
        print("\n\n")


@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/redirect_patient")
def redirect_patient():
    return render_template("redirect_patient.html")

@app.route("/redirect_doctor")
def redirect_doctor():
    return render_template("redirect_doctor.html")

@app.route("/get_ecg")
def get_ecg():
    return render_template("ecg_report.html")

@app.route("/get_ai_response", methods=["POST"])
def get_ai_response():
    data = request.json
    user_message = data["message"]
    chat_history = data["history"]
    patient_info = data["patientInfo"]

    log_debug(user_message)
    log_debug(chat_history)
    log_debug(patient_info)
    
    ai_response = patient_agent.get_a_question(patient_data= patient_info, conversation= chat_history)
    log_debug(("ai_response",ai_response))
    return jsonify({"response": ai_response})

@app.route("/get_greetings", methods=["POST"])
def get_greetings():
    data = request.json
    patient_info = data["patientInfo"]

    log_debug(patient_info)

    greetings = patient_agent.greet(patient_data = patient_info)
    log_debug(greetings)

    return jsonify({"response": greetings})

@app.route("/upload", methods=["POST"])
def upload():
    # Extract patient details from the form
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
    # log_debug patient details in JSON format
    log_debug("Patient Details (JSON):")
    log_debug(json.dumps(patient_details, indent=4))

    # Process uploaded files
    if "files" in request.files:
        files = request.files.getlist("files")
        file_data = []
        for file in files:
            file_data.append({"filename": file.filename, "content": file.read()})
            file.seek(0)  # Reset file pointer after reading

        report = file_handler.handle_file(file_data= file_data)
        log_debug(report)

    questions = doctor_agent.get_questions(patient_data= patient_details, reports= report)
    log_debug(questions)
    return jsonify({"questions": questions, "report": report})


@app.route('/generate_report', methods=['POST'])
def generate_report():
    patient_info = request.json.get('patientInfo')
    report = request.json.get('report')
    follow_up_questions = request.json.get('followUpQuestions')

    log_debug(f"Patient Info: {patient_info}")
    log_debug(f"Report: {report}")
    log_debug(f"Follow-up Questions: {follow_up_questions}")

    differential_diagonosis = doctor_agent.generate_report(patient_data= patient_info, report= report, follow_up_questions= follow_up_questions)
    log_debug(differential_diagonosis)

    return jsonify({"report": differential_diagonosis})

@app.route('/get_ecg_report', methods=['POST'])
def get_ecg_report():
    files = request.files.getlist("files")
    file_data = []
    for file in files:
        file_data.append({
            "filename": file.filename,
            "content": file.read()
        })
        file.seek(0)

    report = ecg_agent.handle_file(file_data=file_data)
    return jsonify({"report": report})


if __name__ == "__main__":
    app.run(debug=True, port=5000)


# --------Patient Page-----------#
# prioritize bayer meds first country specific.
# make the country field specific

# -------Doctor Part-------------#
# make the country field specific
# suggest bayers meds that is country specific.
