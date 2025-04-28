# 🖼️ WordPress Image Uploader CLI

A command-line tool that reads a CSV with WordPress post IDs and image URLs, uploads images to your WordPress media library, sets them as featured images, and adds image blocks to the post content.

---

## 🔧 Setup

### 1. Clone the repo & install requirements

```bash
$ python3 -m pip install -r requirements.txt
```

### 2. Configure `.env`

Create a `.env` file using this template:

```env
WP_SITE_URL=https://your-wordpress-site.com
WP_USERNAME=your_wp_username
WP_APP_PASSWORD=your_wp_application_password
```

---

## 📄 CSV Format

Your CSV should include the following columns: (articles.csv)

```csv
post_id,image_url
101,https://example.com/image1.jpg
102,https://example.com/image2.jpg
```

---

## 🚀 Run the Script

```bash
ENV=.env python3 wp_image_uploader.py --csv articles.csv --post_type post
```

- `--post_type` is optional. Default: `posts`
- Logs are saved daily in `logs/YYYY-MM-DD.log`

---

## 🗂️ Output

Each run generates a log file inside the `/logs/` directory, including upload status, media IDs, and error messages if any.