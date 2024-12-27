Sure! Below is a `README.md` template for your project that describes the setup, usage, and requirements for the Python script that uploads files with multi-level folder structures to the Internet Archive, with support for environment variables.

---

# Internet Archive Multi-Level Folder Uploader

This Python script allows you to upload files to an existing item on the Internet Archive, while preserving the directory structure. The script supports multi-level folder uploads and can update metadata for an existing item. Additionally, it leverages environment variables for configuration to improve security and flexibility.

## Features
- Upload files recursively from a folder, preserving directory structure.
- Update metadata for an existing item on the Internet Archive.
- Support for environment variables for API key, secret key, item identifier, and folder path.
- Optionally load environment variables from a `.env` file.

## Prerequisites
Before running the script, ensure you have the following:
- **Python 3.x** installed.
- An **Internet Archive** account and **API key** (Access Key and Secret Key).
- Access to the **existing item** on the Internet Archive you wish to update.

## Requirements

- Python 3.x
- `internetarchive` Python package
- `python-dotenv` (optional, for loading environment variables from `.env` file)

### Install Required Libraries

To install the required Python libraries, run the following:

```bash
pip install internetarchive python-dotenv
```

## Setting Up Environment Variables

### 1. Set Environment Variables

There are two ways to set up your environment variables: either manually in your terminal or using a `.env` file.

#### Method 1: Set Environment Variables in Shell

On **macOS/Linux**:

```bash
export INTERNET_ARCHIVE_ACCESS_KEY="your_access_key"
export INTERNET_ARCHIVE_SECRET_KEY="your_secret_key"
export ITEM_NAME="existing_item_identifier"
export ROOT_DIR="/path/to/your/folder"
```

On **Windows (CMD)**:

```bash
set INTERNET_ARCHIVE_ACCESS_KEY=your_access_key
set INTERNET_ARCHIVE_SECRET_KEY=your_secret_key
set ITEM_NAME=existing_item_identifier
set ROOT_DIR=C:\path\to\your\folder
```

#### Method 2: Use `.env` File (Recommended)

Create a `.env` file in the root of your project and add the following content:

```bash
# .env file
INTERNET_ARCHIVE_ACCESS_KEY=your_access_key
INTERNET_ARCHIVE_SECRET_KEY=your_secret_key
ITEM_NAME=existing_item_identifier
ROOT_DIR=/path/to/your/folder
```

### 2. Verify Environment Variables

The script will automatically load environment variables using `python-dotenv` (if a `.env` file exists) or fetch them directly from the shell environment using `os.getenv()`. The script will check that all required variables are set before proceeding.

## Script Overview

The script performs the following tasks:
- **Authentication**: Using your Internet Archive API access key and secret key.
- **Metadata Update**: Updates the metadata for an existing item (e.g., title, description, creator).
- **File Upload**: Recursively uploads files from a specified folder, preserving the folder structure.

## Usage

### 1. Configure Environment Variables

Ensure you have set your environment variables as described above. You can either set them directly in your terminal or use a `.env` file.

### 2. Run the Script

Once the environment variables are configured, you can run the script as follows:

```bash
python upload_folders.py
```

This will:
- Update the metadata for the existing item on the Internet Archive.
- Upload all files from the specified folder, preserving the directory structure.
- Print the status of each file being uploaded.

### 3. Verify Upload

After the script finishes running, you can view the uploaded files and updated metadata on your Internet Archive item page:

```
https://archive.org/details/{ITEM_NAME}
```

For example, if your `ITEM_NAME` is `my_uploaded_item`, visit:

```
https://archive.org/details/my_uploaded_item
```

## Script Details

### Environment Variables
- `INTERNET_ARCHIVE_ACCESS_KEY`: Your **Internet Archive Access Key**.
- `INTERNET_ARCHIVE_SECRET_KEY`: Your **Internet Archive Secret Key**.
- `ITEM_NAME`: The identifier for the existing item on the Internet Archive.
- `ROOT_DIR`: The root directory of the folder structure you want to upload.

### Example `.env` File

```bash
# .env file
INTERNET_ARCHIVE_ACCESS_KEY=your_access_key
INTERNET_ARCHIVE_SECRET_KEY=your_secret_key
ITEM_NAME=existing_item_identifier
ROOT_DIR=/path/to/your/folder
```

### Example Folder Structure

If your folder structure is:

```
root/
  ├── folder1/
  │   ├── file1.txt
  │   └── file2.txt
  └── folder2/
      └── file3.txt
```

The Internet Archive item will preserve the structure as follows:

```
root/
  folder1/
    file1.txt
    file2.txt
  folder2/
    file3.txt
```

## Troubleshooting

### Missing Environment Variables

If you receive an error like:

```
EnvironmentError: Missing required environment variables
```

Make sure that all required environment variables (`INTERNET_ARCHIVE_ACCESS_KEY`, `INTERNET_ARCHIVE_SECRET_KEY`, `ITEM_NAME`, and `ROOT_DIR`) are correctly set either in your shell or in the `.env` file.

### Permissions

Ensure that your **Internet Archive account** has the necessary permissions to upload or update items. You must own or have edit access to the item.

### File Upload Errors

If you encounter issues uploading specific files, verify the file paths and ensure that the files exist at the specified location. You can print debugging information by adding `print()` statements in the script.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Conclusion

This Python script makes it easy to upload an entire folder structure to the Internet Archive, preserving directory structure and updating metadata for an existing item. Using environment variables for sensitive data like API keys and item identifiers enhances security and flexibility across different environments.

If you encounter any issues or have suggestions for improvement, feel free to open an issue or submit a pull request!