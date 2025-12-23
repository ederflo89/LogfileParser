"""
Log Parser - Extrahiert Fehler aus Logfiles
"""

import os
import re
import zipfile
from typing import List, Tuple, Callable
from pathlib import Path


def generalize_file_paths(text: str) -> str:
    """
    Generalisiert Dateipfade in Fehlermeldungen für bessere Pattern-Erkennung.
    
    Ersetzt konkrete Pfade durch Platzhalter:
    - Windows-Pfade (C:\\..., D:\\...) → <DRIVE_PATH>
    - UNC-Pfade (\\\\server\\share\\...) → <UNC_PATH>
    - Network-Pfade (srv://...) → <SRV_PATH>
    - URL-encoded Pfade (<?>\\D:\\...) → <URL_PATH>
    - IP-Adressen → <IP>
    
    Args:
        text: Zu generalisierender Fehlertext
        
    Returns:
        Generalisierter Text ohne spezifische Pfade
        
    Examples:
        >>> generalize_file_paths("loading 'D:\\\\test\\\\file.mp4' failed")
        "loading '<DRIVE_PATH>' failed"
        
        >>> generalize_file_paths("error on \\\\\\\\192.168.1.5\\\\share\\\\file.mov")
        "error on <UNC_PATH> failed"
    """
    # Kopie des Textes erstellen
    result = text
    
    # 1. URL-encoded Pfade mit <?> Prefix - MUSS ZUERST kommen
    # Matches: '<?>D:\path\file' oder '<?>\\server\share\file'
    result = re.sub(r'<\?>[A-Za-z]:[/\\][^\'"\s]*', '<URL_PATH>', result)
    result = re.sub(r'<\?>\\\\[^\'"\s]+', '<URL_PATH>', result)
    
    # 2. UNC-Pfade (MÜSSEN VOR normalen Pfaden kommen)
    # Matches: '\\192.168.1.5\share\file' oder '\\server\share\file'
    result = re.sub(r'\\\\[\d.]+\\[^\'"\s]*', '<UNC_PATH>', result)
    result = re.sub(r'\\\\[A-Za-z0-9\-_.]+\\[^\'"\s]*', '<UNC_PATH>', result)
    
    # 3. Network srv:// Pfade
    # Matches: 'srv://192.168.1.2/path/file.pfm'
    result = re.sub(r'srv://[\d.]+/[^\s\'\"]*', '<SRV_PATH>', result)
    
    # 4. Windows absolute Pfade (NACH UNC-Pfaden!)
    # Matches: 'C:\path\file.mp4' oder 'D:/path/file.png'
    # Wichtig: Nur Pfade die mit Laufwerksbuchstabe:\ oder :/ starten
    result = re.sub(r'[A-Za-z]:[/\\][^\'"\s]*', '<DRIVE_PATH>', result)
    
    # 5. IP-Adressen ohne Pfad
    # Matches: '192.168.210.10:27102' oder '192.168.1.5'
    result = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(:\d+)?', '<IP>', result)
    
    # 6. Datei-IDs und Hashes (lange Zahlenfolgen/Hex-Strings)
    # Diese werden NACH Pfad-Replacement durchgeführt, um auch IDs in Dateinamen zu erfassen
    result = re.sub(r'\b\d{16,}\b', '<FILE_ID>', result)  # Sehr lange Zahlen wie 4536398972959022_16660441324635355046
    result = re.sub(r'\b[a-f0-9]{32,}\b', '<HASH>', result)  # MD5/SHA Hashes
    
    # 7. Datums-/Zeit-Strings in Dateinamen (z.B. _202509301202, _202510032056)
    result = re.sub(r'_\d{12}', '_<TIMESTAMP>', result)  # _YYYYMMDDHHMI
    result = re.sub(r'_\d{14}', '_<TIMESTAMP>', result)  # _YYYYMMDDHHMMSS
    
    # 8. Pfad-Reste nach bereits ersetzten Platzhaltern entfernen
    # Matches: '<URL_PATH> Resources\path\file' → '<URL_PATH>'
    # Matches: '<DRIVE_PATH> Stumpfl/path/file' → '<DRIVE_PATH>'
    # Wichtig: Muss auch mehrere Wörter/Pfad-Segmente erfassen bis zum nächsten Quote/Space
    result = re.sub(r'<URL_PATH>\s+[^\'\"]*(?=[\'\"\\s]|$)', '<URL_PATH>', result)
    result = re.sub(r'<DRIVE_PATH>\s+[^\'\"]*(?=[\'\"\\s]|$)', '<DRIVE_PATH>', result)
    result = re.sub(r'<UNC_PATH>\s+[^\'\"]*(?=[\'\"\\s]|$)', '<UNC_PATH>', result)
    
    # 9. UNC-Style Pfade mit Platzhalter-IP (//192.168.1.5/share/path)
    result = re.sub(r'//<IP>/[^\s:\'\"]*', '//<IP>/<SHARE_PATH>', result)
    
    # 10. Relative Pfade (SHM/path/file.pfm)
    result = re.sub(r'\b[A-Z]{2,}/[\w/._-]+\.\w+', '<REL_PATH>', result)
    
    # 11. Parameter-IDs (screen_id: 12850, target_id: 12852, mapping_id: 13127)
    result = re.sub(r'(\w+_id):\s*\d+', r'\1: <ID>', result)
    
    # 12. Output/Device/Port Nummern
    result = re.sub(r'\bOutput\s+\d+', 'Output <NUM>', result)
    result = re.sub(r'\bdevice\s+\d+', 'device <NUM>', result)
    result = re.sub(r'\bport\s+\d+', 'port <NUM>', result)
    
    # 13. Matrix-Koordinaten (LRTB: 0, 0, 0, 0 / Z-NF: 10, 5e+13)
    result = re.sub(r'LRTB:\s*[\d\.\-,\s]+', 'LRTB: <COORDS>', result)
    result = re.sub(r'Z-NF:\s*[\d\.\-,\se\+]+', 'Z-NF: <COORDS>', result)
    
    return result


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
                    severity = self._detect_severity(line)
                    if severity:
                        # Generalisiere Pfade für Duplikaterkennung UND Export
                        generalized_line = generalize_file_paths(line)
                        
                        # Prüfe ob dieser Fehler bereits gefunden wurde (basierend auf generalisierter Version)
                        if generalized_line not in self.seen_errors:
                            self.seen_errors.add(generalized_line)
                            self.results.append((
                                str(file_path),
                                severity,
                                generalized_line  # Speichere generalisierte Zeile für CSV Export
                            ))
                            
                            if self.progress_callback:
                                self.progress_callback(
                                    f"Fehler gefunden in {file_path.name}: {severity.upper()}"
                                )
                        else:
                            self.skipped_duplicates += 1
        
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
                                if not line:
                                    continue
                                
                                severity = self._detect_severity(line)
                                if severity:
                                    # Generalisiere Pfade für Duplikaterkennung UND Export
                                    generalized_line = generalize_file_paths(line)
                                    
                                    # Prüfe ob dieser Fehler bereits gefunden wurde (basierend auf generalisierter Version)
                                    if generalized_line not in self.seen_errors:
                                        self.seen_errors.add(generalized_line)
                                        # Verwende ZIP-Pfad + interner Pfad als Dateiname
                                        full_name = f"{zip_path.name}/{txt_file}"
                                        self.results.append((
                                            full_name,
                                            severity,
                                            generalized_line  # Speichere generalisierte Zeile für CSV Export
                                        ))
                                        
                                        if self.progress_callback:
                                            self.progress_callback(
                                                f"Fehler gefunden in {full_name}: {severity.upper()}"
                                            )
                                    else:
                                        self.skipped_duplicates += 1
                    
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
