from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import shutil
import PyPDF2

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
SORTED_FOLDER = 'sorted'

# Ensure the upload and sorted folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(SORTED_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({"error": "No files part in the request"}), 400
    
    files = request.files.getlist('files')
    print("Files received:", [file.filename for file in files])
    
    def extract_text_from_pdf(pdf_file):
        reader = PyPDF2.PdfReader(pdf_file)
        pdf_text = []
        for page in reader.pages:
            content = page.extract_text()
            pdf_text.append(content)
        return pdf_text

    for file in files:
        text = extract_text_from_pdf(file)
        print(f"Extracted text from {file.filename}: {text[:100]}")  # Print first 100 characters of extracted text for debugging

        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        
        # Dummy sorting logic: Move the file to sorted folder
        sorted_path = os.path.join(SORTED_FOLDER, file.filename)
        shutil.move(file_path, sorted_path)
    
    return jsonify({"message": f"{len(files)} files uploaded and sorted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
