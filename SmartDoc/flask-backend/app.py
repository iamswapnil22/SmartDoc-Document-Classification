from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shutil
import PyPDF2
from huggingface_hub import hf_hub_download
from concurrent.futures import ThreadPoolExecutor
import logging
import re
import time
import google.generativeai as genai

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini model from Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

UPLOAD_FOLDER = 'uploads'
SORTED_FOLDER = 'sorted'

# Ensure the upload and sorted folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SORTED_FOLDER, exist_ok=True)

def clean_text(text):
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing spaces
    text = text.strip()
    # Replace erroneous newlines within words (optional)
    text = re.sub(r'(\w)\s*(\n)\s*(\w)', r'\1\2\3', text)
    return text

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    pdf_text = []
    for page in reader.pages:
        content = page.extract_text()
        pdf_text.append(content)
    return " ".join(pdf_text)

def classify_document(file):
    text = extract_text_from_pdf(file)
    cleaned_text = clean_text(text)

    logger.info(f"Extracted text from {file.filename}: {cleaned_text[:100]}")  # Print first 100 characters of extracted text for debugging

    # Prepare Gemini input
    input_prompt = f'''SYSTEM: Guess the type of Document for example is it (Resume, contract, NewsPaper, Letter, Email, Form):

    USER: This is my Text -  {cleaned_text[:500]} Guess My document type on base of text from (Resume,contract,NewsPaper,Form,Letter,Email).'''

    logger.info("Input Prompt: %s", input_prompt)

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([input_prompt, cleaned_text])
        predicted_class = response.text
    except Exception as e:
        logger.error("Error during Gemini model inference: %s", str(e))
        return "Unknown", 0

    logger.info("Predicted Class: %s", predicted_class)

    # Move the file to sorted folder
    sorted_path = os.path.join(SORTED_FOLDER, file.filename)
    shutil.move(file.filename, sorted_path)

    return predicted_class, 0  # Return predicted class and elapsed time (set as 0 for now)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    logger.info("Files received: %s", [file.filename for file in files])

    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(classify_document, file): file for file in files}
        for future in futures:
            try:
                document_class, elapsed_time = future.result()
                results.append({"file": futures[future].filename, "class": document_class, "time": elapsed_time})
            except Exception as e:
                results.append({"file": futures[future].filename, "error": str(e)})
                logger.error("Error processing file %s: %s", futures[future].filename, str(e))

    return jsonify(results), 200

if __name__ == '__main__':
    app.run(debug=True)
