"""
CSV Exporter - Exportiert Parsing-Ergebnisse in CSV-Format
"""

import csv
from typing import List, Tuple
from pathlib import Path


class CSVExporter:
    """Exportiert Log-Parsing-Ergebnisse in CSV-Dateien"""
    
    @staticmethod
    def export(results: List[Tuple[str, str, str]], output_path: str):
        """
        Exportiert Ergebnisse in eine CSV-Datei
        
        Args:
            results: Liste von Tupeln (Logfilename, Severity, Eintragstext)
            output_path: Pfad zur Ausgabe-CSV-Datei
        """
        output_file = Path(output_path)
        
        # Erstelle Verzeichnis falls nicht vorhanden
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header schreiben
            writer.writerow(['Ordner', 'Dateiname', 'Severity', 'Eintragstext'])
            
            # Daten schreiben
            for logfile, severity, text in results:
                # Teile Pfad in Ordner und Dateiname auf
                path = Path(logfile)
                directory = str(path.parent) if path.parent != Path('.') else ''
                filename = path.name
                
                writer.writerow([directory, filename, severity, text])
        
        return output_file
