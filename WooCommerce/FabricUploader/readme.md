# 🎨 WooCommerce Fabric Uploader

A command-line tool that analyzes a folder of fabric images, detects the dominant color in each image, uploads the image to your WordPress media library, and creates WooCommerce products combining the detected color name into the product title.

---

## 🔧 Setup

### 1. Install requirements

```bash
$ pip install -r requirements.txt
```

### 2. Configure `.env`

Create a `.env` file in the same directory using this template:

```env
WP_URL=https://yourwebsite.com
WP_USERNAME=your_wp_admin_username
WP_APP_PASSWORD=your_wp_application_password

WC_CONSUMER_KEY=ck_your_consumer_key
WC_CONSUMER_SECRET=cs_your_consumer_secret

IMAGE_FOLDER=./fabric_images
PRODUCT_PRICE=15.00
```

---

## 🚀 Run the Script

1. Place your fabric images (e.g. `.png`, `.jpg`, `.jpeg`, `.webp`) in the folder specified by `IMAGE_FOLDER` (default is `./fabric_images`).
2. Run the script:

```bash
$ python fabric_uploader.py
```

---

## 🗂️ Features & Output

*   **Dominant Color Analysis**: Uses K-Means clustering to identify the dominant color of the fabric, mapping it to the closest human-readable CSS3 color name.
*   **WordPress Media Upload**: Uploads each image directly to WordPress media library, auto-detecting file format (WebP/PNG/JPEG).
*   **WooCommerce Product Creation**: Creates products (e.g. "Premium Linen Fabric - SlateGray") with the associated uploaded image.
