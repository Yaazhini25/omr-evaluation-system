# omr_preprocessing.py
import cv2
import numpy as np


def preprocess_omr(file):
    """
    Input: uploaded OMR image file (from Streamlit)
    Output: thresholded, perspective-corrected image
    """
    # Read image
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image")
    
    # Store original for debugging
    original_height, original_width = img.shape[:2]
    
    # Resize maintaining aspect ratio but ensuring minimum size
    target_height = 1200
    aspect_ratio = original_width / original_height
    target_width = int(target_height * aspect_ratio)
    
    img = cv2.resize(img, (target_width, target_height))
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    
    # Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Use Otsu's thresholding for better binary conversion
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh  # Return only the processed image