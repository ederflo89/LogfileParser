"""
Turso Client - Database client for error database operations

Provides methods for querying and managing the error database.
Supports both local CSV and Turso cloud database backends.
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from functools import lru_cache
from core.database_matcher import DatabaseMatcher


class TursoClient:
    """
    Database client for error database operations
    
    Supports:
    - CSV file backend (for local development and testing)
    - Turso cloud database (for production)
    - Cached queries for performance
    """
    
    def __init__(self, database_path: Optional[str] = None, connection_string: Optional[str] = None):
        """
        Initialize the TursoClient
        
        Args:
            database_path: Path to local CSV database file (for CSV backend)
            connection_string: Turso connection string (for cloud backend)
        """
        self.database_path = database_path
        self.connection_string = connection_string
        self.use_csv = database_path is not None
        self._cache = {}
        
        if not self.use_csv and not connection_string:
            raise ValueError("Either database_path or connection_string must be provided")
    
    def _load_csv_entries(self) -> List[Dict[str, Any]]:
        """
        Load all entries from CSV database
        
        Returns:
            List of database entries as dictionaries
        """
        if not self.database_path:
            return []
        
        db_file = Path(self.database_path)
        if not db_file.exists():
            return []
        
        entries = []
        try:
            with open(db_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Extract relevant fields
                    entry = {
                        'error_text': row.get('Type/Source', '') or row.get('error_text', ''),
                        'description': row.get('Description', '') or row.get('description', ''),
                        'cause': row.get('Cause', '') or row.get('cause', ''),
                        'solution': row.get('Solution', '') or row.get('solution', ''),
                        'severity': row.get('Severity', '') or row.get('severity', ''),
                        'category': row.get('Fehler-Kategorie', '') or row.get('category', ''),
                        'filename': row.get('Dateiname', '') or row.get('filename', ''),
                        'date': row.get('Datum', '') or row.get('date', ''),
                        'time': row.get('Zeit', '') or row.get('time', ''),
                    }
                    entries.append(entry)
        except Exception as e:
            print(f"Error loading CSV database: {e}")
            return []
        
        return entries
    
    def get_all_entries(self) -> List[Dict[str, Any]]:
        """
        Get all database entries
        
        Returns:
            List of all database entries
        """
        if self.use_csv:
            return self._load_csv_entries()
        else:
            # TODO: Implement Turso query
            return []
    
    def find_entries_by_normalized_text(self, normalized_text: str) -> List[Dict[str, Any]]:
        """
        Find database entries matching the normalized text
        
        This method normalizes all database entries and compares them
        with the provided normalized text.
        
        Args:
            normalized_text: Normalized error text to search for
            
        Returns:
            List of matching database entries
        """
        all_entries = self.get_all_entries()
        matching_entries = []
        
        for entry in all_entries:
            # Normalize the database entry text
            db_text = entry.get('error_text', '')
            if not db_text:
                continue
            
            normalized_db = DatabaseMatcher.normalize_error_text(db_text)
            
            # Compare normalized texts
            if normalized_db.lower() == normalized_text.lower():
                matching_entries.append(entry)
        
        return matching_entries
    
    @lru_cache(maxsize=128)
    def get_entry_by_text_cache(self, error_text: str) -> Optional[Dict[str, Any]]:
        """
        Get database entry by error text (cached)
        
        Uses LRU cache to avoid repeated database lookups for the same error.
        
        Args:
            error_text: Error text to search for
            
        Returns:
            Matching database entry or None
        """
        # Normalize the search text
        normalized = DatabaseMatcher.normalize_error_text(error_text)
        
        # Find matching entries
        matches = self.find_entries_by_normalized_text(normalized)
        
        # Return first match (best match)
        return matches[0] if matches else None
    
    def clear_cache(self):
        """Clear the LRU cache"""
        self.get_entry_by_text_cache.cache_clear()
        self._cache.clear()
    
    def close(self):
        """Close database connection (if any)"""
        # For CSV backend, no connection to close
        # For Turso backend, implement connection cleanup
        self.clear_cache()
