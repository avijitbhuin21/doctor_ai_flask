from supabase import create_client
from flask import jsonify
import os
from dotenv import load_dotenv
from static.helper_files.universal_functions import log_debug

load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)


def get_login_status(email):
    if not email:
        return jsonify({"status": False, "error": "Email is required"})
    
    try:
        # Check if email exists in waitlist
        result = supabase.table("wait_list").select("*").eq("email", email).execute()
        
        if result.data:
            # Email exists, check status
            user = result.data[0]
            if user["status"] == "true":
                return jsonify({"status": True})
            else:
                return jsonify({"status": "already exists"})
        else:
            # New email, add to waitlist
            supabase.table("wait_list").insert({
                "email": email,
                "status": "false"
            }).execute()
            return jsonify({"status": False})
            
    except Exception as e:
        log_debug(f"Database error: {str(e)}")
        return jsonify({"status": False, "error": "Database error"})
    
def store_feedback(email, feedback):
    result = supabase.table('Feedback').insert({
        "email": email,
        "feedback": feedback
    }).execute()
    
    return jsonify({"status": "success"}), 200

def store_B2b_data(data):
    result = supabase.table('B2b_convo').insert({
        "email": data['email'],
        "patient_info": data['patient_info'],
        "report": data['report'],
        "follow_up": data['follow_up'],
        "diagnosis": data['diagnosis']
    }).execute()
    
    return jsonify({"status": "success"}), 200

def store_B2c_data(data):
    result = supabase.table('conversation').insert({
        "email": data['email'],
        "conversation": data['conversation'],
    }).execute()
    
    return jsonify({"status": "success"}), 200

def store_patient_info(data):
    result = supabase.table('patient_info_B2c').insert({
        "email": data['email'],
        "patient_info": data['patient_info']
        }).execute()
    
    return jsonify({"status": "success"}), 200