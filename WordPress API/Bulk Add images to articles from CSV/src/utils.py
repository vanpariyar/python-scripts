import os
from PIL import Image, ExifTags
from io import BytesIO
from iptcinfo3 import IPTCInfo


def extract_caption_credit(image_input):
    """
    Extracts caption and credit metadata from an image using IPTC and EXIF.

    Parameters:
        image_input (str or bytes): Path to image file or byte stream.

    Returns:
        tuple: (caption, credit) or (None, None)
    """
    try:
        if isinstance(image_input, bytes):
            input_stream = BytesIO(image_input)
        elif isinstance(image_input, str) and os.path.exists(image_input):
            input_stream = image_input
        else:
            return None, None

        caption, credit = None, None

        # --- IPTC ---
        try:
            iptc = IPTCInfo(input_stream, force=True)
            caption = iptc["credit"] if iptc["credit"] else None
            print( caption )
            caption = caption.decode('UTF-8')
            credit = caption
            if caption or credit:
                return caption, credit
        except Exception as e:
            print(f"[INFO] IPTC metadata could not be read: {e}")

    except Exception as e:
        print(f"[ERROR] Failed to extract metadata: {e}")
        return None, None


def compress_image(image: Image.Image, max_size_mb=2):
    """
    Compress image to ensure it is under max_size_mb.

    Parameters:
        image (PIL.Image): Pillow image object.
        max_size_mb (float): Max size in megabytes.

    Returns:
        bytes: Compressed image in JPEG format, or None if failed.
    """
    try:
        buffer = BytesIO()
        quality = 95
        while True:
            buffer.seek(0)
            buffer.truncate()
            image.save(buffer, format='JPEG', optimize=True, quality=quality)
            size_mb = buffer.tell() / (1024 * 1024)
            if size_mb <= max_size_mb or quality <= 10:
                break
            quality -= 5
        return buffer.getvalue()
    except Exception as e:
        print(f"❌ Failed to compress image: {e}")
        return None
