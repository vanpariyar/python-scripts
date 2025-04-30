import os
import sys
import argparse
import logging
import pandas as pd
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv

# Import helper functions
sys.path.append(os.path.dirname(__file__))
from utils import compress_image, extract_caption_credit

# === Load .env Variables ===
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
    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
)

# === WordPress Functions ===

def upload_image_to_wp(image_path):
    try:
        filename = os.path.basename(image_path)

        with Image.open(image_path) as img:
            image_data = compress_image(img)

        if not image_data:
            raise ValueError("Compression failed")

        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'image/jpeg',
        }

        response = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/media",
            headers=headers,
            auth=AUTH,
            data=image_data
        )
        response.raise_for_status()
        media = response.json()
        logging.info(f"✅ Uploaded image: {filename} (Media ID: {media['id']})")
        return media['id'], media['source_url']
    except Exception as e:
        logging.error(f"❌ Failed to upload {image_path}: {e}")
        return None

def set_featured_image(post_id, media_id, post_type):
    try:
        url = f"{WP_SITE_URL}/wp-json/wp/v2/{post_type}/{post_id}?context=edit"
        response = requests.post(url, auth=AUTH, json={'featured_media': media_id})
        response.raise_for_status()
        logging.info(f"✅ Set featured image for post ID {post_id}")
    except Exception as e:
        logging.error(f"❌ Failed to set featured image: {e}")

def update_acf_flag(post_id, post_type):
    try:
        url = f"{WP_SITE_URL}/wp-json/wp/v2/{post_type}/{post_id}?context=edit"
        acf_data = {"acf": {"public": {"show_on_homecategory_pages": True}}}
        response = requests.post(url, auth=AUTH, json=acf_data)
        response.raise_for_status()
        logging.info(f"✅ ACF field updated for post ID {post_id}")
    except Exception as e:
        logging.warning(f"⚠️ Failed to update ACF: {e}")

def append_image_block(post_id, image_url, caption, post_type):
    try:
        url = f"{WP_SITE_URL}/wp-json/wp/v2/{post_type}/{post_id}?context=edit"
        post_response = requests.get(url, auth=AUTH)
        post_response.raise_for_status()
        post = post_response.json()

        content = post['content'].get('raw') or post['content'].get('rendered', '')
        block_json = '{"className":"wp-block-image"}'
        caption_html = f'<figcaption class="wp-element-caption">{caption}</figcaption>' if caption else ''
        image_block = (
            f'<!-- wp:image {block_json} -->\n'
            f'<figure class="wp-block-image"><img src="{image_url}" alt=""/>{caption_html}</figure>\n'
            f'<!-- /wp:image -->'
        )

        updated_content = image_block + "\n\n" + content

        update_response = requests.post(url, auth=AUTH, json={'content': updated_content})
        update_response.raise_for_status()
        logging.info(f"✅ Added image block to post ID {post_id}")
    except Exception as e:
        logging.error(f"❌ Failed to append image block: {e}")

# === Main Workflow ===

def process_csv(csv_path, image_dir, post_type):
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            post_id = int(row['content_id'])
            domain = row['domain']
            filename = row['image file name']
            image_path = os.path.join(image_dir, filename)

            logging.info(f"\n--- Processing Post ID: {post_id} | File: {filename} ---")

            if not os.path.exists(image_path):
                logging.error(f"❌ Image file not found: {image_path}")
                continue

            # Extract caption and credit
            caption, credit = extract_caption_credit(image_path)
            final_caption = f"Photo Courtesy: {credit}" if credit else None

            # Upload
            media_info = upload_image_to_wp(image_path)
            if media_info:
                media_id, image_url = media_info
                set_featured_image(post_id, media_id, post_type)
                update_acf_flag(post_id, post_type)
                append_image_block(post_id, image_url, final_caption, post_type)
    except Exception as e:
        logging.critical(f"❌ Fatal error processing CSV: {e}")

# === CLI ===

def main():
    parser = argparse.ArgumentParser(description="Attach local images to WordPress posts")
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--images', required=True, help='Path to folder of images')
    parser.add_argument('--post_type', default='posts', help='WordPress post type (default: posts)')
    args = parser.parse_args()

    process_csv(args.csv, args.images, args.post_type)

if __name__ == "__main__":
    main()
