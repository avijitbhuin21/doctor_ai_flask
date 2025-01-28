import re
import openai
import json
from dotenv import load_dotenv
import os
from mistralai import Mistral
import random
import io
import base64
import fitz  
from PIL import Image
from IPython.display import display, Image as IPyImage

load_dotenv()
DEBUG = False

def log_debug(data):
    if DEBUG:
        print(f"DEBUG: {data}")


#PROMPTS
##############################################################################################################################################################################################################################
DIAGONOSING_PROMPT = """Based on this data if you can guess the disease then answer in this JSON format:
{"status": "success", "content": name of the disease(str)}

If you want to ask the patient question to get more context answer in this JSON format:
{"status": "pending", "content": question(str)}

You may only ask one question at a time."""

DECIDING_PROMPT = """Based on this data You have to guess the disease and generate a mesage for the user telling him the disease and probable medications for that.
Also mention the next step the user should take.
Generate this is MARKDOWN format.
Also You Must Mention that the patient is advised to consult a doctor before taking any of those meds."""

MEDS_PROMPT = """Based on this data generate a mesage for the user telling him the disease and probable medications for that.
Also mention the next step the user should take.
Generate this is MARKDOWN format.
Also You Must Mention that the patient is advised to consult a doctor before taking any of those meds."""

REPORT_GENERATION_PROMPT = """Analyze all these images and generate me a overall report from the data in these images without leaving any significant details behind.
Cause this will be used to diagonose the patient. Generate this in MARKDOWN format."""

DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT = """Please generate a differential diagnosis using the following template for a given case:

Patient Information
- Name:  
- Age:  
- Gender:  
- Main Symptoms:  
- Past Medical History:  
- Known Medical Conditions:  
- Current Medications:

Differential Diagnosis:

For each potential disease, include:

## 1. Disease Name (Chance Percentage)
- Reasoning:
  - Symptom 1
  - Symptom 2
  - Relevant history or examination finding
- Probable Medications:
  - Medication 1
  - Medication 2

Repeat for up to 10 diseases that are most likely based on the patient information."""
##############################################################################################################################################################################################################################
class LLM:
    def extract_query(self, text: str) -> str:
        pattern = r"```(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        return matches[0] if matches else text

    def ask_llama(self, query, api_key = random.choice(os.getenv('Sambanova_Api_Key').split()), model = "Meta-Llama-3.1-405B-Instruct", JSON = False):
        for i in range(5):
            SambaNova_Client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.sambanova.ai/v1",
                )
            response = SambaNova_Client.chat.completions.create(
                model=model,
                messages=[{"role":"system","content": "You're a Doctor-AI with 20 years of experience."},{"role":"user","content":query}],
                temperature =  0.1,
                top_p = 0.1,
            )
            ans = response.choices[0].message.content
            if not JSON:
                return ans
            try:
                data = json.loads(self.extract_query(ans))
                return data
            except Exception as e:
                print(e)
                print(response.choices[0].message.content)

    def ask_Mistral(self, question, sys="You're a Doctor-AI with 20 years of experience.", JSON= False, model = "mistral-large-2411"):
        try:
            self.Mistral_Client = Mistral(
                    api_key=random.choice(os.getenv('Mistral_Api_Key').split()),
                )
            for i in range(10):
                try:
                    if JSON:
                        response = self.Mistral_Client.chat.complete(
                        model=model,
                        messages=[{"role":"system","content":sys},{"role":"user","content":question}],
                        temperature =  0.1,
                        top_p = 0.1,
                        response_format = {
                                "type": "json_object",
                            }
                    )
                        return json.loads(response.choices[0].message.content)
                    else:
                        response = self.Mistral_Client.chat.complete(
                        model=model,
                        messages=[{"role":"system","content":sys},{"role":"user","content":question}],
                        temperature =  0.1,
                        top_p = 0.1
                    )
                        return response.choices[0].message.content
                    
                except Exception as e:
                    print(e)
                    print(response.choices[0].message.content)

        except Exception as e:
            print(e)

    def ask_Pixtral(self, question, images, model = "pixtral-large-2411"):
        try:
            self.Pixtral_Client = Mistral(
                    api_key=random.choice(os.getenv('Mistral_Api_Key').split()),
                )
            messages = [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": question
                                    }
                                ] + [{
                                        "type": "image_url",
                                        "image_url": f"data:image/jpeg;base64,{i}" 
                                    } for i in images]
                            }
                        ]
            chat_response = self.Pixtral_Client.chat.complete(
                            model=model,
                            messages= messages
                        )
            
            return chat_response.choices[0].message.content
        
        except Exception as e:
            print(e)


