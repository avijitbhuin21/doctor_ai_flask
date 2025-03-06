from supabase import create_client
from flask import jsonify
import os
from dotenv import load_dotenv
from .utils import log_debug

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