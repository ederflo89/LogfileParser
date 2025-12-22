"""
Log Parser - Extrahiert Fehler aus Logfiles
"""

import os
import re
import zipfile
from typing import List, Tuple, Callable
from pathlib import Path


class LogParser:
    """Parst Logfiles und extrahiert Fehlereinträge"""
    
    # Severity-Level die gesucht werden sollen
    SEVERITY_LEVELS = ['error', 'fatal', 'critical', 'warning']
    
    def __init__(self, progress_callback: Callable = None):
        """
        Initialisiert den LogParser
        
        Args:
            progress_callback: Callback-Funktion für Fortschrittsmeldungen
        """
        self.progress_callback = progress_callback
        self.results = []
        self.seen_errors = set()  # Set für bereits gefundene Fehlertexte
        self.skipped_duplicates = 0  # Zähler für übersprungene Duplikate
        
    def parse_directory(self, directory_path: str) -> List[Tuple[str, str, str]]:
        """
        Durchsucht ein Verzeichnis rekursiv nach Logfiles
        
        Args:
            directory_path: Pfad zum Verzeichnis
            
        Returns:
            Liste von Tupeln (Logfilename, Severity, Eintragstext)
        """
        self.results = []
        self.seen_errors = set()
        self.skipped_duplicates = 0
        directory = Path(directory_path)
        
        if not directory.exists():
            raise ValueError(f"Verzeichnis nicht gefunden: {directory_path}")
        
        # Durchsuche alle .txt und .zip Dateien rekursiv
        txt_files = list(directory.rglob('*.txt'))
        zip_files = list(directory.rglob('*.zip'))
        
        # Verarbeite .txt Dateien
        for txt_file in txt_files:
            self._parse_file(txt_file)
        
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
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Prüfe auf Severity-Level
                    seve# Prüfe ob dieser Fehler bereits gefunden wurde
                        if line not in self.seen_errors:
                            self.seen_errors.add(line)
                            self.results.append((
                                str(file_path),
                                severity,
                                line
                            ))
                            
                            if self.progress_callback:
                                self.progress_callback(
                                    f"Fehler gefunden in {file_path.name}: {severity.upper()}"
                                )
                        else:
                            self.skipped_duplicates += 1elf.progress_callback(
                                f"Fehler gefunden in {file_path.name}: {severity.upper()}"
                            )
        
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Fehler beim Lesen von {file_path.name}: {str(e)}")
    
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
                # Finde alle .txt Dateien im ZIP
                txt_files = [f for f in zip_ref.namelist() if f.endswith('.txt')]
                
                for txt_file in txt_files:
                    try:
                        # Lese Datei direkt aus ZIP
                        with zip_ref.open(txt_file) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            
                            for line in content.splitlines():
                                line = line.strip()
                                if notPrüfe ob dieser Fehler bereits gefunden wurde
                                    if line not in self.seen_errors:
                                        self.seen_errors.add(line)
                                        # Verwende ZIP-Pfad + interner Pfad als Dateiname
                                        full_name = f"{zip_path.name}/{txt_file}"
                                        self.results.append((
                                            full_name,
                                            severity,
                                            line
                                        ))
                                        
                                        if self.progress_callback:
                                            self.progress_callback(
                                                f"Fehler gefunden in {full_name}: {severity.upper()}"
                                            )
                                    else:
                                        self.skipped_duplicates += 1
                                    
                                    if self.progress_callback:
                                        self.progress_callback(
                                            f"Fehler gefunden in {full_name}: {severity.upper()}"
                                        )
                    
                    except Exception as e:
                        if self.progress_callback:
                            self.progress_callback(
                                f"Fehler beim Lesen von {txt_file} aus ZIP: {str(e)}"
                            )
        
        except Exception as e:
            if self.progress_callback:
                self.progress_callback(f"Fehler beim Öffnen von ZIP {zip_path.name}: {str(e)}")
    
    def _detect_severity(self, line: str) -> str:
        """
        Erkennt Severity-Level in einer Zeile
        
        Args:
            line: Zu prüfende Zeile
            
        Returns:
            Severity-Level oder None
        """
        line_lower = line.lower()
        
        for severity in self.SEVERITY_LEVELS:
            # Suche nach dem Severity-Keyword (case-insensitive)
            # Verwendet Word-Boundaries um Teilwort-Matches zu vermeiden
            pattern = r'\b' + severity + r'\b'
            if re.search(pattern, line_lower):
                return severity
        
        return None
