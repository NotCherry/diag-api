import base64
from PIL import Image
import io

def resize_base64_image_preserve_aspect_ratio(base64_string, new_width=None, new_height=None):
    # Step 1: Decode the Base64 string to an image
    img_data = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_data))

    # Step 2: Calculate the new dimensions while preserving aspect ratio
    original_width, original_height = img.size
    
    if new_width and not new_height:
        # Calculate new height based on aspect ratio
        ratio = new_width / float(original_width)
        new_height = int((float(original_height) * float(ratio)))
    
    elif new_height and not new_width:
        # Calculate new width based on aspect ratio
        ratio = new_height / float(original_height)
        new_width = int((float(original_width) * float(ratio)))

    # Step 3: Resize the image
    img = img.resize((new_width, new_height))

    # Step 4: Convert the resized image back to Base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    resized_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return resized_base64