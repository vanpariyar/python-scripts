import os
import internetarchive
from internetarchive import upload
from dotenv import load_dotenv  # To load .env file if present

# Load environment variables from a .env file, if it exists
load_dotenv()

# Fetch environment variables
access_key = os.getenv("INTERNET_ARCHIVE_ACCESS_KEY")
secret_key = os.getenv("INTERNET_ARCHIVE_SECRET_KEY")
item_name = os.getenv("ITEM_NAME")
root_dir = os.getenv("ROOT_DIR")

# Ensure required environment variables are set
if not all([access_key, secret_key, item_name, root_dir]):
    raise EnvironmentError("Missing required environment variables")

# Set up the session with your credentials
session = internetarchive.get_session(access_key=access_key, secret_key=secret_key)

# Define updated metadata (optional)
updated_metadata = {
    "title": "Updated Title of the Item",
    "creator": "Your Name",
    "subject": "Folder Structure Upload",
    "description": "This is an updated folder structure upload.",
}

# Get the existing item from Internet Archive
item = internetarchive.get_item(item_name, session=session)

# Update the metadata for the existing item (optional)
item.metadata.update(updated_metadata)
item.metadata.commit()

# Function to upload files recursively while preserving folder structure
def upload_directory(item_name, root_dir, session):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Get the relative path of the file within the root directory
            relative_path = os.path.relpath(file_path, root_dir)
            
            # Upload the file with the preserved relative path
            print(f"Uploading file: {relative_path}")
            upload(item_name, files=[file_path], metadata=item.metadata, session=session, file_path=relative_path)

# Start the upload process
print(f"Updating metadata and uploading files for {item_name}...")

# Call the function to upload files and preserve directory structure
upload_directory(item_name, root_dir, session)

# Done!
print(f"Upload process completed. Visit your item here: https://archive.org/details/{item_name}")