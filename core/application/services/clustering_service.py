"""Service for image clustering and similarity analysis"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from PIL import Image

from ...domain.entities.image import Image as ImageEntity
from ...domain.entities.image_hash import ImageHash
from .image_hash_service import ImageHashService

logger = logging.getLogger(__name__)

class ClusterManager:
    """Manages image clustering and similarity analysis"""
    
    def __init__(self, 
                 hash_service: ImageHashService,
                 eps: float = 0.3,
                 min_samples: int = 5):
        self.hash_service = hash_service
        self.eps = eps
        self.min_samples = min_samples
        self.logger = logging.getLogger(__name__)
        
    def cluster_images(self, images: List[ImageEntity]) -> List['ImageCluster']:
        """Cluster images based on perceptual hashes"""
        try:
            if not images:
                return []
                
            # Compute hashes for all images
            image_hashes = []
            valid_images = []
            
            for image in images:
                if hash_data := self.hash_service.compute_perceptual_hash(image):
                    image_hashes.append(hash_data.to_binary())
                    valid_images.append(image)
                    
            if not valid_images:
                return []
                
            # Convert to numpy array and normalize
            X = np.array(image_hashes)
            X_scaled = StandardScaler().fit_transform(X)
            
            # Perform clustering
            db = DBSCAN(eps=self.eps, min_samples=self.min_samples)
            cluster_labels = db.fit_predict(X_scaled)
            
            # Group images by cluster
            clusters = {}
            for idx, label in enumerate(cluster_labels):
                if label >= 0:  # Ignore noise points (-1)
                    if label not in clusters:
                        clusters[label] = ImageCluster(label)
                    clusters[label].add_image(valid_images[idx])
                    
            return sorted(clusters.values(), key=lambda x: len(x.images), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error clustering images: {e}")
            return []
            
    def find_similar_images(self, 
                          target: ImageEntity,
                          candidates: List[ImageEntity],
                          threshold: float = 0.85) -> List[ImageEntity]:
        """Find images similar to the target image"""
        try:
            similar = self.hash_service.find_similar_images(
                target=target,
                candidates=candidates,
                threshold=threshold,
                hash_type='perceptual'  # Use perceptual hash for better accuracy
            )
            return [img for img, _ in similar]
            
        except Exception as e:
            self.logger.error(f"Error finding similar images: {e}")
            return []

class ImageCluster:
    """Represents a cluster of similar images"""
    
    def __init__(self, cluster_id: int):
        self.cluster_id = cluster_id
        self.images: List[ImageEntity] = []
        
    def add_image(self, image: ImageEntity):
        """Add an image to the cluster"""
        self.images.append(image)
        
    @property
    def size(self) -> int:
        """Get number of images in cluster"""
        return len(self.images)
        
    @property
    def representative_image(self) -> Optional[ImageEntity]:
        """Get a representative image for the cluster"""
        return self.images[0] if self.images else None

    def analyze_duplicates(self, 
                         images: List[ImageEntity],
                         threshold: float = 0.95) -> List[List[ImageEntity]]:
        """Find duplicate or near-duplicate images"""
        try:
            # Calculate hashes for all images
            image_hashes = {}
            
            for image in images:
                if hash_data := self.hash_service.compute_average_hash(image):
                    image_hashes[image] = hash_data
                    
            # Find groups of similar images
            duplicate_groups = []
            processed = set()
            
            for image1, hash1 in image_hashes.items():
                if image1 in processed:
                    continue
                    
                group = [image1]
                
                for image2, hash2 in image_hashes.items():
                    if image1 != image2 and image2 not in processed:
                        similarity = hash1.similarity(hash2)
                        if similarity >= threshold:
                            group.append(image2)
                            
                if len(group) > 1:
                    duplicate_groups.append(group)
                    processed.update(group)
                    
            return duplicate_groups
            
        except Exception as e:
            self.logger.error(f"Error analyzing duplicates: {e}")
            return [] 