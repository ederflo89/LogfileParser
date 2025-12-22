"""
CSV Exporter für AV Stumpfl Log-Parsing-Ergebnisse
"""

import csv
from typing import List, Tuple
from pathlib import Path


class AVStumpflCSVExporter:
    """Exportiert AV Stumpfl Log-Parsing-Ergebnisse in CSV-Dateien"""
    
    @staticmethod
    def export(results: List[Tuple[str, str, str, str, str, str]], output_path: str):
        """
        Exportiert Ergebnisse in eine CSV-Datei
        
        Args:
            results: Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
            output_path: Pfad zur Ausgabe-CSV-Datei
        """
        output_file = Path(output_path)
        
        # Erstelle Verzeichnis falls nicht vorhanden
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header schreiben
            writer.writerow(['Logfilename', 'Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
            
            # Daten schreiben
            for logfile, date, time, severity, log_type, description in results:
                writer.writerow([logfile, date, time, severity, log_type, description])
        
        return output_file
