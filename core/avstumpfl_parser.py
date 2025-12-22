"""
AV Stumpfl Log Parser - Spezialisiert für AV Stumpfl Logfile-Format
"""

import re
from typing import List, Tuple, Callable
from pathlib import Path
import zipfile


class AVStumpflLogParser:
    """Parst AV Stumpfl Logfiles mit spezifischem Format"""
    
    # Severity-Level Mapping
    SEVERITY_MAP = {
        'V': 'verbose',
        'I': 'info',
        'E': 'error',  # Event oder Error
        'W': 'warning',
        'F': 'fatal',
        'C': 'critical'
    }
    
    # Filter: Nur diese Severities werden extrahiert
    FILTER_SEVERITIES = {'E', 'W', 'F', 'C'}
    
    # Regex für Log-Eintrag: DD.MM.YYYY HH:MM:SS [TAB] SEVERITY [TAB] Type
    LOG_ENTRY_PATTERN = re.compile(
        r'^(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2}:\d{2})\s+([VIWFCE])\s+(.+)$'
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
            
            # Prüfe ob es ein Log-Eintrag ist
            match = self.LOG_ENTRY_PATTERN.match(line)
            
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
                        if self.LOG_ENTRY_PATTERN.match(next_line):
                            break
                        
                        # Füge eingerückte Zeile zur Description hinzu
                        if next_line.startswith('\t') or next_line.startswith('    '):
                            description_lines.append(next_line.strip())
                            i += 1
                        else:
                            break
                    
                    description = '\n'.join(description_lines) if description_lines else ''
                    
                    # Erstelle eindeutigen Schlüssel für Duplikatserkennung
                    # Verwende Type + erste Zeile der Description (ohne Pfade/IPs)
                    first_desc_line = description_lines[0] if description_lines else ''
                    error_key = f"{severity_code}|{log_type}|{first_desc_line}"
                    
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
