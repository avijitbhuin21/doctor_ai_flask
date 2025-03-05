import re
import openai
import json
from dotenv import load_dotenv
import os
from mistralai import Mistral
import random
import io
import base64

import markdown
from markdown.extensions import fenced_code

import fitz  
from PIL import Image
# from IPython.display import display, Image as IPyImage
import google.generativeai as genai
import tempfile
import mimetypes
import google.generativeai as genai
from werkzeug.utils import secure_filename

load_dotenv()
DEBUG = True

def log_debug(data):
    if DEBUG:
        print("DEBUG:")
        print(data)
        print("\n\n")

def generate_medical_report_html(markdown_text):
    # Replace tabs with spaces and preserve line breaks
    markdown_text = markdown_text.replace('\t', '    ')
    
    # Convert markdown to HTML using the markdown library with extensions
    html_content = markdown.markdown(
        markdown_text,
        extensions=['fenced_code', 'nl2br'],
        output_format='html5'
    )
    formatted_html = f"<div class='medical-report'>{html_content}</div>".replace('''<br>
    - ''', '''<br>
       - ''')
    log_debug(formatted_html)
    return {"type":"markdown" ,"html": formatted_html, "markdown": markdown_text}





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

    def ask_Mistral(self, question, sys="You're a Doctor-AI with 20 years of experience.", JSON= False, model = "mistral-large-latest"):
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
    def get_mime_type(self, filename):
        """Determine mime type based on file extension"""
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type and mime_type.startswith('image/'):
            return mime_type
        # Default to JPEG if can't determine
        return 'image/jpeg'

    def base64_to_bytes(self, base64_string):
        """Convert base64 string back to bytes"""
        return base64.b64decode(base64_string)

    def ask_Gemini(self, image_list, prompt):
        """
        image_list: List of tuples (image_name, base64_image) or just base64 strings for PDF pages
        prompt: String containing the prompt for Gemini
        """
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-exp-1206",
            generation_config=generation_config,
        )

        temp_files = []
        files_for_gemini = []
        
        try:
            for item in image_list:
                if isinstance(item, tuple):
                    # Handle (filename, base64_image) tuple
                    filename, base64_image = item
                    img_data = self.base64_to_bytes(base64_image)
                    ext = os.path.splitext(filename)[1].lower()
                    mime_type = self.get_mime_type(filename)
                else:
                    # Handle base64 string from PDF conversion
                    img_data = self.base64_to_bytes(item)
                    ext = '.jpg'  # PDF pages are converted to JPEG
                    mime_type = 'image/jpeg'

                if not ext:
                    ext = '.jpg'

                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
                temp_files.append(temp_file.name)
                
                # Write the binary content
                temp_file.write(img_data)
                temp_file.close()
                
                # Upload to Gemini
                gemini_file = genai.upload_file(temp_file.name, mime_type=mime_type)
                files_for_gemini.append(gemini_file)

            # Start chat session with all images
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": files_for_gemini,
                    },
                ]
            )

            # Send the prompt and get response
            response = chat_session.send_message(prompt)
            return response.text

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    print(f"Error removing temporary file {temp_file}: {e}")


