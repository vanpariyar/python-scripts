import os
import sys
import yaml
import jsonlines
import time
import httpx
from argparse import ArgumentParser
from loguru import logger
from multiprocessing import Pool
from dotenv import load_dotenv


class EnvVars(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)

language_map = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "it": "Italian",
    "ja": "Japanese",
    "pt": "Portuguese",
    "ru": "Russian",
    "es": "Spanish",
    "da": "Danish",
    "nl": "Dutch",
    "no": "Norwegian",
    "sv": "Swedish",
    "el": "Greek",
    "id": "Indonesian",
    "ko": "Korean",
    "ms": "Malay",
    "pl": "Polish",
    "th": "Thai",
    "tr": "Turkish",
    "zh": "Traditional Chinese",
    "ro": "Romanian"
}

def fetch_records(page_url):
    try:
        response = httpx.get(page_url, timeout=None)
        if response.status_code != 200:
            print(f"Failed to fetch data for page {page_url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.exception(e)

    return response.json()

def fetch_all_records(env):
    all_records = []
    article_titles_url = env.WP_ARTICLE_TITLES_ENDPOINT
    
    first_page_data = fetch_records(f"{article_titles_url}&_envelope")
    all_records.extend(first_page_data.get('body', []))

    total_pages = int(first_page_data.get('headers', {}).get('X-WP-TotalPages', 0))
    total_records = int(first_page_data.get('headers', {}).get('X-WP-Total', 0))
    logger.info(f"Total pages : {total_pages}, Total records : {total_records}")
    
    if total_pages > 1:
        page_urls = [f"{article_titles_url}&page={page}" for page in range(2, total_pages + 1)] 
        with Pool(env.BATCH_SIZE) as pool:
            for i in range(0, len(page_urls), env.BULK_SIZE):
                    current_batch = []
                    batch = page_urls[i:i + env.BULK_SIZE]
                    current_batch.extend(pool.map(fetch_records, batch))
                    for result in current_batch:
                        all_records.extend(result)
                    logger.info(f"Submitted {len(batch)} records for retrieve, total submitted: {i + len(batch)}")

    return all_records
    

def prepare_annotation_record(record, args, prompt_template):
    """Prepare a record ready to be processed by OpenAI generation"""
    if 'tin_locale' in record and '_' in record['tin_locale']:
        required_language = record['tin_locale'].split('_')[0]
    else:
        required_language = "en"

    prompt_message_vars = {
        "keyword": record["title"]["rendered"],
        "target_language": language_map[required_language],
        "num_keywords": args.num_keywords,
        "article_id": record["id"]
    }
    system_message = prompt_template.pop("system_message").format(**prompt_message_vars)
    user_message = prompt_template.pop("user_message").format(**prompt_message_vars)
    prep_record = prompt_template
    prep_record["messages"] = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
    info = record.get("info", {})
    info["keyword_original"] = record["title"]["rendered"]
    if 'tin_locale' in record and '_' in record['tin_locale']:
        info["source_language"] = record['tin_locale'].split('_')[0]
        info["target_language"] = record['tin_locale'].split('_')[0]
    else:
        info["source_language"] = args.source_language
        info["target_language"] = args.target_language
    info["prompt_template"] = args.prompt_template
    info["visits"] = 10
    info["category"] = record['amg_category']['title'][0]
    prep_record["metadata"] = info

    return prep_record

def log_detailed_humane_time(seconds):
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes and {seconds % 60} seconds"
    else:
        return f"{seconds // 3600} hours, {(seconds % 3600) // 60} minutes, and {(seconds % 3600) % 60} seconds"
    
def get_env_vars():
    env = EnvVars(**os.environ)

    env.WP_ARTICLE_TITLES_ENDPOINT = os.getenv('WP_ARTICLE_TITLES_ENDPOINT')
    env.BATCH_SIZE = int(os.getenv('BATCH_SIZE', 8))
    env.BULK_SIZE = int(os.getenv('BULK_SIZE', 100))

    return env

def main():
    """Prep generation of keyword """
    load_dotenv(os.getenv(".env", None))
    env = get_env_vars()

    parser = ArgumentParser(description='Keyword Generation Job')
    parser.add_argument('prep_file', type=str)
    parser.add_argument('predicted_file', type=str)
    parser.add_argument('prompt_template', type=str)
    parser.add_argument('num_keywords', type=int)
    args = parser.parse_args()

    if not 1 <= args.num_keywords <= 10:
        logger.error("Unsupported num_keywords value: %s", args.num_keywords)
        raise ValueError("Unsupported num_keyword value")

    prompt_config = yaml.full_load(open("prompt_config.yaml"))
    try:
        prompt_template = prompt_config[args.prompt_template]
    except KeyError:
        logger.error("Unsupported prompt_template value: %s", args.prompt_template)

    start = time.time()
    # Call API to fetch JSON data
    all_articles = fetch_all_records(env)
    end = time.time()

    logger.info(f"Retrieved {len(all_articles)} articles in {log_detailed_humane_time(end - start)}.")

    with open(args.prep_file, "wt") as writer:
        jsonl_writer = jsonlines.Writer(writer)
        for article in all_articles:
            jsonl_writer.write(prepare_annotation_record(article, args, dict(prompt_template)))

    if os.path.exists(args.predicted_file):
        os.remove(args.predicted_file)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
