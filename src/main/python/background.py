import os
import cv2
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_backgrounds_single(background_path):
    """
    Read background images for single grading samples.
    Uses specific filenames G1.bmp for global and L1.bmp for local.
    
    Args:
        background_path: Path to the directory containing background images
        
    Returns:
        Dictionary of background models with keys in the format '{view_type}_{sample_index}'
    """
    try:
        logger.info(f"Reading single grade background models from {background_path}")
        background_models = {}
        
        # Load the global background from G1.bmp
        global_bg_path = os.path.join(background_path, "G1.bmp")
        if os.path.exists(global_bg_path):
            global_bg = cv2.imread(global_bg_path)
            
            # Add the same global background for all sample indices
            for sample_index in ["0.075", "0.15", "0.3", "0.6", "1.18", "2.36"]:
                key = f"global_s{sample_index}"
                background_models[key] = global_bg
                
                # Alternative key format
                key_alt = f"global_{sample_index}"
                background_models[key_alt] = global_bg
                
            logger.info(f"Loaded global background from {global_bg_path}")
        else:
            logger.error(f"Global background file not found: {global_bg_path}")
            
        # Load the local background from L1.bmp
        local_bg_path = os.path.join(background_path, "L1.bmp")
        if os.path.exists(local_bg_path):
            local_bg = cv2.imread(local_bg_path)
            
            # Add the same local background for all sample indices
            for sample_index in ["0.075", "0.15", "0.3", "0.6", "1.18", "2.36"]:
                key = f"local_s{sample_index}"
                background_models[key] = local_bg
                
                # Alternative key format
                key_alt = f"local_{sample_index}"
                background_models[key_alt] = local_bg
                
            logger.info(f"Loaded local background from {local_bg_path}")
        else:
            logger.error(f"Local background file not found: {local_bg_path}")
            
        return background_models
            
    except Exception as e:
        logger.error(f"Error reading background models: {str(e)}")
        raise

def read_backgrounds_mixture(background_path):
    """
    Read background images for mixture grading samples.
    Uses specific filenames G1.bmp for global and L1.bmp for local.
    
    Args:
        background_path: Path to the directory containing background images
        
    Returns:
        Dictionary of background models with keys in the format '{view_type}_s{sample_index}'
    """
    try:
        logger.info(f"Reading mixture grade background models from {background_path}")
        background_models = {}
        
        # Load the global background from G1.bmp
        global_bg_path = os.path.join(background_path, "G1.bmp")
        if os.path.exists(global_bg_path):
            global_bg = cv2.imread(global_bg_path)
            
            # Add global background for mixture samples (1-6)
            for i in range(1, 7):
                key = f"global_s{i}"
                background_models[key] = global_bg
                
            logger.info(f"Loaded global background from {global_bg_path}")
        else:
            logger.error(f"Global background file not found: {global_bg_path}")
            
        # Load the local background from L1.bmp
        local_bg_path = os.path.join(background_path, "L1.bmp")
        if os.path.exists(local_bg_path):
            local_bg = cv2.imread(local_bg_path)
            
            # Add local background for mixture samples (1-6)
            for i in range(1, 7):
                key = f"local_s{i}"
                background_models[key] = local_bg
                
            logger.info(f"Loaded local background from {local_bg_path}")
        else:
            logger.error(f"Local background file not found: {local_bg_path}")
            
        return background_models
            
    except Exception as e:
        logger.error(f"Error reading background models: {str(e)}")
        raise

def save_image(image, output_path, filename):
    """
    Save an image to the specified path with the given filename.
    
    Args:
        image: The image to save
        output_path: Directory to save the image to
        filename: Filename for the saved image
    
    Returns:
        Full path to the saved image
    """
    try:
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, filename)
        cv2.imwrite(output_file, image)
        return output_file
    except Exception as e:
        logger.error(f"Error saving image: {str(e)}")
        raise
