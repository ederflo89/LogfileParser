"""
Anonymizer - Anonymisiert sensible Daten in Logfiles für LLM-Training
"""

import re
from typing import Dict, Set, Tuple
from pathlib import Path


class DataAnonymizer:
    """Anonymisiert sensible Daten wie IP-Adressen, Pfade, Hostnamen etc."""
    
    def __init__(self):
        self.ip_mapping: Dict[str, str] = {}
        self.path_mapping: Dict[str, str] = {}
        self.hostname_mapping: Dict[str, str] = {}
        self.filename_mapping: Dict[str, str] = {}
        
        self.ip_counter = 1
        self.path_counter = 1
        self.hostname_counter = 1
        self.filename_counter = 1
    
    def anonymize_ip(self, ip: str) -> str:
        """
        Anonymisiert IP-Adressen konsistent
        
        Args:
            ip: IP-Adresse (z.B. 192.168.200.5)
            
        Returns:
            Anonymisierte IP (z.B. 10.0.0.1)
        """
        if ip not in self.ip_mapping:
            self.ip_mapping[ip] = f"10.0.0.{self.ip_counter}"
            self.ip_counter += 1
        return self.ip_mapping[ip]
    
    def anonymize_path(self, path: str, keep_structure: bool = True) -> str:
        """
        Anonymisiert Dateipfade, behält aber Struktur bei
        
        Args:
            path: Originaler Pfad
            keep_structure: Wenn True, behält Ordnerstruktur bei
            
        Returns:
            Anonymisierter Pfad
        """
        if not path or path in ['', '.']:
            return path
        
        if path in self.path_mapping:
            return self.path_mapping[path]
        
        if keep_structure:
            # Behalte Struktur, anonymisiere nur Namen
            parts = Path(path).parts
            anon_parts = []
            
            for part in parts:
                # Behalte Laufwerksbuchstaben und bestimmte Standardordner
                if part in ['C:', 'D:', 'E:', 'Z:', '/', '\\']:
                    anon_parts.append(part)
                elif part.lower() in ['content', 'logs', 'temp', 'data', 'backup']:
                    anon_parts.append(part.lower())
                else:
                    # Anonymisiere, aber behalte Typ (wenn erkennbar)
                    if 'project' in part.lower():
                        anon_parts.append(f'project_{self.path_counter}')
                        self.path_counter += 1
                    elif re.match(r'.*\d{4}[-_]\d{2}[-_]\d{2}', part):  # Datumsmuster
                        anon_parts.append('YYYY-MM-DD')
                    else:
                        anon_parts.append(f'folder_{self.path_counter}')
                        self.path_counter += 1
            
            result = str(Path(*anon_parts)) if anon_parts else ''
        else:
            result = f'<path_{self.path_counter}>'
            self.path_counter += 1
        
        self.path_mapping[path] = result
        return result
    
    def anonymize_filename(self, filename: str, keep_extension: bool = True) -> str:
        """
        Anonymisiert Dateinamen, behält aber Extension bei
        
        Args:
            filename: Originaler Dateiname
            keep_extension: Wenn True, behält Dateiendung bei
            
        Returns:
            Anonymisierter Dateiname
        """
        if not filename:
            return filename
        
        if filename in self.filename_mapping:
            return self.filename_mapping[filename]
        
        if keep_extension and '.' in filename:
            name, ext = filename.rsplit('.', 1)
            # Behalte erkennbare Muster
            if re.match(r'.*[-_]\d+[-_]\d+', name):  # Hat Nummern
                result = f'file_{self.filename_counter}.{ext}'
            else:
                result = f'file_{self.filename_counter}.{ext}'
            self.filename_counter += 1
        else:
            result = f'file_{self.filename_counter}'
            self.filename_counter += 1
        
        self.filename_mapping[filename] = result
        return result
    
    def anonymize_message(self, message: str, keep_errors: bool = True) -> str:
        """
        Anonymisiert eine Fehlermeldung
        
        Args:
            message: Originale Nachricht
            keep_errors: Wenn True, behält Fehlermeldungen bei
            
        Returns:
            Anonymisierte Nachricht
        """
        if not message:
            return message
        
        result = message
        
        # Anonymisiere IP-Adressen
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        for ip in re.findall(ip_pattern, result):
            result = result.replace(ip, self.anonymize_ip(ip))
        
        # Anonymisiere UNC Pfade (\\server\share)
        unc_pattern = r'\\\\([\w\.-]+)\\([\w\$]+)'
        for match in re.finditer(unc_pattern, result):
            server = match.group(1)
            share = match.group(2)
            
            # Prüfe ob Server eine IP ist
            if re.match(r'\d+\.\d+\.\d+\.\d+', server):
                anon_server = self.anonymize_ip(server)
            else:
                if server not in self.hostname_mapping:
                    self.hostname_mapping[server] = f'server_{self.hostname_counter}'
                    self.hostname_counter += 1
                anon_server = self.hostname_mapping[server]
            
            result = result.replace(f'\\\\{server}\\{share}', f'\\\\{anon_server}\\share_{len(self.hostname_mapping)}')
        
        # Anonymisiere absolute Pfade (aber behalte relative Struktur)
        # Windows-Pfade
        win_path_pattern = r'[A-Z]:[/\\][\w\s/\\.-]+'
        for path in re.findall(win_path_pattern, result):
            # Vereinfache lange Pfade zu generischen
            simplified = self._simplify_path(path)
            result = result.replace(path, simplified)
        
        # Unix-Pfade
        unix_path_pattern = r'/[\w/.-]+'
        for path in re.findall(unix_path_pattern, result):
            if len(path) > 10:  # Nur längere Pfade
                simplified = self._simplify_path(path)
                result = result.replace(path, simplified)
        
        return result
    
    def _simplify_path(self, path: str) -> str:
        """
        Vereinfacht einen Pfad zu einem generischen Format
        
        Args:
            path: Originaler Pfad
            
        Returns:
            Vereinfachter Pfad
        """
        parts = Path(path).parts
        
        # Extrahiere wichtige Informationen
        has_content = any('content' in p.lower() for p in parts)
        has_project = any('project' in p.lower() for p in parts)
        has_logs = any('log' in p.lower() for p in parts)
        
        # Behalte Dateiname wenn vorhanden
        filename = parts[-1] if parts and '.' in parts[-1] else None
        extension = Path(filename).suffix if filename else None
        
        # Baue generischen Pfad
        if has_content:
            base = 'Content'
        elif has_project:
            base = 'Projects'
        elif has_logs:
            base = 'Logs'
        else:
            base = 'Data'
        
        # Behalte Dateityp
        if filename and extension:
            return f'{base}/.../*{extension}'
        else:
            return f'{base}/...'
    
    def get_stats(self) -> Dict[str, int]:
        """
        Gibt Statistiken über anonymisierte Daten zurück
        
        Returns:
            Dictionary mit Anzahl anonymisierter Elemente
        """
        return {
            'ips_anonymized': len(self.ip_mapping),
            'paths_anonymized': len(self.path_mapping),
            'hostnames_anonymized': len(self.hostname_mapping),
            'filenames_anonymized': len(self.filename_mapping)
        }
