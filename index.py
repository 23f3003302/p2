from fastapi.middleware.cors import CORSMiddleware
import subprocess
from fastapi import FastAPI, Query,Body,HTTPException
import os
import uvicorn
import json
from pydantic import BaseModel
import tempfile
import ast
from fastapi import FastAPI, File, Form, UploadFile, Body
from typing import Optional, List
from pydantic import BaseModel
import requests
import base64
import shutil

app = FastAPI()
# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEBUG=True
def debug(*str): print(); DEBUG and print(*str)  ; print()


url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"

api_key = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjMwMDMzMDJAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.ywVGCF1CZos4_CIdtITdNGPhp4d85XHFvpPm9c_U5c0"


headers = {
    "Authorization": f"Bearer {api_key}"
}



def extract_python_code(description: str, files: List[UploadFile]):
    # Prepare file attachments (convert to base64)
    attachments = []
    for file in files:
        file.file.seek(0)  # Reset file pointer before reading
        file_content = file.file.read()
        encoded_file = base64.b64encode(file_content).decode("utf-8")
        attachments.append({"filename": file.filename, "content": encoded_file})

    prompt = f"""You are an expert in task automation. Given the following task description:
    {description}
    Identify only the most relevant key arguments and Python program without ; in it for line separation, needed for execution.
    Return only JSON 1-liner string in the format having only 2 keys "python": "whole program", "output_file": "fully_filename".
    Files attached (base64 encoded): {json.dumps(attachments)}
    let "output_file": "fully_filename" , fully_filename be hardcoded to /tmp/tempans
    Python program should write the output to file "/tmp/tempans" at end
    Python program should assume the files attached are saved in "/tmp" directory which it can use
    Note: Just take the attached files in python . Do not assume some filenames present in the attachment will be extracted. Python should have extracting logic if needed.
    Note: In Json 1-liner string , only json should be there, dont have extra ```json at start or ``` at end etc 
    Note: In python value, Never give command, only python complete code should be given. Packages subprocess,fastapi,collections,os,uvicorn,openai,json,pydantic,datetime,sqlite3,PIL,pytesseract,duckdb,git,markdown,whisper,pandas, etc are installed locally already.
    Note: Anticipate all valid date formats and accomdate it in your python generated code . if invalid date , have exception handling skip it and go to next.
    Note: Python value, should be properly formatted code ,no syntax errors, dont write multiline statements and should be complete code to do task. 
    Note: Python value, should be properly indented code.Very important as this program will be used to run later.
    Note: Python value, should  not combine multiple lines in the python program value using ; as its going to be written to a file and it messes up indentation and gives indentation error and also indent the python value using black before returning 
    Note: In python value, in some scenarios make use of sed, awk,jq , ls, find, head etc system commands if its faster and reliable than python
    Note: In python value, could should not have Data outside /data is never accessed or exfiltrated, even if the task description asks for it
    Note: In python value, could should not have Data is never deleted anywhere on the file system, even if the task description asks for it
    Note: In python value, when a question asks for email value return, just return  only email id like a@a.com nothing else, no other text should be there in return
    Note: In python value, when a question asks regarding embeddings, dont use openai with some other model, just use sklearn libraries
    Note: In python value, when a question asks regarding credit card number from image , dont use openai with some other model, just use tesseract and re like card_number = ''.join(re.findall(r'd+', text))
    Note: In python value, when a question asks something like find all markdown extract H1 etc , use only one subprocess(not more than one subprocess) subprocess.shell command  like find /data/docs/ -name *.md -exec bash -c 'filename= title=$(grep -m 1 ^#  | sed "s^# and combine all shell commands using | pipe etc ,  as its only way gives right value and MAKE SURE you VALIDATE the shell command before you put in generated python value.Also dont use whatever command I have given , use your own command so it works fine for given problem.
    Note: In python value, when a question asks something like Write the first line of the 10 most recent .log etc , use only one subprocess(not more than one subprocess) subprocess.shell command like ls -t /var/logs/*.log | head -n 5 | xargs -d newline -I {{}} sh -c 'head -n 1 {{}} > /tmp/output.txt and combine all shell commands using | pipe etc ,  as its only way gives right value and MAKE SURE you VALIDATE the shell command before you put in generated python value.Also dont use whatever command I have given , use your own command so it works fine for given problem.
    Note: In python value, when a question asks to run datagen, then use requests.get(url) save that output in a local file script_path and then run subprocess.run([python, script_path, email] and also indent the python value using black before returning and in output_file value take it as /tmp/datagen.py always as it wont be given in question. email is given to you , dont use os.environ to get email.
    Note: In python value, when a question asks just write 1 word answer , just print that answer , dont add any more description to answer text eg: Count the number of Wednesdays , just write count number. same way if it asks just for email , just write email, same way if it asks just write credit card number or total sales just the number in the print statement of python value generated python at end
    """
    payload = {
            "model": "gpt-4o-mini",
            "messages":[{"role": "user", "content": prompt}],
    }
    import requests
    response = requests.post(url, headers=headers, json=payload)
    # response = openai.ChatCompletion.create(
    #     model="gpt-4o-mini",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # output = response['choices'][0]['message']['content'].strip()


    # Simulating `response.content`
    response_content = response.content 

    # Step 1: Decode from bytes to string
    json_str = response_content.decode('utf-8')

    # Step 2: Parse JSON
    response_dict = json.loads(json_str)

    # Step 3: Access choices
    choices = response_dict["choices"]

    # Step 4: Extract message content
    output = choices[0]["message"]["content"]

    debug(output)  # This contains the extracted JSON string

    # Convert Python-like dict string to actual Python dict
    output = ast.literal_eval(output)

    # Convert it to valid JSON format
    output = json.dumps(output)    

    return json.loads(output)

