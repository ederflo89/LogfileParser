"""
Error Categorizer - Kategorisiert Fehler nach Typ
"""

import re
from typing import Tuple


class ErrorCategorizer:
    """Kategorisiert Fehler in verschiedene Typen für bessere Analyse"""
    
    # Fehler-Kategorien mit Regex-Patterns
    CATEGORIES = {
        'Netzwerk': [
            r'connection.*closed',
            r'network.*path.*not.*found',
            r'network.*error',
            r'timeout',
            r'connection.*refused',
            r'connection.*reset',
            r'authenticating.*failed',
            r'smb\d+.*failed',
            r'\\\\[\d\.]+\\',  # UNC Pfade
        ],
        'Datei': [
            r'file.*not.*found',
            r'transferring.*file.*failed',
            r'copying.*failed',
            r'file.*handle',
            r'end.*of.*file',
            r'cannot.*open.*file',
            r'permission.*denied',
            r'file.*exists',
        ],
        'System': [
            r'i/o.*operation.*aborted',
            r'thread.*exit',
            r'application.*request',
            r'memory.*error',
            r'access.*violation',
            r'null.*reference',
        ],
        'Authentifizierung': [
            r'authenticating',
            r'authentication.*failed',
            r'login.*failed',
            r'unauthorized',
            r'access.*denied',
            r'permission',
        ],
        'Media': [
            r'encoding.*failed',
            r'decoding.*failed',
            r'invalid.*data.*processing.*input',
            r'software.*scaling.*failed',
            r'codec.*error',
            r'frame.*failed',
        ],
        'Modul': [
            r'loading.*module.*failed',
            r'module.*not.*found',
            r'linking.*shared.*object.*failed',
            r'dll.*not.*found',
        ],
        'Zeitbezogen': [
            r'system.*time.*changed',
            r'timestamp',
            r'timeout',
        ]
    }
    
    @staticmethod
    def categorize(error_message: str, error_type: str = '') -> str:
        """
        Kategorisiert einen Fehler basierend auf der Fehlermeldung
        
        Args:
            error_message: Die Fehlermeldung
            error_type: Optionaler Fehlertyp aus dem Log
            
        Returns:
            Kategorie-Name oder 'Sonstige'
        """
        # Kombiniere error_type und error_message für bessere Erkennung
        combined_text = f"{error_type} {error_message}".lower()
        
        # Prüfe jede Kategorie
        for category, patterns in ErrorCategorizer.CATEGORIES.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    return category
        
        return 'Sonstige'
    
    @staticmethod
    def get_short_type(description: str) -> str:
        """
        Erstellt einen kurzen Fehlertyp aus der Description
        
        Args:
            description: Die vollständige Fehlerbeschreibung
            
        Returns:
            Kurzer Fehlertyp (max 50 Zeichen)
        """
        # Extrahiere den Hauptfehler (vor dem ersten Doppelpunkt oder bis zu 50 Zeichen)
        if ':' in description:
            short = description.split(':')[0].strip()
        else:
            short = description[:50].strip()
        
        # Entferne häufige Prefix-Muster
        short = re.sub(r'^\d+x\s+', '', short)  # Entferne "7x " Prefix
        short = re.sub(r'^similar to\s+', '', short)  # Entferne "similar to" Prefix
        
        return short if len(short) <= 50 else short[:47] + '...'
