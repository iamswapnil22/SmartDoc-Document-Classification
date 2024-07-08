from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import shutil
import PyPDF2
import re
import google.generativeai as genai
import zipfile
from concurrent.futures import ThreadPoolExecutor
import logging

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Configure logging
log_filename = 'app.log'
log_file_path = os.path.join(os.getcwd(), log_filename)

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler for storing logs to file
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Initialize logger for the current module
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

    # logger.info(f"Extracted text from {file.filename}: {cleaned_text[:100]}")  # Print first 100 characters of extracted text for debugging

    # Prepare Gemini input
    input_prompt = f'''SYSTEM: Guess the type of Document for example is it (Resume, contract, NewsPaper, Letter, Email, Form):

    USER: This is my Text -  {cleaned_text[:500]} Guess My document type on base of text from (Resume,contract,NewsPaper,Form,Letter,Email).'''

    # logger.info("Input Prompt: %s", input_prompt)

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([input_prompt, cleaned_text])
        predicted_class = response.text.strip()
    except Exception as e:
        logger.error("Error during Gemini model inference: %s", str(e))
        return "Unknown", 0

    logger.info("Predicted Class: %s", predicted_class)

    # Move the file to sorted folder based on predicted class
    sorted_path = os.path.join(SORTED_FOLDER, predicted_class)
    os.makedirs(sorted_path, exist_ok=True)
    
    # Adjust file path for moving and logging
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    sorted_file_path = os.path.join(sorted_path, file.filename)
    
    # Move file and handle any errors
    try:
        shutil.move(file_path, sorted_file_path)
    except FileNotFoundError as e:
        logger.error(f"Error moving file {file.filename}: {str(e)}")
        return "Unknown", 0
    
    return predicted_class, 0  # Return predicted class and elapsed time (set as 0 for now)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    logger.info("Files received: %s", [file.filename for file in files])

    results = []
    for file in files:
        document_class, elapsed_time = classify_document(file)
        results.append({"file": file.filename, "class": document_class, "time": elapsed_time})

    # Provide download link to the sorted documents
    download_link = '/download'
    results.append({"message": "Files uploaded and classified successfully.", "download_link": download_link})
    
    return jsonify(results), 200

@app.route('/download')
def download():
    # Zip the 'sorted' folder
    zip_filename = 'sorted_documents.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(SORTED_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.relpath(file_path, SORTED_FOLDER))

    # Serve the zip file for download
    return send_from_directory('.', zip_filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
