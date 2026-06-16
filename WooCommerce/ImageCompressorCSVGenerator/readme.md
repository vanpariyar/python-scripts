# 🗜️ WooCommerce Image Compressor & CSV Generator

A command-line tool that automates preparing bulk images for WooCommerce. It compresses a folder of sequentially named images, converts them to standard WebP format, and generates a WooCommerce product CSV mapped to automatically link uploaded media.

---

## 🔧 Setup

### 1. Install requirements

```bash
$ pip install -r requirements.txt
```

### 2. Configure Settings

Open the script `process_products.py` and modify the configuration variables at the top of the file:

```python
INPUT_FOLDER = 'original_images'       # Folder containing product subfolders
OUTPUT_FOLDER = 'compressed_images'    # Flat folder for compressed output
CSV_FILENAME = 'woocommerce_import.csv' # Output CSV file name
MAX_FILE_SIZE_KB = 1500                 # Target maximum file size in KB
```

---

## 🚀 Run the Script

1. Place your uncompressed product images in subfolders inside the `original_images/` directory. Each subfolder represents a product.
2. Run the script:

```bash
$ python process_products.py
```

---

## 🗂️ Output & Import Instructions

Each run generates:
*   **`compressed_images/`**: Web-ready, optimized `.webp` images matching target limits.
*   **`woocommerce_import.csv`**: A CSV file containing WooCommerce product data mapping.

### WooCommerce Import Steps:
1. Upload all images in the `compressed_images/` directory to WordPress under **Media > Add New**.
2. Go to **WooCommerce > Products > Import** in your WordPress dashboard.
3. Upload `woocommerce_import.csv` and follow the mapping prompts (it will map the columns automatically).
4. Run the importer. WooCommerce will link the products to your newly uploaded images automatically.