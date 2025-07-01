

# LOCAL IMPORTS
from .PROMPTS import *
from .universal_functions import *

class B2b:
    def get_initial_questions(self, patient_data: dict, reports: str= None) ->str:
        base_prompt = """This is the patient Profile:\n"""

        for i in patient_data:
            if patient_data[i] != '':
                base_prompt += f'''{i}: {patient_data[i]}\n'''

        if reports:
            base_prompt += "These are the reports related to the patient:\n" + reports


        questions = ask_gemini_flash(question=base_prompt, sys=QUESTION_GENERATION_PROMPT_B2B, JSON= True)
        log_debug(questions, name = "Questions")
        
        return questions['content']
        
    def generate_report(self, patient_data: dict, report: str =None, follow_up_questions: dict = None) -> str:
        base_prompt = """This is the patient Profile:\n"""

        for i in patient_data:
            if patient_data[i] != '':
                base_prompt += f'''{i}: {patient_data[i]}\n'''

        if report:
            base_prompt += "These are the reports related to the patient:\n" + report

        if follow_up_questions:
            questions = "These are the follow up questions related to the patient:\n\n"
            for index,i in enumerate(follow_up_questions):
                questions+= f"question_{index}: {i}\n answer: {follow_up_questions[i]}\n\n"
        else:
            follow_up_questions = ''

        prompt = base_prompt + questions
        report = ask_llama(query= prompt, sys= DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT)
        if '</think>':
            report = "\n\n\n"+report.split("</think>")[-1]
        log_debug(report, name = "Report")
        report = generate_medical_report_html(report)
        return report['html']