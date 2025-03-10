"""Domain entity for image perceptual hashes"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from pathlib import Path
import hashlib
import json

@dataclass
class ImageHash:
    """Core domain entity representing a perceptual hash of an image"""
    
    # Basic properties
    hash_array: np.ndarray  # The actual hash data
    hash_size: int  # Size of the hash (e.g., 8 for 8x8 hash)
    hash_type: str  # Type of hash (e.g., 'average', 'perceptual', 'difference')
    
    def __post_init__(self):
        """Validate hash array shape"""
        if self.hash_array.shape != (self.hash_size, self.hash_size):
            raise ValueError(
                f"Hash array shape {self.hash_array.shape} does not match "
                f"hash size {self.hash_size}x{self.hash_size}"
            )
    
    @property
    def hash_bits(self) -> int:
        """Get total number of bits in hash"""
        return self.hash_array.size
        
    def hamming_distance(self, other: 'ImageHash') -> float:
        """Calculate Hamming distance between two hashes"""
        if not isinstance(other, ImageHash):
            raise TypeError("Can only compare with another ImageHash")
            
        if self.hash_bits != other.hash_bits:
            raise ValueError(
                f"Hash sizes do not match: {self.hash_bits} != {other.hash_bits}"
            )
            
        return float(np.count_nonzero(self.hash_array != other.hash_array))
        
    def similarity(self, other: 'ImageHash') -> float:
        """Calculate similarity score (0-1) between two hashes"""
        try:
            distance = self.hamming_distance(other)
            return 1.0 - (distance / self.hash_bits)
        except (TypeError, ValueError):
            return 0.0
            
    def to_binary(self) -> List[bool]:
        """Convert hash to binary list"""
        return self.hash_array.flatten().tolist()
        
    def to_hex(self) -> str:
        """Convert hash to hexadecimal string"""
        bits = np.packbits(self.hash_array.flatten())
        return bits.tobytes().hex()
        
    def to_dict(self) -> dict:
        """Convert hash to dictionary"""
        return {
            'hash': self.to_hex(),
            'size': self.hash_size,
            'type': self.hash_type
        }
        
    @classmethod
    def from_hex(cls, hex_str: str, hash_size: int = 8, hash_type: str = 'average') -> 'ImageHash':
        """Create ImageHash from hexadecimal string"""
        try:
            # Convert hex to bits
            bits = np.unpackbits(np.frombuffer(bytes.fromhex(hex_str), dtype=np.uint8))
            
            # Validate bit length
            expected_bits = hash_size * hash_size
            if len(bits) < expected_bits:
                raise ValueError(f"Not enough bits for {hash_size}x{hash_size} hash")
                
            return cls(
                hash_array=bits[:expected_bits].reshape(hash_size, hash_size),
                hash_size=hash_size,
                hash_type=hash_type
            )
        except Exception as e:
            raise ValueError(f"Invalid hex hash: {e}")
        
    @classmethod
    def from_binary(cls, binary: List[bool], hash_size: int = 8, hash_type: str = 'average') -> 'ImageHash':
        """Create ImageHash from binary list"""
        try:
            binary_array = np.array(binary, dtype=bool)
            expected_bits = hash_size * hash_size
            
            if len(binary_array) != expected_bits:
                raise ValueError(f"Binary list length must be {expected_bits}")
                
            return cls(
                hash_array=binary_array.reshape(hash_size, hash_size),
                hash_size=hash_size,
                hash_type=hash_type
            )
        except Exception as e:
            raise ValueError(f"Invalid binary hash: {e}")
            
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageHash':
        """Create ImageHash from dictionary"""
        try:
            return cls.from_hex(
                data['hash'],
                hash_size=data['size'],
                hash_type=data['type']
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid hash dictionary: {e}")

    @staticmethod
    def create_file_hash(file_path: str) -> str:
        """Create a hash from a file path that can be used for caching"""
        try:
            path = Path(file_path)
            if not path.exists():
                return ""
                
            # Get file stats for hash input
            stats = path.stat()
            
            # Create hash input combining path, size and modification time
            hash_input = json.dumps({
                'path': str(path.absolute()),
                'size': stats.st_size,
                'mtime': stats.st_mtime
            }, sort_keys=True).encode()
            
            # Create hash
            return hashlib.sha256(hash_input).hexdigest()
            
        except Exception as e:
            return "" 