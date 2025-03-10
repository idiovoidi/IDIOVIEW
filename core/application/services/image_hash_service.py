"""Service for generating and comparing image hashes"""

import logging
from typing import Optional, List, Dict, Tuple
import numpy as np
from scipy.fftpack import dct

from core.domain.entities.image import Image as ImageEntity
from core.domain.entities.image_hash import ImageHash
from core.infrastructure.utils.image_utils import open_image_efficient

logger = logging.getLogger(__name__)

class ImageHashService:
    """Service for generating and comparing perceptual image hashes"""
    
    def __init__(self, hash_size: int = 8):
        self.hash_size = hash_size
        self.logger = logging.getLogger(__name__)
        
    def compute_average_hash(self, image: ImageEntity) -> Optional[ImageHash]:
        """Compute average hash (aHash) for an image"""
        try:
            # Open image efficiently and convert to grayscale
            if img := open_image_efficient(image.path, (self.hash_size, self.hash_size)):
                with img:
                    # Convert to grayscale and resize
                    img = img.convert('L')
                    
                    # Get pixel data
                    pixels = np.array(img)
                    
                    # Compute average and generate hash
                    avg = pixels.mean()
                    hash_array = pixels > avg
                    
                    return ImageHash(
                        hash_array=hash_array,
                        hash_size=self.hash_size,
                        hash_type='average'
                    )
                    
        except Exception as e:
            self.logger.error(f"Error computing average hash for {image.path}: {e}")
            return None
            
    def compute_perceptual_hash(self, image: ImageEntity) -> Optional[ImageHash]:
        """Compute perceptual hash (pHash) for an image"""
        try:
            # Open image efficiently and convert to grayscale
            if img := open_image_efficient(image.path, (32, 32)):
                with img:
                    # Convert to grayscale
                    img = img.convert('L')
                    
                    # Get pixel data
                    pixels = np.array(img, dtype=float)
                    
                    # Compute DCT
                    dct_result = dct(dct(pixels.T, norm='ortho').T, norm='ortho')
                    
                    # Keep top-left 8x8 of DCT
                    dct_low = dct_result[:self.hash_size, :self.hash_size]
                    
                    # Compute median and generate hash
                    med = np.median(dct_low)
                    hash_array = dct_low > med
                    
                    return ImageHash(
                        hash_array=hash_array,
                        hash_size=self.hash_size,
                        hash_type='perceptual'
                    )
                    
        except Exception as e:
            self.logger.error(f"Error computing perceptual hash for {image.path}: {e}")
            return None
            
    def compute_difference_hash(self, image: ImageEntity) -> Optional[ImageHash]:
        """Compute difference hash (dHash) for an image"""
        try:
            # Open image efficiently and convert to grayscale
            if img := open_image_efficient(image.path, (self.hash_size + 1, self.hash_size)):
                with img:
                    # Convert to grayscale
                    img = img.convert('L')
                    
                    # Get pixel data
                    pixels = np.array(img)
                    
                    # Compute differences
                    diff = pixels[:, 1:] > pixels[:, :-1]
                    
                    return ImageHash(
                        hash_array=diff,
                        hash_size=self.hash_size,
                        hash_type='difference'
                    )
                    
        except Exception as e:
            self.logger.error(f"Error computing difference hash for {image.path}: {e}")
            return None
            
    def find_similar_images(self, 
                          target: ImageEntity,
                          candidates: List[ImageEntity],
                          threshold: float = 0.85,
                          hash_type: str = 'average') -> List[Tuple[ImageEntity, float]]:
        """Find similar images based on hash comparison"""
        try:
            # Get hash function based on type
            hash_func = {
                'average': self.compute_average_hash,
                'perceptual': self.compute_perceptual_hash,
                'difference': self.compute_difference_hash
            }.get(hash_type)
            
            if not hash_func:
                raise ValueError(f"Invalid hash type: {hash_type}")
                
            # Compute target hash
            target_hash = hash_func(target)
            if not target_hash:
                return []
                
            # Compare with candidates
            similar_images = []
            for candidate in candidates:
                if candidate.path == target.path:
                    continue
                    
                candidate_hash = hash_func(candidate)
                if candidate_hash:
                    similarity = target_hash.similarity(candidate_hash)
                    if similarity >= threshold:
                        similar_images.append((candidate, similarity))
                        
            return sorted(similar_images, key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error finding similar images: {e}")
            return [] 