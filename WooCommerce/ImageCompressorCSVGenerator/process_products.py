import os
import csv
from PIL import Image

# ================= CONFIGURATION =================
INPUT_FOLDER = 'original_images'       # Base folder containing your product subfolders
OUTPUT_FOLDER = 'compressed_images'    # Flat folder where ALL compressed images will go
CSV_FILENAME = 'woocommerce_import.csv' # Name of the generated CSV file
MAX_FILE_SIZE_KB = 1500                 # Target maximum file size in KB
# =================================================

def compress_image(input_path, output_path, max_kb):
    """Compresses an image, preserving color profiles and using WebP for optimal quality."""
    img = Image.open(input_path)
    
    # 1. Extract the color profile to prevent colors from dulling or shifting
    icc_profile = img.info.get('icc_profile')
    
    # 2. Properly handle PNG transparency (RGBA) by adding a white background
    # Otherwise, transparent areas turn solid black when converted.
    if img.mode in ("RGBA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "RGBA":
            # Use the alpha channel as a mask
            background.paste(img, mask=img.split()[3])
        else:
            background.paste(img)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    quality = 85
    # Save as WebP - retains high quality and accurate colors at much lower file sizes
    img.save(output_path, format='WEBP', icc_profile=icc_profile, quality=quality, method=4)
    
    # 3. Smarter reduction: Resize the dimensions if it's still too big, 
    # but NEVER drop the visual quality below 65.
    while os.path.getsize(output_path) > max_kb * 1024 and quality >= 65:
        # If the file is significantly larger than the target, resize the dimensions first
        if os.path.getsize(output_path) > max_kb * 1500:
            width, height = img.size
            img = img.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
        else:
            # Only drop quality if we are close to the target size
            quality -= 5 
            
        img.save(output_path, format='WEBP', icc_profile=icc_profile, quality=quality, method=4)

def main():
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    csv_headers = [
        'Type', 'SKU', 'Name', 'Published', 'Is featured?', 
        'Visibility in catalog', 'Regular price', 'Categories', 'Images'
    ]
    csv_data = []
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')

    products = {}

    print("Scanning folders...")

    for root, dirs, files in os.walk(INPUT_FOLDER):
        if root == INPUT_FOLDER:
            continue # Skip files not in a subfolder
            
        product_name = os.path.basename(root)
        valid_files = [f for f in files if f.lower().endswith(valid_extensions)]
        
        if valid_files:
            valid_files.sort()
            
            if product_name not in products:
                products[product_name] = []

            for file in valid_files:
                input_path = os.path.join(root, file)
                
                base_name = os.path.splitext(file)[0]
                # CHANGED: Save as WebP instead of JPG
                final_img_name = f"{base_name}.webp" 
                output_path = os.path.join(OUTPUT_FOLDER, final_img_name)
                
                compress_image(input_path, output_path, MAX_FILE_SIZE_KB)
                print(f"Processed: Product '{product_name}' -> {final_img_name}")
                
                products[product_name].append(final_img_name)

    if not products:
        print(f"Error: Found 0 valid images inside subfolders of '{INPUT_FOLDER}'.")
        return

    print(f"\nFound {len(products)} unique products. Generating CSV...")

    for product_name, image_list in products.items():
        images_string = ", ".join(image_list)
        safe_sku = f"FABRIC-{product_name.upper().replace(' ', '-')}"

        csv_data.append({
            'Type': 'simple',
            'SKU': safe_sku,                           
            'Name': product_name,                       
            'Published': 1,
            'Is featured?': 0,
            'Visibility in catalog': 'visible',
            'Regular price': '1500',                    
            'Categories': 'Linen Fabrics',              
            'Images': images_string                     
        })

    with open(CSV_FILENAME, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"\nSuccess! \n- Saved to: {OUTPUT_FOLDER}/\n- CSV saved as: {CSV_FILENAME}")

if __name__ == "__main__":
    main()