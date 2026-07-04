import os
import requests
from requests.auth import HTTPBasicAuth
from woocommerce import API
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import webcolors

# Helper to load variables from a .env file if it exists
def load_env_file(filepath=".env"):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    os.environ[key] = val

# Load configuration from .env file (checking current directory and parent)
load_env_file(".env")
load_env_file("../.env")
load_env_file("../../.env")

# ==========================================
# CONFIGURATION - UPDATE THESE VALUES
# ==========================================
WP_URL = os.environ.get("WP_URL", "https://yourwebsite.com")
WP_USERNAME = os.environ.get("WP_USERNAME", "your_wp_admin_username")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD", "your_wp_application_password") # Not your login password!

WC_CONSUMER_KEY = os.environ.get("WC_CONSUMER_KEY", "ck_your_consumer_key")
WC_CONSUMER_SECRET = os.environ.get("WC_CONSUMER_SECRET", "cs_your_consumer_secret")

IMAGE_FOLDER = os.environ.get("IMAGE_FOLDER", "./fabric_images") # Path to the folder containing your product subfolders

# WooCommerce Product Defaults
PRODUCT_PRICE = os.environ.get("PRODUCT_PRICE", "15.00")
CATEGORY_IDS = [] # List of category IDs, e.g., [12]. Keep empty if you do not want to assign a category or don't know the IDs.
# ==========================================

# Initialize WooCommerce API Client
wcapi = API(
    url=WP_URL,
    consumer_key=WC_CONSUMER_KEY,
    consumer_secret=WC_CONSUMER_SECRET,
    version="wc/v3",
    timeout=60
)

def get_closest_color_name(rgb_tuple):
    """Converts an RGB tuple to the closest human-readable CSS3 color name."""
    min_colours = {}
    
    # Handle compatibility across webcolors version changes (specifically version 24.6.0+)
    try:
        hex_to_names = webcolors.CSS3_HEX_TO_NAMES
        for hex_str, name in hex_to_names.items():
            r_c, g_c, b_c = webcolors.hex_to_rgb(hex_str)
            rd = (r_c - rgb_tuple[0]) ** 2
            gd = (g_c - rgb_tuple[1]) ** 2
            bd = (b_c - rgb_tuple[2]) ** 2
            min_colours[(rd + gd + bd)] = name
    except AttributeError:
        # Fallback for newer versions of webcolors
        for name in webcolors.names('css3'):
            hex_str = webcolors.name_to_hex(name)
            r_c, g_c, b_c = webcolors.hex_to_rgb(hex_str)
            rd = (r_c - rgb_tuple[0]) ** 2
            gd = (g_c - rgb_tuple[1]) ** 2
            bd = (b_c - rgb_tuple[2]) ** 2
            min_colours[(rd + gd + bd)] = name
            
    if not min_colours:
        return "Unknown"
        
    return min_colours[min(min_colours.keys())]

def get_dominant_color(image_path, k=4):
    """Finds the dominant color in an image using K-Means clustering."""
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize((50, 50)) # Resize to speed up processing
    
    # Convert image data to numpy array
    img_array = np.array(img)
    pixels = img_array.reshape((-1, 3))
    
    # Use KMeans to find dominant colors
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(pixels)
    
    # Find the most frequent cluster center
    counts = np.bincount(kmeans.labels_)
    dominant_rgb = kmeans.cluster_centers_[np.argmax(counts)]
    
    return get_closest_color_name(tuple(map(int, dominant_rgb)))

def upload_image_to_wp(image_path):
    """Uploads an image to the WordPress Media Library and returns the Attachment ID."""
    media_url = f"{WP_URL}/wp-json/wp/v2/media"
    filename = os.path.basename(image_path)
    
    # Detect Content-Type based on file extension
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.png':
        content_type = 'image/png'
    elif ext == '.webp':
        content_type = 'image/webp'
    else:
        content_type = 'image/jpeg'
        
    headers = {
        'Content-Disposition': f'attachment; filename="{filename}"',
        'Content-Type': content_type
    }
    
    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                media_url,
                headers=headers,
                data=img_file,
                auth=HTTPBasicAuth(WP_USERNAME, WP_APP_PASSWORD)
            )
            
        if response.status_code == 201:
            print(f"✅ Successfully uploaded {filename}")
            return response.json().get('id')
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception occurred during image upload: {e}")
        return None

