import re
import openai
import json
from dotenv import load_dotenv
import os
import random
from google import genai
from google.genai import types
import tempfile
from datetime import datetime
import markdown
from typing import List, Tuple

load_dotenv()
DEBUG = True

def log_debug(data, name=None, level="DEBUG"):
    """Enhanced logging function with timestamp and log levels"""
    if DEBUG:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(data, (dict, list)):
            data = json.dumps(data, indent=2)
        message = f"[{timestamp}] [{level}] {name}: {data}" if name else f"[{timestamp}] [{level}] {data}"
        print(message)



#Parse text to JSON
def parse_text_to_json(text):
    try:
        if "```json" in text:
            text = text.replace("```json","").replace("```","")
        if "```" in text:
            text = text.replace("```", "")

        return json.loads(text)
    except Exception as e:
        log_debug(f"Error parsing text to JSON: {e}")
        return {"error": str(e)}
    


# Generate a medical report in HTML format
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



#ASK GEMINI FLASH Function:
def ask_gemini_flash(question, sys, api_key = os.getenv('GEMINI_API_KEY'), model = "gemini-2.0-flash-thinking-exp-01-21", JSON = False, history = None):

    log_debug(question, name = "Asking Gemini Flash")

    client = genai.Client(api_key=api_key)

    #Assuming the history is in this format: [{"role": "user", "text": "Hello"}, {"role": "model", "text": "Hi there!"}]
    if history:
        history = history + [{"role": "user", "parts": question}]
        log_debug(history, name = "History")
        contents = [types.Content(role=content["role"], parts=[types.Part.from_text(text=str(content["parts"]))]) for content in history] 
    else:
        contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=question),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=65536,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=sys),
        ],
    )

    response =  client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )

    if JSON:
        return parse_text_to_json(response.text)
    else:
        return response.text
    


#Process a file with Gemini
def process_file_with_gemini(file_data: List[Tuple], sys= '', prompt= '', api_key = os.getenv('GEMINI_API_KEY'), model = "gemini-2.0-flash", JSON = False):
    
    # File data structure: [(filename, file_content), (filename, file_content),...]

    client = genai.Client(api_key=api_key)

    parts_init = []
    

    # make temporary files
    for file_name, file_bytes in file_data:
        tmp_file = tempfile.NamedTemporaryFile(suffix="." + file_name.split(".")[-1], delete=False)

        tmp_file.write(file_bytes)
        tmp_file.close()
    
        # Upload the file
        uploaded_file = client.files.upload(
            file=tmp_file.name,
        )
        parts_init.append(types.Part.from_uri(
                    file_uri=uploaded_file.uri,
                    mime_type=uploaded_file.mime_type,
                ))

        # remove the temporary file
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)

    contents = [
        types.Content(
            role="user",
            parts= parts_init + [types.Part.from_text(text=prompt)],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=65536,
        response_mime_type="text/plain",
        system_instruction=[
            types.Part.from_text(text=sys),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    
    if JSON:
        return parse_text_to_json(response.text)
    else:
        return response.text


def ask_llama(sys, query, api_key = random.choice(os.getenv('Sambanova_Api_Key').split()), model = "DeepSeek-R1-0528", JSON = False):
    for i in range(5):
        SambaNova_Client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.sambanova.ai/v1",
            )
        response = SambaNova_Client.chat.completions.create(
            model=model,
            messages=[{"role":"system","content": sys},{"role":"user","content":query}],
            temperature =  0.1,
            top_p = 0.1,
        )
        ans = response.choices[0].message.content
        if not JSON:
            return ans
        try:
            data = parse_text_to_json(ans)
            return data
        except Exception as e:
            print(e)
            print(response.choices[0].message.content)
