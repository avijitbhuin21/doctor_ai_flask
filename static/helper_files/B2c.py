
# LOCAL IMPORTS
from .PROMPTS import *
from .universal_functions import *

class B2c:
    def __init__(self):
        self.report_displayed_status = False

    def greet(self, patient_data: dict) -> str:
        base_prompt = """This is the patient Profile:\n"""
        for i in patient_data:
            if patient_data[i] != '':
                base_prompt += f'''{i}: {patient_data[i]}\n'''

        greetings = ask_gemini_flash(question=base_prompt, sys=GREETINGS_PROMPT, JSON= True)
        return {"type": "text", "data": greetings['content']}
    
    def get_a_question(self, patient_data: dict, conversation: list) -> str:
        patient_profile = "This is the patient Profile:\n"
        for key, value in patient_data.items():
            if value:
                patient_profile += f"{key}: {value}\n"
        
        # Create chat history string
        chat_history = "CHAT HISTORY:\n"
        for msg in conversation:
            chat_history += f"{msg['role']}: {msg['message']}\n"

        # If we've already displayed a report, handle follow-up interaction
        if self.report_displayed_status:
            # Get further response
            print(f"Report status: {self.report_displayed_status}")
            content = ask_gemini_flash(
                question=f"{patient_profile}\n\n{chat_history}",
                sys=FURTHER_PROMPT,
                JSON=True
            )
            
            # Handle markdown conversion if needed
            if content['type'] == "markdown":
                m = generate_medical_report_html(content['data'])
                content['html'] = m['html']
                content['markdown'] = m['markdown']
            log_debug(("content", content))
            return content

        try:
            # Check if we can make a diagnosis
            log_debug("asking llama for status")
            status = ask_llama(
                query=f"{patient_profile}\n\n{chat_history}",
                sys=STATUS_PROMPT,
                JSON=True
            )
            
            # If we have a successful diagnosis
            if status['status'] == 'success':
                prom = f"{patient_profile}\n\n{chat_history}DIAGNOSED DISEASE:\n{status['content']}"
                try:
                    report = self.get_report(prompt=prom)
                    
                    # Set the flag to True BEFORE returning the report
                    self.report_displayed_status = True
                    log_debug("Setting report_displayed_status to True")
                    return report
                    
                except Exception as e:
                    log_debug(f"Report generation failed: {str(e)}")
                    # If report generation fails, continue with question generation
            
            # If no diagnosis yet or report generation failed, generate next question
            question = ask_gemini_flash(
                question=f"{patient_profile}\n\n{chat_history}",
                sys=QUESTION_GENERATION_PROMPT,
                JSON=True
            )
            return {"type": "text", "data": question['content']}
            
        except Exception as e:
            log_debug(f"Error in diagnosis process: {str(e)}")
            # Fallback to question generation in case of any errors
            question = ask_gemini_flash(
                question=f"{patient_profile}\n\n{chat_history}",
                sys=QUESTION_GENERATION_PROMPT,
                JSON=True
            )
            return {"type": "text", "data": question['content']}
        
    def get_report(self, prompt: str):
        report = ask_llama(sys=REPORT_GENERATION_PROMPT, query=prompt)
        log_debug(report)
        report = generate_medical_report_html(report)
        return report