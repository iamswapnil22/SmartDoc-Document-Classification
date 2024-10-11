from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS, cross_origin
import io
import PyPDF2
import re
import google.generativeai as genai
import zipfile
import logging
from google.cloud import storage
import os
import zip_to_gcp

app = Flask(__name__)
CORS(app)

log_filename = 'app.log'
log_file_path = log_filename

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Google Cloud Storage bucket name
BUCKET_NAME = 'smartdoc-files-bucket'

def upload_to_gcs(file, destination_blob_name):
    """Upload a file to GCS and return its public URL."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file)
    blob.make_public()
    return blob.public_url

def move_file_in_gcs(source_blob_name, destination_blob_name):
    """Move a file within the GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(source_blob_name)
    new_blob = bucket.rename_blob(blob, destination_blob_name)
    return new_blob.public_url

def cleanup_bucket(bucket_name):
    """Clean up all files in the specified GCS bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # List all blobs in the bucket
    blobs = bucket.list_blobs()
    for blob in blobs:
        blob.delete()  # Delete the blob
        logger.info(f"Deleted blob: {blob.name}")

    logger.info(f"All files in bucket {bucket_name} have been deleted.")

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    text = re.sub(r'(\w)\s*(\n)\s*(\w)', r'\1\2\3', text)
    return text

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    pdf_text = []
    for page in reader.pages:
        content = page.extract_text()
        pdf_text.append(content)
    return " ".join(pdf_text)

def classify_document(file, file_name):
    text = extract_text_from_pdf(file)
    cleaned_text = clean_text(text)
    
    input_prompt = f'''SYSTEM: Guess the type of Document (Resume, contract, NewsPaper, Letter, Email, None):
    
    USER: This is my Text -  {cleaned_text[:500]} Guess My document type.'''

    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content([input_prompt, cleaned_text])
        predicted_class = response.text.strip()
    except Exception as e:
        logger.error("Error during Gemini model inference: %s", str(e))
        return predicted_class, 0

    logger.info("Predicted Class: %s", predicted_class)

    # Move file in GCS
    sorted_file_path = f'{predicted_class}/{file_name}'
    public_url = move_file_in_gcs(file_name, sorted_file_path)
    
    return predicted_class, public_url

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({"status": "success", "data": "This is a test API response!"})



@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400

    files = request.files.getlist('files')
    logger.info("Files received: %s", [file.filename for file in files])

    results = []
    for file in files:
        # Upload the file to GCS
        public_url = upload_to_gcs(file, file.filename)

        # Continue with the document classification logic
        document_class, public_url = classify_document(file, file.filename)
        results.append({"file": file.filename, "class": document_class, "url": public_url})

    # Process zipping and uploading all folders after the files are classified
    bucket_name = 'smartdoc-files-bucket'  # Your GCS bucket name
    zip_url = zip_to_gcp.zip_and_upload_all_folders(bucket_name)

    # Return the URL of the zip file for downloading
    if zip_url:
        results.append({"message": "Files uploaded and classified successfully.", "download_link": zip_url})
    else:
        results.append({"message": "Files uploaded and classified successfully, but zip creation failed."})

    # cleanup_bucket(bucket_name)

    return jsonify(results), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)