def create_woocommerce_product(product_name, color_name, image_ids):
    """Creates a simple WooCommerce product with the generated data."""
    # Ensure color name is appended if it's not already in the product name
    if color_name.lower() not in product_name.lower():
        title = f"{product_name} ({color_name.title()})"
    else:
        title = product_name
        
    description = f"Experience the comfort and breathability of our high-quality fabric. This beautiful shade of {color_name} is perfect for apparel, home decor, and crafting projects."
    sku = f"FABRIC-{product_name.upper().replace(' ', '-')}"
    
    # Prepare image payload. WooCommerce REST API treats the first image in the array 
    # as the featured (main) image, and any subsequent images as product gallery images.
    images_payload = [{"id": img_id} for img_id in image_ids]
    
    data = {
        "name": title,
        "type": "simple",
        "sku": sku,
        "regular_price": PRODUCT_PRICE,
        "description": description,
        "short_description": f"High quality fabric in {color_name}.",
        "images": images_payload
    }
    
    if CATEGORY_IDS:
        data["categories"] = [{"id": cat_id} for cat_id in CATEGORY_IDS]
        
    try:
        response = wcapi.post("products", data)
        
        if response.status_code == 201:
            print(f"🎉 Product created successfully: {title}")
        else:
            print(f"❌ Failed to create product: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Exception occurred during product creation: {e}")

def main():
    if not os.path.exists(IMAGE_FOLDER):
        print(f"❌ Image folder '{IMAGE_FOLDER}' does not exist. Please create it and add your product subfolders.")
        return
        
    # Scan subfolders inside IMAGE_FOLDER (each subfolder is a product)
    subfolders = [os.path.join(IMAGE_FOLDER, d) for d in os.listdir(IMAGE_FOLDER) if os.path.isdir(os.path.join(IMAGE_FOLDER, d))]
    
    if not subfolders:
        print(f"ℹ️ No subfolders found in '{IMAGE_FOLDER}'. Checking for files in root...")
        # Fallback to checking the root directory for direct files
        files_to_process = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        if files_to_process:
            print("💡 Found images directly in root folder. Processing as individual products...")
            for filename in files_to_process:
                image_path = os.path.join(IMAGE_FOLDER, filename)
                name_without_ext = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").title()
                
                try:
                    color_name = get_dominant_color(image_path)
                    print(f"\nProcessing file: {filename}...")
                    print(f"🎨 Detected Color: {color_name}")
                except Exception as e:
                    print(f"❌ Failed to detect color for {filename}: {e}")
                    continue
                
                image_id = upload_image_to_wp(image_path)
                if image_id:
                    create_woocommerce_product(name_without_ext, color_name, [image_id])
        return

    for folder_path in subfolders:
        folder_name = os.path.basename(folder_path)
        product_name = folder_name.replace("_", " ").replace("-", " ").title()
        
        print(f"\n📁 Processing Product Folder: '{folder_name}'...")
        
        # Get all valid images in the subfolder
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        images = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
        
        if not images:
            print(f"⚠️ No valid images found in folder '{folder_name}'. Skipping.")
            continue
            
        # Sort images to ensure consistent main image ordering (e.g. image_1, image_2, etc.)
        images.sort()
        
        main_image_path = images[0]
        print(f"🖼️ Main (featured) image: {os.path.basename(main_image_path)}")
        if len(images) > 1:
            print(f"🖼️ Gallery images: {', '.join([os.path.basename(img) for img in images[1:]])}")
            
        # 1. Detect Color using the main (first) image
        try:
            color_name = get_dominant_color(main_image_path)
            print(f"🎨 Detected Color (from main image): {color_name}")
        except Exception as e:
            print(f"❌ Failed to detect color for {os.path.basename(main_image_path)}: {e}")
            continue
            
        # 2. Upload all images to WordPress and get attachment IDs
        uploaded_image_ids = []
        for img_path in images:
            image_id = upload_image_to_wp(img_path)
            if image_id:
                uploaded_image_ids.append(image_id)
                
        # 3. Create Product in WooCommerce
        if uploaded_image_ids:
            create_woocommerce_product(product_name, color_name, uploaded_image_ids)
        else:
            print(f"❌ Failed to upload any images for product '{product_name}'. Product creation skipped.")

if __name__ == "__main__":
    main()