class File:
    def __init__(self):
        self.llm_client = LLM()

    def Extract_Text(self, file_bytes, file_name):      
        if "jpg" not in file_name and "jpeg" not in file_name and "png" not in file_name:    
            base64_images = []
            try:
                with fitz.open(stream=file_bytes) as doc:
                    for page_num in range(len(doc)):
                        page = doc.load_page(page_num)
                        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG')
                        base64_img = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                        base64_images.append(base64_img)

                report = self.llm_client.ask_Pixtral(question=REPORT_GENERATION_PROMPT, images= base64_images)

                return report
        
            except Exception as e:
                raise ValueError(f"Conversion error: {str(e)}")
        else:
            base64_images = base64.b64encode(file_bytes).decode('utf-8')
            report = self.llm_client.ask_Pixtral(question=REPORT_GENERATION_PROMPT, images= base64_images)
            return report

    def display_images(self, base64_images):
        for i, img in enumerate(base64_images):
            try:
                # Decode the base64 image
                image_data = base64.b64decode(img)
                # Display the image
                display(IPyImage(data=image_data, format='jpeg'))
                print(f"Page {i+1} image displayed.")
            except Exception as e:
                print(f"Error displaying image for page {i+1}: {e}")
        
    def handle_file(self, file_data):
        final_report = ""

        for each_file in file_data:
            file_text = self.Extract_Text(each_file['content'], each_file['filename'])
            final_report += file_text + "\n\n"

        return final_report
        




class Helper:
    def __init__(self):
        self.llm = LLM()
        self.file_handler = File()

    def get_prompt(self, patient_data, conversation):
        base_prompt = """This is the patient Profile:\n"""
        for i in patient_data:
            if patient_data[i] != '':
                base_prompt += f'''{i}: {patient_data[i]}\n'''

        formatted_conversation = "Chat History:\n"
        question_count = 0

        for i, message in enumerate(conversation):
            if message['role'] == 'assistant':
                question_count += 1
                formatted_conversation += f"Assistant: {message['content']}\n"
                if i + 1 < len(conversation) and conversation[i + 1]['role'] == 'user':
                    formatted_conversation += f"User: {conversation[i + 1]['content']}\n\n"
                else:
                    formatted_conversation += "\n"
            elif message['role'] == 'assistant' and (i == 0 or conversation[i - 1]['role'] != 'user'):
                formatted_conversation += f"Assistant: {message['content']}\n\n"
        if question_count == 0:
            temp = ''
        if question_count == 1:
            temp = f"This is your 1st question."
        if question_count == 2:
            temp = f"This is your 2nd question."
        if question_count == 3:
            temp = f"This is your 3rd question."
        if question_count > 3:
            temp = f"this is your {question_count}th question."

        main = formatted_conversation + "\n" + temp
        if conversation == []:
            return (base_prompt, None, question_count)
        else:
            return (base_prompt, main, question_count)
    
    def ask_doctor(self, patient_data, conversation):
        patient_profile, history, question_count = self.get_prompt(patient_data= patient_data, conversation= conversation)

        if history == None:
            prompt = patient_profile + "\n" + DIAGONOSING_PROMPT + "\n" + "Note that you can ask maximum of 5 questions." + "\n" + "try to ask least number of questions." + "\n" + 'Also Greet the user first then ask the question, as this is the start of our conversation with the patient.'
            log_debug(prompt)
            ai_ans = self.llm.ask_Mistral(question= prompt, JSON= True)
        else:
            if question_count > 6:
                prompt = patient_profile + "\n" + history + "\n" + DECIDING_PROMPT
                log_debug(prompt)
                return self.llm.ask_llama(query= prompt, JSON= False)

            else:
                prompt = patient_profile + "\n" + history + "\n" + DIAGONOSING_PROMPT
                log_debug(prompt)
                ai_ans = self.llm.ask_Mistral(question= prompt, JSON= True)

        if ai_ans['status'] == 'success':
            prompt = patient_profile + "\n" + history + "\n" + f"The Most Probable Disease is: {ai_ans['content']}" + "\n" + MEDS_PROMPT
            log_debug(prompt)
            return self.llm.ask_llama(query= prompt, JSON= False)
        
        log_debug(ai_ans)
        return ai_ans['content']
    
    def Generate_differential_Diagonosis(self, patient_data):
        
        medical_reports = patient_data['medical_reports']
        Final_Medical_report = self.file_handler.handle_file(medical_reports)
        patient_data['medical_reports'] = Final_Medical_report

        prompt,_,_ = self.get_prompt(patient_data= patient_data, conversation= [])
        
        diagonosis = self.llm.ask_llama(query= prompt + "\n\n" + DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT)

        return diagonosis









        
            
        