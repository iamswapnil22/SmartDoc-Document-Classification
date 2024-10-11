import os
import zipfile
import shutil
from google.cloud import storage
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Google Cloud Storage client
def initialize_storage_client():
    return storage.Client()

# List all blobs (files) in a folder
def list_files_in_folder(bucket, folder_name):
    blobs = bucket.list_blobs(prefix=folder_name)
    return [blob for blob in blobs if not blob.name.endswith('/')]

# Download files to local directory
def download_files(bucket, folder_name, local_folder):
    blobs = list_files_in_folder(bucket, folder_name)
    if not os.path.exists(local_folder):
        os.makedirs(local_folder)

    for blob in blobs:
        local_file_path = os.path.join(local_folder, os.path.basename(blob.name))
        blob.download_to_filename(local_file_path)

# Create a single ZIP file containing all folders
def create_zip_file(source_folders, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for folder in source_folders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(folder))
                    zipf.write(file_path, arcname)

# Upload ZIP file to Google Cloud Storage
def upload_to_bucket(bucket, local_file_path, destination_blob_name):
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)
    blob.make_public()
    return blob.public_url

def zip_and_upload_all_folders(bucket_name, output_folder='zipped_folders'):
    try:
        client = initialize_storage_client()
        bucket = client.get_bucket(bucket_name)

        blobs = bucket.list_blobs()
        folders = set([blob.name.split('/')[0] for blob in blobs if '/' in blob.name])

        temp_dir = '/tmp/smartdoc_downloads'  # Adjust for Windows if necessary
        os.makedirs(temp_dir, exist_ok=True)

        local_folders = []
        for folder in folders:
            logging.info(f"Processing folder: {folder}")
            local_folder = os.path.join(temp_dir, folder)
            download_files(bucket, folder, local_folder)
            local_folders.append(local_folder)

        timestamp = time.strftime("%Y%m%d-%H%M%S")
        combined_zip_name = f'all_folders_{timestamp}.zip'
        combined_zip_path = f'/tmp/{combined_zip_name}'
        
        create_zip_file(local_folders, combined_zip_path)

        destination_blob_name = f'{output_folder}/{combined_zip_name}'
        zip_url = upload_to_bucket(bucket, combined_zip_path, destination_blob_name)
        logging.info(f"Combined ZIP file uploaded: {zip_url}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

    finally:
        # Clean up
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        if os.path.exists(combined_zip_path):
            os.remove(combined_zip_path)

    return zip_url

if __name__ == '__main__':
    bucket_name = 'smartdoc-files-bucket'  # Your GCS bucket name
    zip_and_upload_all_folders(bucket_name)
