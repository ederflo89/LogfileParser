"""
AV Stumpfl Log Parser - Spezialisiert für AV Stumpfl Logfile-Format
"""

import re
from typing import List, Tuple, Callable
from pathlib import Path
import zipfile


class AVStumpflLogParser:
    """Parst AV Stumpfl Logfiles mit spezifischem Format"""
    
    @staticmethod
    def _normalize_for_deduplication(text: str) -> str:
        """
        Normalisiert Text für Duplikatserkennung durch Ersetzen variabler Teile
        
        Args:
            text: Zu normalisierender Text
            
        Returns:
            Normalisierter Text mit Platzhaltern
        """
        normalized = text
        
        # Entferne generische Anzahl-Präfixe (z.B. "9x ...", "123 x ...", "17x similar to...")
        # Dies muss VOR allen anderen Normalisierungen kommen
        normalized = re.sub(r'^\d+\s*x\s+', '', normalized, flags=re.IGNORECASE)
        
        # Entferne umschließende Anführungszeichen
        normalized = re.sub(r"^'(.*)'$", r'\1', normalized)
        
        # Ersetze IP-Adressen durch Platzhalter
        normalized = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '<IP>', normalized)
        
        # Ersetze komplette Dateinamen mit Zahlen und Extensions
        # z.B. GH_DP4_SKIE_A_5760X1416_202510021510.mov → <FILE>
        normalized = re.sub(r'[\w_-]+\d+[\w_-]*\.(mov|mp4|avi|mkv|pfm|png|jpg|jpeg|fbx|obj|log|txt)', '<FILE>', normalized, flags=re.IGNORECASE)
        
        # Ersetze verbleibende Dateinamen mit Extensions
        normalized = re.sub(r'[\w_-]+\.(mov|mp4|avi|mkv|pfm|png|jpg|jpeg|fbx|obj|log|txt)', '<FILE>', normalized, flags=re.IGNORECASE)
        
        # Ersetze UNC-Pfade (\\server\share\path\to\file)
        # Muss NACH Dateinamen-Ersetzung kommen
        normalized = re.sub(r'\\\\[^\\]+\\[^\\]+(?:\\[^\\\'\"]+)*', '<UNC_PATH>', normalized)
        
        # Ersetze Windows-Pfade (D:\path\to\file)
        normalized = re.sub(r'[A-Z]:[\\\/](?:[^\\\/\'\"\s]+[\\\/])*[^\\\/\'\"\s]*', '<WIN_PATH>', normalized)
        
        # Ersetze srv:// URLs
        normalized = re.sub(r'srv://[^\s\'\"]+', '<SRV_URL>', normalized)
        
        # Ersetze Unix-Pfade (/path/to/file oder path/to/file)
        normalized = re.sub(r'(?:^|[\s\'\"])/(?:[^/\s\'\"]+/)*[^/\s\'\"]+', '<UNIX_PATH>', normalized)
        normalized = re.sub(r'(?:^|[\s\'\"])[\w_-]+(?:/[\w_.-]+)+', '<REL_PATH>', normalized)
        
        # Ersetze Zahlenfolgen in verbleibenden Namen (z.B. warp_12345_67)
        normalized = re.sub(r'_\d+(?:_\d+)*', '_<NUM>', normalized)
        
        # Ersetze Zeitstempel und Datums-Patterns
        normalized = re.sub(r'\d{4}[-_]\d{2}[-_]\d{2}[-_]?\d{0,6}', '<TIMESTAMP>', normalized)
        normalized = re.sub(r'\d{8,}', '<LONGNUM>', normalized)
        
        # Ersetze Port-Nummern (nach IP oder Hostname)
        normalized = re.sub(r':\d{4,5}\b', ':<PORT>', normalized)
        
        # Ersetze verbleibende längere Zahlenfolgen
        normalized = re.sub(r'\b\d{4,}\b', '<NUM>', normalized)
        
        return normalized
    
    # Severity-Level Mapping
    SEVERITY_MAP = {
        'V': 'verbose',
        'I': 'info',
        'E': 'error',  # Event oder Error
        'W': 'warning',
        'F': 'fatal',
        'C': 'critical',
        'INFO': 'info',
        'ERROR': 'error',
        'WARN': 'warning',
        'WARNING': 'warning',
        'FATAL': 'fatal',
        'CRITICAL': 'critical'
    }
    
    # Filter: Nur diese Severities werden extrahiert
    FILTER_SEVERITIES = {'E', 'W', 'F', 'C', 'ERROR', 'WARN', 'WARNING', 'FATAL', 'CRITICAL'}
    
    # Regex für Log-Eintrag Format 1: DD.MM.YYYY HH:MM:SS [TAB] SEVERITY [TAB] Type
    LOG_ENTRY_PATTERN_1 = re.compile(
        r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})\s+([VIWFCE])\s+(.+)$'
    )
    
    # Regex für Log-Eintrag Format 2: YYYY-MM-DD HH:MM:SS.mmm [LEVEL] Class.Method
    LOG_ENTRY_PATTERN_2 = re.compile(
        r'^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s+\[(INFO|ERROR|WARN|WARNING|FATAL|CRITICAL)\]\s+(.+)$'
    )
    
    # Regex für Log-Eintrag Format 3: Day DD.Mon. HH:MM:SS.mmm LEVEL Message
    LOG_ENTRY_PATTERN_3 = re.compile(
        r'^(\w{3}\s+\d{2}\.\w{3}\.\s+)(\d{2}:\d{2}:\d{2}\.\d{3})\s+(INFO|ERROR|WARN|WARNING|FATAL|CRITICAL)\s+(.+)$'
    )
    
    def __init__(self, progress_callback: Callable = None):
        """
        Initialisiert den AV Stumpfl LogParser
        
        Args:
            progress_callback: Callback-Funktion für Fortschrittsmeldungen
        """
        self.progress_callback = progress_callback
        self.results = []
        self.seen_errors = set()
        self.skipped_duplicates = 0
        
    def parse_directory(self, directory_path: str) -> List[Tuple[str, str, str, str, str, str]]:
        """
        Durchsucht ein Verzeichnis rekursiv nach Logfiles
        
        Args:
            directory_path: Pfad zum Verzeichnis
            
        Returns:
            Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
        """
        self.results = []
        self.seen_errors = set()
        self.skipped_duplicates = 0
        directory = Path(directory_path)
        
        if not directory.exists():
            raise ValueError(f"Verzeichnis nicht gefunden: {directory_path}")
        
        # Durchsuche alle .log und .txt Dateien rekursiv
        log_files = list(directory.rglob('*.log')) + list(directory.rglob('*.txt'))
        zip_files = list(directory.rglob('*.zip'))
        
        # Verarbeite Logfiles
        for log_file in log_files:
            self._parse_file(log_file)
        
        # Verarbeite .zip Dateien
        for zip_file in zip_files:
            self._parse_zip_file(zip_file)
        
        return self.results
    
    def _parse_file(self, file_path: Path):
        """
        Parst eine einzelne Logfile
        
        Args:
            file_path: Pfad zur Logfile
        """
        if self.progress_callback:
            self.progress_callback(f"Verarbeite: {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            self._parse_log_content(lines, str(file_path))
        
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Fehler beim Lesen von {file_path.name}: {str(e)}")
    
    def _parse_log_content(self, lines: List[str], source_name: str):
        """
        Parst den Inhalt einer Logfile
        
        Args:
            lines: Zeilen der Logfile
            source_name: Name der Quelle (Dateiname)
        """
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Prüfe alle drei Log-Formate
            match = None
            pattern_type = None
            
            # Format 1: DD.MM.YYYY HH:MM:SS SEVERITY Type
            match = self.LOG_ENTRY_PATTERN_1.match(line)
            if match:
                pattern_type = 1
            
            # Format 2: YYYY-MM-DD HH:MM:SS.mmm [LEVEL] Class.Method
            if not match:
                match = self.LOG_ENTRY_PATTERN_2.match(line)
                if match:
                    pattern_type = 2
            
            # Format 3: Day DD.Mon. HH:MM:SS.mmm LEVEL Message
            if not match:
                match = self.LOG_ENTRY_PATTERN_3.match(line)
                if match:
                    pattern_type = 3
            
            if match:
                date = match.group(1)
                time = match.group(2)
                severity_code = match.group(3)
                log_type = match.group(4).strip()
                
                # Prüfe ob dieser Severity-Level relevant ist
                if severity_code in self.FILTER_SEVERITIES:
                    # Lese die nächste(n) Zeile(n) für die Description
                    description_lines = []
                    i += 1
                    
                    # Sammle alle eingerückten Folgezeilen
                    while i < len(lines):
                        next_line = lines[i].rstrip()
                        
                        # Prüfe ob es ein neuer Log-Eintrag ist
                        if (self.LOG_ENTRY_PATTERN_1.match(next_line) or 
                            self.LOG_ENTRY_PATTERN_2.match(next_line) or
                            self.LOG_ENTRY_PATTERN_3.match(next_line)):
                            break
                        
                        # Füge eingerückte Zeile zur Description hinzu
                        if next_line.startswith('\t') or next_line.startswith('    '):
                            description_lines.append(next_line.strip())
                            i += 1
                        else:
                            break
                    
                    description = '\n'.join(description_lines) if description_lines else ''
                    
                    # Erstelle eindeutigen Schlüssel für Duplikatserkennung
                    # Normalisiere Type und Description um variable Teile zu entfernen
                    normalized_type = self._normalize_for_deduplication(log_type)
                    first_desc_line = description_lines[0] if description_lines else ''
                    normalized_desc = self._normalize_for_deduplication(first_desc_line)
                    
                    error_key = f"{severity_code}|{normalized_type}|{normalized_desc}"
                    
                    if error_key not in self.seen_errors:
                        self.seen_errors.add(error_key)
                        
                        severity_name = self.SEVERITY_MAP.get(severity_code, severity_code)
                        
                        self.results.append((
                            source_name,
                            date,
                            time,
                            severity_name,
                            log_type,
                            description
                        ))
                        
                        if self.progress_callback:
                            self.progress_callback(
                                f"Fehler gefunden in {Path(source_name).name}: {severity_name.upper()} - {log_type}"
                            )
                    else:
                        self.skipped_duplicates += 1
                    
                    continue
            
            i += 1
    
    def _parse_zip_file(self, zip_path: Path):
        """
        Extrahiert und parst Logfiles aus einem ZIP-Archiv
        
        Args:
            zip_path: Pfad zum ZIP-Archiv
        """
        if self.progress_callback:
            self.progress_callback(f"Extrahiere ZIP: {zip_path.name}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Finde alle .log und .txt Dateien im ZIP
                log_files = [f for f in zip_ref.namelist() 
                           if f.endswith('.log') or f.endswith('.txt')]
                
                for log_file in log_files:
                    try:
                        # Lese Datei direkt aus ZIP
                        with zip_ref.open(log_file) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            lines = content.splitlines(keepends=True)
                            
                            full_name = f"{zip_path.name}/{log_file}"
                            self._parse_log_content(lines, full_name)
                    
                    except Exception as e:
                        if self.progress_callback:
                            self.progress_callback(
                                f"Fehler beim Lesen von {log_file} aus ZIP: {str(e)}"
                            )
        
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Fehler beim Öffnen von ZIP {zip_path.name}: {str(e)}")
