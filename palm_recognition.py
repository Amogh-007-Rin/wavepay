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
        Preprocess palm image for feature extraction with improved handling
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logging.error(f"Failed to load image: {image_path}")
                return None
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter to reduce noise while preserving edges
            filtered = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Enhance contrast using adaptive histogram equalization
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(filtered)
            
            # Apply slight Gaussian blur for smoothing
            smoothed = cv2.GaussianBlur(enhanced, (3, 3), 0)
            
            # Resize to larger standard size for better feature detection
            resized = cv2.resize(smoothed, (640, 480))
            
            # Apply sharpening kernel to enhance palm lines
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(resized, -1, kernel)
            
            # Blend original and sharpened image
            final = cv2.addWeighted(resized, 0.7, sharpened, 0.3, 0)
            
            return final
            
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
            
            # Use more lenient distance threshold for better matching
            good_matches = [m for m in matches if m.distance < 60]  # Increased from 50 to 60
            
            # Use top 20% of matches for more reliable scoring
            top_matches = matches[:max(10, len(matches) // 5)]
            excellent_matches = [m for m in top_matches if m.distance < 45]
            
            # Calculate multiple similarity metrics
            # 1. Ratio of good matches to minimum feature count
            min_features = min(len(features1), len(features2))
            basic_score = len(good_matches) / min_features
            
            # 2. Quality-weighted score based on match distances
            if len(top_matches) > 0:
                avg_distance = sum(m.distance for m in top_matches) / len(top_matches)
                distance_score = max(0, (80 - avg_distance) / 80)  # Normalize distance to 0-1
            else:
                distance_score = 0
            
            # 3. Excellent matches bonus
            excellent_ratio = len(excellent_matches) / min(20, min_features)
            
            # Combine scores with weights
            final_score = (basic_score * 0.4) + (distance_score * 0.4) + (excellent_ratio * 0.2)
            
            # Cap the score at 1.0
            final_score = min(1.0, final_score)
            
            logging.info(f"Feature comparison: {len(good_matches)} good matches, {len(excellent_matches)} excellent matches out of {len(matches)} total")
            logging.info(f"Scores - Basic: {basic_score:.3f}, Distance: {distance_score:.3f}, Excellent: {excellent_ratio:.3f}")
            logging.info(f"Final similarity score: {final_score:.3f}")
            
            return final_score
            
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