class Patient_chat_Helper:
    def __init__(self):
        self.llm = LLM()
        self.report_displayed_status = False

    def greet(self, patient_data: dict) -> str:
        base_prompt = """This is the patient Profile:\n"""
        for i in patient_data:
            if patient_data[i] != '':
                base_prompt += f'''{i}: {patient_data[i]}\n'''

        GREETINGS_PROMPT = """Greet the patient briefly while asking a question regarding their visit.
        Use this JSON schema for construction of the answer:
        {"content": str}"""

        greetings = self.llm.ask_Mistral(base_prompt + GREETINGS_PROMPT, JSON=True)
        return {"type": "text", "data": greetings['content']}

    def get_a_question(self, patient_data: dict, conversation: list) -> str:
        patient_profile = "This is the patient Profile:\n"
        for key, value in patient_data.items():
            if value:
                patient_profile += f"{key}: {value}\n"
        
        # Create chat history string
        chat_history = "CHAT HISTORY:\n"
        for index, msg in enumerate(conversation):
            if index % 2 == 0:
                chat_history += f"Assistant: {msg['assistant']}\n"
            else:
                chat_history += f"User: {msg['user']}\n\n"

        QUESTION_GENERATION_PROMPT = '''generate the answer in the following JSON format:
            {"content": str}

            ask one question to the patient to get a more clear view of their symptoms/situation.
            make the question clear and if required give a real life example or reference to be more specific just like a real doctor would do.
            Do not ask multiple questions inside a single one.
            Keep the conversation Professional and do not thank the user everytime.
            If the user requests anything other than diagnosing a disease, decline the request politely.'''

        STATUS_PROMPT = """Based on this data if you can guess the disease then answer in this JSON format:
                            {"status": "success", "content": name of the disease(str)}

                            If you are still not sure then answer in this JSON format:
                            {"status": "failed", "content": "pending"}"""

        FURTHER_PROMPT = """Based on this patient profile and the conversation provided help the user with their query. 
                            Keep the message brief and concise like you would do in a chat.
                            If the user requests anything that is not related to a doctor, YOU MUST decline the request.
                            answer in this JSON format:
                            {"data": answer(str), "type": type of the answer (can be "text" or "markdown" only based on the answer provided)}"""

        if self.report_displayed_status:
            # Get further response
            print(f"Report status: {self.report_displayed_status}")
            content = self.llm.ask_Mistral(
                question=f"{patient_profile}\n\n{chat_history}{FURTHER_PROMPT}",
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
            status = self.llm.ask_llama(
                query=f"{patient_profile}\n\n{chat_history}{STATUS_PROMPT}",
                JSON=True
            )
            
            # If we have a successful diagnosis
            if status['status'] == 'success':
                prom = f"{patient_profile}\n\n{chat_history}DIAGNOSED DISEASE:\n{status['content']}"
                try:
                    report = self.get_report(prompt=prom, country=patient_data['Country'])
                    if report:  # Only set status to True if report generation was successful
                        self.report_displayed_status = True
                    return report
                except Exception as e:
                    log_debug(f"Report generation failed: {str(e)}")
                    # If report generation fails, continue with question generation
                    pass

            # If no diagnosis yet or report generation failed, generate next question
            question = self.llm.ask_Mistral(
                f"{patient_profile}\n\n{chat_history}{QUESTION_GENERATION_PROMPT}",
                JSON=True
            )
            return {"type": "text", "data": question['content']}
            
        except Exception as e:
            log_debug(f"Error in diagnosis process: {str(e)}")
            # Fallback to question generation in case of any errors
            question = self.llm.ask_Mistral(
                f"{patient_profile}\n\n{chat_history}{QUESTION_GENERATION_PROMPT}",
                JSON=True
            )
            return {"type": "text", "data": question['content']}

    # def get_bayer_meds(self, prompt: str, country: str = None):
    #     bayers_meds = open('static/data/bayers_data.json').read()
    #     prompt = prompt +"""
    #             Based on this data Provided, can you gimme a list of meds i can suggest from this list of meds for the disease mentioned in the prompt.
    #             """ + bayers_meds + """
    #             in this JSON format:
    #             {"status": found / error, "meds": [{"name": str, "side_effects": str, "uses": str}]}

    #             if no meds are suitable set the status as "error" and set meds as []
    #             only if any meds found return status as "found" and in meds return the medicines.
    #             Do not return anything other than the JSON data.
    #             Do not include any explanation, apology or introductions in the answer.
    #             """
    #     meds = self.llm.ask_llama(query = prompt)
    #     log_debug(meds)
    #     if "error" in meds:
    #         return None
    #     return meds

    def get_report(self, prompt: str, country: str):
        # bayer_meds = self.get_bayer_meds(prompt = prompt, country = country)
        bayer_meds = None
        REPORT_PROMPT = """Based on this data generate a mesage for the user telling him the disease and probable medications for that.
                    Also mention the next step the user should take."""
                    
        STRUCTURE_OF_THE_ANSWER = """
                    Generate this is MARKDOWN format.
                    Also You Must Mention that the patient is advised to consult a doctor before taking any of those meds.
                    
                    Use the format below to generate the report(from this template if the data is available for the patient only then add it to the report else ignore that particular option or section):
                    Certainly! Below is a simplistic template for a Disease Diagnosis Report:

#Disease Diagnosis Report


**Diagnosis:**
- Disease/Condition: [Name of the Disease/Condition]

**Symptoms:**
- [List of Symptoms Observed]

**Medical History:**
- [Relevant Medical History if provided by the user]

**Treatment Plan:**
- Medications: [List of Prescribed Medications]

- Name: [Name of the Drug]
    - Use: [Purpose of the Drug]
    - Dosage: [Dosage Instructions and Efficacy of the Drug]
    - Known Side Effects: [List of known side effects of the provided medications (only if there are any side effects)]
    - Efficacy of the drug.
(repeat this pattern for each prescribed medicine)

- Therapy/Procedures: [List of Recommended Therapies/Procedures]
- Follow-up: [Follow-up Instructions]

**Probable Tests:**
- [Relevant tests to be taken to confirm the diagnosis (only if required)]

**Prognosis:**
- [Expected Outcome and Prognosis]

**Additional Notes:**
- [Any Additional Information or Notes]

---
Disclaimer: Do no Take any medication without consulting a Doctor.
"""

        if bayer_meds != None:
            ADDITIONAL_PROMPT = f'''When mentioning medications always prioritize the medications from the following data, if no meds available then you may prescribe any medicine you think is suitable: {bayer_meds}'''
            REPORT_GENERATION_PROMPT = REPORT_PROMPT + ADDITIONAL_PROMPT + STRUCTURE_OF_THE_ANSWER
        else:
            REPORT_GENERATION_PROMPT = REPORT_PROMPT + STRUCTURE_OF_THE_ANSWER

        updated_prompt = prompt + "\n\n" + REPORT_GENERATION_PROMPT
        report = self.llm.ask_llama(updated_prompt)
        log_debug(report)
        report = generate_medical_report_html(report)
        return report

class Internet_Search_Agent:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }


