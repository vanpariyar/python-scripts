import os
import sys
import jsonlines
import csv
import time
import httpx
from argparse import ArgumentParser
from loguru import logger
from dotenv import load_dotenv


class EnvVars(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


def fetch_record_by_slug(env, slug):
    """Send POST request to WordPress API to get the article ID by slug"""
    endpoint = f"{env.WP_ENDPOINT}?slug={slug}"
    try:
        response = httpx.get(endpoint, timeout=None)
        if response.status_code != 200:
            logger.error(f"Failed to fetch ID for slug {slug}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.exception(e)
        return None

    return response.json()


def process_jsonl_and_fetch_ids(jsonl_file, env):
    """Process JSONL file, fetch IDs from WordPress, and store results in a list"""
    records = []
    
    with jsonlines.open(jsonl_file) as reader:
        for obj in reader:
            slug = obj.get('slug')
            if not slug:
                logger.error("Missing 'slug' in the JSONL record")
                continue
            
            record_data = (env, slug)
            if record_data:
                logger.info(f"Fetched ID {record_data}")
                record_id = record_data[0]['id']
                if record_id:
                    records.append({'slug': slug, 'id': record_id})
                    logger.info(f"Fetched ID {record_id} for slug {slug}")
                else:
                    logger.error(f"No ID returned for slug {slug}")
            time.sleep(1)  # To avoid rate-limiting

    return records


def save_to_csv(records, output_file):
    """Save the slug and IDs to a CSV file"""
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['slug', 'id'])
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Saved {len(records)} records to {output_file}")


def get_env_vars():
    env = EnvVars(**os.environ)

    env.FILE = os.getenv('FILE')
    env.WP_API_ENDPOINT = os.getenv('WP_ENDPOINT',
                                    'https://www.example.com/wp-json/wp/v2/posts'
                                    '/wp-json/wp/v2/posts')
    env.BATCH_SIZE = int(os.getenv('BATCH_SIZE', 8))
    env.AUTH_USERNAME = os.getenv('WP_USERNAME', None)
    env.AUTH_PASSWORD = os.getenv('WP_PASSWORD', None)
    env.STATUS_FILE = os.getenv('WP_STATUS_FILE', f'/tmp/wp_deletion_status_status.jsonl')
    env.AUTH = (env.AUTH_USERNAME, env.AUTH_PASSWORD)
    env.TIMEOUT_SEC = float(os.getenv('TIMEOUT_SEC', 10))
    env.BULK_SIZE = int(os.getenv('BULK_SIZE', 100))

    return env


def main():
    load_dotenv(os.getenv(".env", None))
    env = get_env_vars()

    parser = ArgumentParser(description='Process JSONL file and fetch IDs')
    parser.add_argument('jsonl_file', type=str, help='Input JSONL file with slugs')
    parser.add_argument('output_csv', type=str, help='Output CSV file to save slugs and IDs')
    args = parser.parse_args()

    # Process JSONL and fetch IDs
    records = process_jsonl_and_fetch_ids(args.jsonl_file, env)

    # Save records to CSV
    save_to_csv(records, args.output_csv)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        sys.exit(1)