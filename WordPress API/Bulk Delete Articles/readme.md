Create a file called .env in the same dir where you put this script:

```
FILE=<path/to/file/with/ids.jsonl>
WP_STATUS_FILE=/tmp/wp-deleted-records.jsonl
```

# Change this to PROD url if deleting from Prod
```
WP_ENDPOINT={SITE_URL}/wp-json/central-articles/v1/article
WP_USERNAME=<user>
WP_PASSWORD=<pwd>
BULK_SIZE=5
APP_LOG_LEVEL=DEBUG
TIMEOUT_SEC=600
```

```python
$ python3 -m pip install -r requirements.txt
$ ENV=.env python3 delete_wp_records.py
```