class File:
    def __init__(self):
        self.llm_client = LLM()

    def Extract_Text(self, file_bytes, file_name):
        REPORT_GENERATION_PROMPT = """Analyze all these images and generate me a overall report from the data in these images without leaving any significant details behind.
Cause this will be used to diagonose the patient. Generate this in MARKDOWN format."""      
        if "jpg" in file_name or "jpeg" in file_name or "png" in file_name:  
            base64_images = base64.b64encode(file_bytes).decode('utf-8')
            # self.display_images([base64_images])
            report = self.llm_client.ask_Pixtral(question=REPORT_GENERATION_PROMPT, images= base64_images)
            return report
        if "pdf" in file_name or "doc" in file_name:    
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
                        # self.display_images([base64_img])
                        base64_images.append(base64_img)

                report = self.llm_client.ask_Pixtral(question=REPORT_GENERATION_PROMPT, images= base64_images)

                return report
         
            except Exception as e:
                raise ValueError(f"Conversion error: {str(e)}")
        else:
            return open(file_bytes, 'r').read()

    def display_images(self, base64_images):
        for i, img in enumerate(base64_images):
            try:
                # Decode the base64 image
                image_data = base64.b64decode(img)
                # Display the image
                # display(IPyImage(data=image_data, format='jpeg'))
                print(f"Page {i+1} image displayed.")
            except Exception as e:
                print(f"Error displaying image for page {i+1}: {e}")
        
    def handle_file(self, file_data):
        final_report = ""

        for each_file in file_data:
            file_text = self.Extract_Text(each_file['content'], each_file['filename'])
            final_report += file_text + "\n\n"

        return final_report