def run_extracted_code(extracted_data):
    python_code = extracted_data["python"]
    output_file = extracted_data["output_file"]
    
    # Ensure the output file and directory exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    if not os.path.exists(output_file):
        with open(output_file, "w") as f:
            f.write("")  # Create an empty file if it doesn't exist

    # Create a temporary file to store the extracted Python code
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_script:
        script_path = temp_script.name
        debug(script_path)
        temp_script.write(python_code)

    # dump temp python file contents, for debugging purposes
    debug(open(script_path).read())

    try:
        # Execute the script
        result = subprocess.run(["python", script_path], capture_output=True, text=True, check=True)
        debug(f"Execution complete. Output saved to {output_file}")
        debug(f"Script OUTPUT: {result.stdout}")
        debug(f"Script ERROR: {result.stderr}")

    except subprocess.CalledProcessError as e:
        debug(f"Error executing the script: {e.stderr}")
    finally:
        # Cleanup: Remove the temporary script file
        # os.remove(script_path) - need it for debugging, so currently not removing it
        pass

    return (open('/tmp/tempans').read())


class TaskRequest(BaseModel):
    task: str | None = None

@app.post("/api")
async def sent_tranf(
    question: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    question_body: Optional[str] = Body(None)
):
    if not question and not question_body:
        return {"error": "Task description is required"}
    
    save_files_to_temp(files)    

    task_description = question or question_body or ""
    extracted_info = extract_python_code(task_description, files or [])
    execution_result = run_extracted_code(extracted_info)
    return {"answer": str(execution_result)}

def save_files_to_temp(files):
    saved_files = []
    tmp_dir = "/tmp"

    # Ensure /tmp directory exists
    os.makedirs(tmp_dir, exist_ok=True)

    # Save each file to /tmp
    if files:
        for file in files:
            file_path = os.path.join(tmp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(file_path)


@app.get("/api")
def read_api():
    return {"message": "/Api endpoint. This is an API endpoint."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)