import pandas as pd
import requests
import argparse
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

# === Load Environment Variables ===
load_dotenv()

WP_SITE_URL = os.getenv("WP_SITE_URL")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
AUTH = (WP_USERNAME, WP_APP_PASSWORD)

# === Logging Setup ===
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_filename = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_filename, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# === Functions ===

def upload_image_to_wp(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content
        filename = os.path.basename(image_url.split("?")[0])

        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'image/jpeg',
        }

        upload_response = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/media",
            headers=headers,
            auth=AUTH,
            data=image_data
        )
        upload_response.raise_for_status()

        media = upload_response.json()
        logging.info(f"✅ Uploaded image: {filename} (Media ID: {media['id']})")
        return media['id'], media['source_url']
    except Exception as e:
        logging.error(f"❌ Failed to upload image: {e}")
        return None

def set_featured_image(post_id, media_id, post_type):
    try:
        post_url = f"{WP_SITE_URL}/wp-json/wp/v2/{post_type}/{post_id}"
        response = requests.post(post_url, auth=AUTH, json={'featured_media': media_id})
        response.raise_for_status()
        logging.info(f"✅ Set featured image for post ID {post_id}")
    except Exception as e:
        logging.error(f"❌ Failed to set featured image: {e}")

def append_image_block(post_id, image_url, post_type):
    try:
        post_url = f"{WP_SITE_URL}/wp-json/wp/v2/{post_type}/{post_id}"
        response = requests.get(post_url, auth=AUTH)
        response.raise_for_status()
        post = response.json()

        content = post['content'].get('raw') or post['content'].get('rendered', '')

        new_content = content + f'\n<!-- wp:image -->\n<figure class="wp-block-image"><img src="{image_url}" alt=""/></figure>\n<!-- /wp:image -->'

        update_response = requests.post(post_url, auth=AUTH, json={'content': new_content})
        update_response.raise_for_status()
        logging.info(f"✅ Appended image block to post ID {post_id}")
    except Exception as e:
        logging.error(f"❌ Failed to append image block: {e}")

def process_csv(csv_path, post_type):
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            post_id = int(row['post_id'])
            image_url = row['image_url']
            logging.info(f"\n--- Processing post_id={post_id} ---")

            media_info = upload_image_to_wp(image_url)
            if media_info:
                media_id, uploaded_image_url = media_info
                set_featured_image(post_id, media_id, post_type)
                append_image_block(post_id, uploaded_image_url, post_type)
    except Exception as e:
        logging.critical(f"❌ Critical failure while processing CSV: {e}")

# === CLI ===
def main():
    parser = argparse.ArgumentParser(description="Upload images from CSV to WordPress posts")
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--post_type', default='posts', help='WordPress post type (default: posts)')
    args = parser.parse_args()

    process_csv(args.csv, args.post_type)

if __name__ == "__main__":
    main()