class Doctor_chat_Helper:
    def __init__(self):
        self.llm_client = LLM()

    def get_questions(self, patient_data: dict, reports: str = None) -> str:
        prompt = """This is the patient Profile:\n"""
        for i in patient_data:
            if patient_data[i] != '':
                prompt += f'''{i}: {patient_data[i]}\n'''

        if reports:
            prompt += "These are the reports related to the patient:\n" + reports

        QUESTION_GENERATION_PROMPT = '''Based on the following data provided about the patient generate some questions you would like to ask the patient before analyzing the patient.
            Note that ask as less question as possible to the patient.
            in the following JSON format:
            {"content": list(str)}'''

        questions = self.llm_client.ask_Mistral(prompt + '\n\n' + QUESTION_GENERATION_PROMPT, JSON= True)

        return questions['content']

    # def get_bayer_meds(self, prompt: str, country: str = None):
    #     bayers_meds = open('static/data/bayers_data.json').read()
    #     prompt = prompt +"""
    #             Based on this data Provided, can you gimme a list of meds i can suggest from this list of meds for the patient mentioned in the prompt.
    #             """ + bayers_meds + """
    #             in this JSON format:
    #             {"status": found / error, "meds": [{"name": str, "side_effects": str, "uses": str}]}

    #             if no meds are suitable set the status as error and set meds as []
    #             Do not return anything other than the JSON data.
    #             Do not include any explanation, apology or introductions in the answer.
    #             """
    #     meds = self.llm_client.ask_llama(query = prompt)
    #     log_debug(meds)
    #     if "error" in meds:
    #         return None
    #     return meds

    def generate_report(self, patient_data: dict, report: str = None, follow_up_questions: dict = None) -> str:
        patient_profile = """This is the patient Profile:\n"""
        for i in patient_data:
            if patient_data[i] != '':
                patient_profile += f'''{i}: {patient_data[i]}\n'''

        if report:
            report = "These are the reports related to the patient:\n" + report + "\n\n"
        else:
            report = ''

        if follow_up_questions:
            questions = "These are the follow up questions related to the patient:\n\n"
            for index,i in enumerate(follow_up_questions):
                questions+= f"question_{index}: {i}\n answer: {follow_up_questions[i]}\n\n"
        else:
            follow_up_questions = ''
        
        # bayers_meds = self.get_bayer_meds(prompt= patient_profile + report + questions)
        bayers_meds = None
        DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT = """
        Please generate a differential diagnosis using the following template for the given patient:

            ## Patient Information
             - Name:  
             - Age:  
             - Gender:  
             - Main Symptoms:  
             - Past Medical History:  
             - Known Medical Conditions:  
             - Current Medications:
             - Country:

            ##Differential Diagnosis:

            For each potential disease, include:
            # Disease Name (Chance Percentage)
             **Reasoning:**
                - Symptom 1
                - Symptom 2

             **Relevant history or examination finding:**
                - details

             **Probable Medications:**
                - Medication 1
                    - known side effects 
                    - efficacy 

                - Medication 2
                    - known side effects 
                    - efficacy 

             **Tests:**(only if applicable)
                 - test 1
                 - test 2

             **Home Remeady:**(only if applicable)
                 - Suggestion 1
                 - suggestion 2
            
            Repeat for up to 10 diseases that are most likely based on the patient information.
            
            At the very last add the following disclaimer:
            
            ---
            Disclaimer: Do no Take any medication without consulting a Doctor."""

        if bayers_meds != None:
            DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT = """NOTE: When mentioning medications always prioritize the medications from the following data, if no meds available in the data for the disease then you may prescribe any medicine you think is suitable:
                    """ + bayers_meds + DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT


        prompt = patient_profile + report + questions + "\n\n" + DIFFERENTIAL_DIAGONOSIS_GENERATION_PROMPT
        report = self.llm_client.ask_llama(query= prompt)
        report = generate_medical_report_html(report)
        return report['html']

class ECG:
    def __init__(self):
        self.ECG_REPORT_GENERATION_PROMPT = """From the Images provided above make a single proper ecg report for the patient in markdown format. if no data regarding ecg is provided politely decline the request and ask the user to provide proper files. always add a disclaimer that this is a ai generated report and always discuss with a professional before taking any actions.
        Do not add patient or physician details in the report.
        Do not mention the you're making this from a report or your'e provided any external report to generate the report.
        start with ## ECG Analysis
        in conclusion section add the probable disease if applicable from the ecg report in this format:
        ## disease name
        - reason
        - reason"""
        self.llm_client = LLM()

    def get_images(self, file_bytes, file_name):
        if "jpg" in file_name.lower() or "jpeg" in file_name.lower() or "png" in file_name.lower():
            base64_images = base64.b64encode(file_bytes).decode('utf-8')
            return [(file_name, base64_images)]
        
        if "pdf" in file_name.lower() or "doc" in file_name.lower():
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
                        base64_images.append(base64_img)  # Store just the base64 string for PDF pages
                return base64_images
            except Exception as e:
                raise ValueError(f"Conversion error: {str(e)}")

    def get_image_list(self, file_data):
        final_image_list = []
        
        for each_file in file_data:
            image_list = self.get_images(each_file['content'], each_file['filename'])
            final_image_list.extend(image_list)

        return [final_image_list] if len(final_image_list) < 10 else [final_image_list[i:i + 5] for i in range(0, len(final_image_list), 5)]

    def handle_file(self, file_data):
        structured_image_list = self.get_image_list(file_data=file_data)
        reports = ""
        
        # Process each batch of 5 images
        for image_batch in structured_image_list:
            batch_report = self.llm_client.ask_Gemini(
                image_list=image_batch,
                prompt=self.ECG_REPORT_GENERATION_PROMPT
            )
            reports += batch_report + "\n\n"
        
        return reports

    






        

        
