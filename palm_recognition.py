import cv2
import numpy as np
import json
import logging
from typing import Optional, Tuple

class PalmRecognition:
    def __init__(self):
        """Initialize ORB feature detector for palm recognition"""
        self.orb = cv2.ORB_create(nfeatures=500)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocess palm image for feature extraction
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(blurred)
            
            # Resize to standard size for consistency
            resized = cv2.resize(enhanced, (400, 300))
            
            return resized
            
        except Exception as e:
            logging.error(f"Error preprocessing image {image_path}: {str(e)}")
            return None
    
    def extract_features(self, image_path: str) -> Optional[np.ndarray]:
        """
        Extract ORB features from palm image
        """
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return None
            
            # Detect keypoints and compute descriptors
            keypoints, descriptors = self.orb.detectAndCompute(processed_image, None)
            
            if descriptors is None or len(descriptors) == 0:
                logging.warning(f"No features detected in image: {image_path}")
                return None
            
            logging.info(f"Extracted {len(descriptors)} features from {image_path}")
            return descriptors
            
        except Exception as e:
            logging.error(f"Error extracting features from {image_path}: {str(e)}")
            return None
    
    def compare_features(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """
        Compare two sets of ORB features and return similarity score
        """
        try:
            if features1 is None or features2 is None:
                return 0.0
            
            if len(features1) == 0 or len(features2) == 0:
                return 0.0
            
            # Ensure features are in the correct format
            if features1.dtype != np.uint8:
                features1 = features1.astype(np.uint8)
            if features2.dtype != np.uint8:
                features2 = features2.astype(np.uint8)
            
            # Match features using BFMatcher
            matches = self.matcher.match(features1, features2)
            
            if len(matches) == 0:
                return 0.0
            
            # Sort matches by distance (lower is better)
            matches = sorted(matches, key=lambda x: x.distance)
            
            # Calculate similarity score based on good matches
            good_matches = [m for m in matches if m.distance < 50]  # Distance threshold
            
            # Calculate similarity as ratio of good matches to total possible matches
            max_possible_matches = min(len(features1), len(features2))
            similarity_score = len(good_matches) / max_possible_matches
            
            logging.info(f"Feature comparison: {len(good_matches)} good matches out of {len(matches)} total matches")
            logging.info(f"Similarity score: {similarity_score:.3f}")
            
            return similarity_score
            
        except Exception as e:
            logging.error(f"Error comparing features: {str(e)}")
            return 0.0
    
    def authenticate_palm(self, test_image_path: str, stored_features: np.ndarray, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Authenticate palm against stored features
        """
        try:
            # Extract features from test image
            test_features = self.extract_features(test_image_path)
            if test_features is None:
                return False, 0.0
            
            # Compare features
            similarity = self.compare_features(test_features, stored_features)
            
            # Determine if authentication is successful
            is_authenticated = similarity >= threshold
            
            logging.info(f"Palm authentication result: {is_authenticated} (similarity: {similarity:.3f}, threshold: {threshold})")
            
            return is_authenticated, similarity
            
        except Exception as e:
            logging.error(f"Error during palm authentication: {str(e)}")
            return False, 0.0
    
    def validate_palm_image(self, image_path: str) -> bool:
        """
        Validate if an image is suitable for palm recognition
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            # Check image dimensions
            height, width = image.shape[:2]
            if height < 100 or width < 100:
                logging.warning("Image too small for palm recognition")
                return False
            
            # Check if image has sufficient contrast
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if np.std(gray) < 20:  # Low standard deviation indicates low contrast
                logging.warning("Image has insufficient contrast")
                return False
            
            # Try to extract features to validate
            features = self.extract_features(image_path)
            if features is None or len(features) < 10:
                logging.warning("Insufficient features detected in image")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating palm image: {str(e)}")
            return False
