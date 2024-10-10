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

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Configure logging
log_filename = 'app.log'
log_file_path = log_filename

# Configure root logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a file handler for storing logs to file
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

# Initialize logger for the current module
logger = logging.getLogger(__name__)

# Initialize Gemini model from Google Generative AI
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
    
    input_prompt = f'''SYSTEM: Guess the type of Document (Resume, contract, NewsPaper, Letter, Email, Form):
    
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

    # Append the download link to the response
    download_link = request.host_url + 'download'
    print("THIS IS THE DOWNLOAD LINK")
    print(download_link)
    results.append({"message": "Files uploaded and classified successfully.", "download_link": download_link})

    return jsonify(results), 200

@app.route('/download', methods=['GET'])
def download():
    # Define the zip filename
    zip_filename = 'sorted_documents.zip'
    
    # Create a zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)

        # List all folders in the bucket
        blobs = bucket.list_blobs()
        folders = set()  # To store unique folder names
        
        for blob in blobs:
            # Get the folder name from the blob name
            folder_name = blob.name.split('/')[0]  # Assuming the structure is like 'folder/file.pdf'
            if folder_name:
                folders.add(folder_name)

        # Loop through each folder and add its files to the zip
        for folder in folders:
            # List files in the folder
            for blob in bucket.list_blobs(prefix=f"{folder}/"):
                file_name = blob.name
                # Create a temporary file to download the blob to
                temp_file_path = f"/tmp/{file_name.split('/')[-1]}"
                blob.download_to_filename(temp_file_path)
                zip_file.write(temp_file_path, arcname=file_name)  # Use arcname to preserve the folder structure
                os.remove(temp_file_path)  # Remove the temporary file after adding it to the zip

    # Upload the zip file to GCS and get its public URL
    public_url = upload_to_gcs(zip_filename, zip_filename)

    # Clean up the local zip file if necessary
    os.remove(zip_filename)  # Optionally remove the local zip file if not needed
    print(public_url)
    return jsonify({"download_url": public_url}), 200

if __name__ == '__main__':
    app.run(debug=True)
