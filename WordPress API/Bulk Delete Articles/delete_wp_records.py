import copy
import httpx
import json
import gzip
import os
import sys
import nanoid
import time
import urllib.parse
from multiprocessing import Pool
from loguru import logger
from dotenv import load_dotenv


class EnvVars(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


def delete_post(post_id, env: EnvVars):
    try:
        with httpx.Client() as client:
            post_url = os.path.join(env.WP_API_ENDPOINT, str(post_id))

            # We _really_ want to delete the article!
            post_url = urllib.parse.urlparse(post_url)._replace(query='force=true').geturl()

            response = client.delete(
                url=post_url,
                auth=env.AUTH,
                headers={
                    'Content-Type': 'application/json',
                },
                timeout=env.TIMEOUT_SEC
            )

        status = {
            'id': post_id,
            'status_code': response.status_code,
            'post_url': post_url,
            'response': response.text
        }

        if response.status_code == 200:
            status['message'] = f"Post {post_id} deleted successfully."
        else:
            status['message'] = f"Failed to delete post {post_id}."
    except httpx.Timeout:
        status = {
            'id': post_id,
            'post_url': post_url,
            'status_code': None,
            'response': None,
            'message': f"Timeout while trying to delete post {post_id}."
        }
    except Exception as exc:
        status = {
            'id': post_id,
            'post_url': post_url,
            'status_code': None,
            'response': None,
            'message': f"Exception while trying to delete post {post_id}."
        }
        logger.exception(exc)

    return status


def log_detailed_humane_time(seconds):
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes and {seconds % 60} seconds"
    else:
        return f"{seconds // 3600} hours, {(seconds % 3600) // 60} minutes, and {(seconds % 3600) % 60} seconds"


def log_random_record(current_batch: list):
    # Log a random record from the current batch list
    random_record_index = int(nanoid.generate(alphabet='123456789', size=12)) % len(current_batch)
    random_record = copy.deepcopy(current_batch[random_record_index])

    response = json.loads(random_record['response']) if random_record['response'] else None
    if random_record['status_code'] and random_record['status_code'] == 200:
        status_record = {
            'deleted': response.get('deleted', False),
            'id': response.get('previous', {}).get('id', None),
            'title': response.get('previous', {}).get('title', {}).get('raw', None),
            'slug': response.get('previous', {}).get('slug', None),
        }

        random_record['response'] = json.dumps(status_record)
    logger.info(f"Random record from current batch: {random_record}")


def get_env_vars():
    env = EnvVars(**os.environ)

    env.FILE = os.getenv('FILE')
    env.WP_API_ENDPOINT = os.getenv('WP_ENDPOINT',
                                    'https://www.example.com/wp-json/wp/v2/posts'
                                    '/wp-json/wp/v2/posts')
    env.BATCH_SIZE = int(os.getenv('BATCH_SIZE', 8))
    env.AUTH_USERNAME = os.getenv('WP_USERNAME', None)
    env.AUTH_PASSWORD = os.getenv('WP_PASSWORD', None)
    env.STATUS_FILE = os.getenv('WP_STATUS_FILE', f'/tmp/wp_deletion_status_{nanoid.generate(size=8)}.jsonl')
    env.AUTH = (env.AUTH_USERNAME, env.AUTH_PASSWORD)
    env.TIMEOUT_SEC = float(os.getenv('TIMEOUT_SEC', 10))
    env.BULK_SIZE = int(os.getenv('BULK_SIZE', 100))

    return env


def log_env_vars(envs: EnvVars):
    # Log all the app-specific env vars
    logger.info(f"FILE: {envs.FILE}")
    logger.info(f"WP_API_ENDPOINT: {envs.WP_API_ENDPOINT}")
    logger.info(f"BATCH_SIZE: {envs.BATCH_SIZE}")
    logger.info(f"AUTH_USERNAME: {envs.AUTH_USERNAME}")
    logger.info(f"AUTH_PASSWORD: {'*' * len(envs.AUTH_PASSWORD)}")
    logger.info(f"STATUS_FILE: {envs.STATUS_FILE}")
    logger.info(f"TIMEOUT_SEC: {envs.TIMEOUT_SEC}")


def main():
    load_dotenv(os.getenv("ENV", None))

    env = get_env_vars()
    log_env_vars(env)

    # Load the jsonl file
    logger.info(f"Reading file {os.path.abspath(env.FILE)}...")
    post_ids = get_non_empty_ids(env)
    args_for_delete_post = [(post_id, env) for post_id in post_ids]
    logger.info(f"Total post ids to process: {len(post_ids)}")

    start = time.time()
    results = delete_records(args_for_delete_post, env)
    end = time.time()
    logger.info(f"Submitted {len(post_ids)} posts in {log_detailed_humane_time(end - start)}.")

    # Write results to the status file
    logger.info(f"Writing status file to {os.path.abspath(env.STATUS_FILE)}...")
    write_status_file(env, results)
    logger.info(f"Status file written to {os.path.abspath(env.STATUS_FILE)}")


def delete_records(args_for_delete_post: list, env: EnvVars) -> list:
    results = []

    with Pool(env.BATCH_SIZE) as pool:
        for i in range(0, len(args_for_delete_post), env.BULK_SIZE):
            current_batch = []
            batch = args_for_delete_post[i:i + env.BULK_SIZE]
            current_batch.extend(pool.starmap(delete_post, batch))
            results.extend(current_batch)
            logger.info(f"Submitted {len(batch)} records for deletion, total submitted: {i + len(batch)}")

            log_random_record(current_batch)

    return results


def write_status_file(env: EnvVars, results: list):
    if env.STATUS_FILE.endswith(".gz"):
        with gzip.open(env.STATUS_FILE, 'wt') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
    else:
        with open(env.STATUS_FILE, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')


def get_non_empty_ids(env: EnvVars) -> list:
    if env.FILE.endswith(".gz"):
        open_file = gzip.open
    else:
        open_file = open
    with open_file(env.FILE, 'rt') as f:
        post_ids = []
        for line in f:
            record = json.loads(line)
            if record.get('id', None):
                post_ids.append(record['id'])

    return post_ids


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception(e)
        sys.exit(1)
