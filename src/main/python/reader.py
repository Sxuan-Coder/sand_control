"""
Temporary reader module for sand particle image processing.
This module provides basic functionality for reading and processing images.
"""

import cv2
import numpy as np
import os

def read_image(file_path):
    """Read an image file and return it as a numpy array."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Image file not found: {file_path}")
    return cv2.imread(file_path)

def read_background_model(file_path):
    """Read a background model file and return it as a numpy array."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Background model file not found: {file_path}")
    return cv2.imread(file_path)

def read_binary_mask(file_path):
    """Read a binary mask file and return it as a numpy array."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Mask file not found: {file_path}")
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    return cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)[1]

def save_image(file_path, image):
    """Save an image to a file."""
    cv2.imwrite(file_path, image)

def read_folder_images(folder_path, extensions=('.jpg', '.jpeg', '.png', '.bmp')):
    """Read all images from a folder."""
    images = []
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
        
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(extensions):
            file_path = os.path.join(folder_path, file_name)
            try:
                img = cv2.imread(file_path)
                if img is not None:
                    images.append({
                        'image': img,
                        'path': file_path,
                        'name': file_name
                    })
            except Exception as e:
                print(f"Error reading image {file_name}: {str(e)}")
                
    return images
