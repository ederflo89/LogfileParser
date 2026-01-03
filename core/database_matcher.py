"""
Database Matcher - 3-Stage Error Matching Engine

Provides efficient matching of log errors against a database of known errors
with causes and solutions. Uses a three-stage matching strategy:
1. Exact Match - Direct string comparison
2. Normalized Match - Count-prefix removal and path generalization
3. Fuzzy Match - Similarity-based matching (85%+ threshold)

Performance target: <50ms for typical queries
"""

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Optional, Dict, Any, Tuple
from core.avstumpfl_parser import AVStumpflLogParser
from core.log_parser import generalize_file_paths


class DatabaseMatcher:
    """
    3-Stage Error Matching Engine
    
    Matches log errors against a database using:
    1. Exact Match - Full text comparison
    2. Normalized Match - Normalized text (count-prefix removed, paths generalized)
    3. Fuzzy Match - SequenceMatcher with 85%+ threshold
    
    Uses LRU caching for performance optimization.
    """
    
    # Fuzzy matching threshold (85% similarity)
    FUZZY_THRESHOLD = 0.85
    
    # Cache size for normalized text and fuzzy matches
    CACHE_SIZE = 256
    
    def __init__(self, database_client=None):
        """
        Initialize the DatabaseMatcher
        
        Args:
            database_client: Optional database client for fetching entries.
                           If None, matcher can still be used for normalization.
        """
        self.database_client = database_client
        self._normalization_cache = {}
        
    @staticmethod
    @lru_cache(maxsize=256)
    def normalize_error_text(text: str) -> str:
        """
        Normalize error text for matching using the same normalization
        as the log parser (count-prefix removal + path generalization).
        
        This ensures database entries and log texts use identical normalization.
        
        Args:
            text: Error text to normalize
            
        Returns:
            Normalized text with placeholders for variable parts
            
        Examples:
            >>> DatabaseMatcher.normalize_error_text("17x Connection failed")
            "Connection failed"
            
            >>> DatabaseMatcher.normalize_error_text("File D:\\\\test\\\\file.mov not found")
            "File <DRIVE_PATH> not found"
        """
        # Stage 1: Apply count-prefix and pattern normalization from AVStumpflLogParser
        normalized = AVStumpflLogParser._normalize_for_deduplication(text)
        
        # Stage 2: Apply path generalization
        normalized = generalize_file_paths(normalized)
        
        return normalized
    
    def match_exact(self, error_text: str, database_entry_text: str) -> bool:
        """
        Perform exact text matching
        
        Args:
            error_text: Log error text
            database_entry_text: Database entry text
            
        Returns:
            True if texts match exactly (case-insensitive)
        """
        return error_text.strip().lower() == database_entry_text.strip().lower()
    
    def match_normalized(self, error_text: str, database_entry_text: str) -> bool:
        """
        Perform normalized text matching (count-prefix + path generalization)
        
        Both texts are normalized using the same rules before comparison.
        
        Args:
            error_text: Log error text
            database_entry_text: Database entry text
            
        Returns:
            True if normalized texts match
            
        Examples:
            >>> matcher = DatabaseMatcher()
            >>> matcher.match_normalized(
            ...     "17x Connection failed",
            ...     "Connection failed"
            ... )
            True
        """
        norm_error = self.normalize_error_text(error_text)
        norm_db = self.normalize_error_text(database_entry_text)
        
        return norm_error.lower() == norm_db.lower()
    
    @lru_cache(maxsize=256)
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts (cached)
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def match_fuzzy(self, error_text: str, database_entry_text: str, 
                    threshold: Optional[float] = None) -> Tuple[bool, float]:
        """
        Perform fuzzy text matching using SequenceMatcher
        
        Args:
            error_text: Log error text
            database_entry_text: Database entry text
            threshold: Similarity threshold (default: 0.85)
            
        Returns:
            Tuple of (match_found, similarity_ratio)
            
        Examples:
            >>> matcher = DatabaseMatcher()
            >>> match, score = matcher.match_fuzzy(
            ...     "Connection forcibly closed",
            ...     "Connection forcefully closed"
            ... )
            >>> match
            True
            >>> score > 0.85
            True
        """
        if threshold is None:
            threshold = self.FUZZY_THRESHOLD
        
        # Normalize both texts first for better matching
        norm_error = self.normalize_error_text(error_text)
        norm_db = self.normalize_error_text(database_entry_text)
        
        # Calculate similarity
        similarity = self._calculate_similarity(norm_error, norm_db)
        
        return (similarity >= threshold, similarity)
    
    def match_error(self, error_text: str, error_type: str = "", 
                    database_entries: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """
        Orchestrate all 3 matching stages to find the best match
        
        Matching stages (in order):
        1. Exact Match - Direct comparison
        2. Normalized Match - Count-prefix + path normalization
        3. Fuzzy Match - Similarity-based (85%+ threshold)
        
        Args:
            error_text: Log error text to match
            error_type: Optional error type/source for additional context
            database_entries: Optional list of database entries to match against.
                            If None and database_client is available, will query database.
                            Each entry should be a dict with keys: 'error_text', 'cause', 'solution'
            
        Returns:
            Dict with matched entry details if found, None otherwise.
            Format: {
                'match_type': 'exact'|'normalized'|'fuzzy',
                'similarity': float (0.0-1.0, always 1.0 for exact/normalized),
                'error_text': str,
                'cause': str,
                'solution': str,
                'original_entry': dict (original database entry)
            }
            
        Examples:
            >>> matcher = DatabaseMatcher()
            >>> entries = [
            ...     {'error_text': 'Connection failed', 'cause': 'Network issue', 'solution': 'Check network'}
            ... ]
            >>> result = matcher.match_error("17x Connection failed", database_entries=entries)
            >>> result['match_type']
            'normalized'
        """
        if not error_text or not error_text.strip():
            return None
        
        # If no entries provided, try to query from database
        if database_entries is None:
            if self.database_client is None:
                return None
            
            # Query database for potential matches
            # Try to get entries by normalized text
            normalized = self.normalize_error_text(error_text)
            database_entries = self.database_client.find_entries_by_normalized_text(normalized)
            
            # If no matches found, try broader search
            if not database_entries:
                database_entries = self.database_client.get_all_entries()
        
        if not database_entries:
            return None
        
        # Stage 1: Exact Match
        for entry in database_entries:
            db_text = entry.get('error_text', '')
            if self.match_exact(error_text, db_text):
                return {
                    'match_type': 'exact',
                    'similarity': 1.0,
                    'error_text': db_text,
                    'cause': entry.get('cause', ''),
                    'solution': entry.get('solution', ''),
                    'original_entry': entry
                }
        
        # Stage 2: Normalized Match
        for entry in database_entries:
            db_text = entry.get('error_text', '')
            if self.match_normalized(error_text, db_text):
                return {
                    'match_type': 'normalized',
                    'similarity': 1.0,
                    'error_text': db_text,
                    'cause': entry.get('cause', ''),
                    'solution': entry.get('solution', ''),
                    'original_entry': entry
                }
        
        # Stage 3: Fuzzy Match
        best_match = None
        best_similarity = 0.0
        
        for entry in database_entries:
            db_text = entry.get('error_text', '')
            is_match, similarity = self.match_fuzzy(error_text, db_text)
            
            if is_match and similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    'match_type': 'fuzzy',
                    'similarity': similarity,
                    'error_text': db_text,
                    'cause': entry.get('cause', ''),
                    'solution': entry.get('solution', ''),
                    'original_entry': entry
                }
        
        return best_match
    
    def clear_cache(self):
        """Clear all internal caches"""
        self._normalization_cache.clear()
        self.normalize_error_text.cache_clear()
        self._calculate_similarity.cache_clear()
