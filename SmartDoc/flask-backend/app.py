from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shutil
import PyPDF2
from huggingface_hub import hf_hub_download
import threading
from llama_cpp import Llama
import re
import time
from concurrent.futures import ThreadPoolExecutor
import logging

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
SORTED_FOLDER = 'sorted'

# Ensure the upload and sorted folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SORTED_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Download and load the LLaMA model
model_name_or_path = "TheBloke/Llama-2-13B-chat-GGML"
model_basename = "llama-2-13b-chat.ggmlv3.q5_1.bin" # the model is in bin format
model_path = hf_hub_download(repo_id=model_name_or_path, filename=model_basename)

logger.info("Model Path - %s", model_path)

lcpp_llm = Llama(   
    model_path=model_path,
    n_threads=2,  # CPU cores
    n_batch=512,  # Should be between 1 and n_ctx, consider the amount of VRAM in your GPU.
    n_gpu_layers=12 # Change this value based on your model and your GPU VRAM pool.
)

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

def doc_class(result):
    pattern = r"Predicted Class \(One Word\):\\s(\w+)"
    match = re.search(pattern, result)
    if match:
        return match.group(1)
    else:
        return "Unknown"

def classify_document(file):
    text = extract_text_from_pdf(file)
    cleaned_text = clean_text(text)

    logger.info(f"Extracted text from {file.filename}: {cleaned_text[:100]}")  # Print first 100 characters of extracted text for debugging

    # Save the file
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Example of using the Llama model for classification
    prompt_template = f'''SYSTEM: Guess the type of Document for example is it (Resume, contract, NewsPaper, Letter, Email):

    USER: This is my Text -  {cleaned_text[:500]} Guess My document type on base of text from (Resume,contract,NewsPaper,Form,Letter,Email).

    Predicted Class (One Word):'''
    logger.info(prompt_template)

    start_time = time.perf_counter()
    try:
        response = lcpp_llm(prompt=prompt_template, max_tokens=512, temperature=0.5, top_p=0.95,
                            repeat_penalty=1.2, top_k=150, echo=True)
    except Exception as e:
        logger.error("Error during model inference: %s", str(e))
        return "Error", 0

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    logger.info("Elapsed time: %s", elapsed_time)
    logger.info("Predicted Class: %s", response["choices"][0]["text"])

    document_class = doc_class(response["choices"][0]["text"])

    # Move the file to sorted folder
    sorted_path = os.path.join(SORTED_FOLDER, file.filename)
    shutil.move(file_path, sorted_path)

    return document_class, elapsed_time

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
