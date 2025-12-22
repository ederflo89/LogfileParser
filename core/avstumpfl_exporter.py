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
            writer.writerow(['Log-Kategorie', 'Ordner', 'Dateiname', 'Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
            
            # Daten schreiben
            for logfile, date, time, severity, log_type, description in results:
                # Teile Pfad in Komponenten auf
                path = Path(logfile)
                filename = path.name
                
                # Extrahiere Log-Kategorie (z.B. pixera_hub_logs, rx_logs)
                parts = path.parts
                log_category = ''
                remaining_path = str(path.parent) if path.parent != Path('.') else ''
                
                # Suche nach typischen Log-Ordnern
                for i, part in enumerate(parts):
                    if 'log' in part.lower() or 'rx' in part.lower() or 'pixera' in part.lower():
                        log_category = part
                        # Nimm alles nach der Log-Kategorie als restlichen Pfad
                        if i + 1 < len(parts) - 1:  # -1 weil der Dateiname nicht im Pfad sein soll
                            remaining_path = str(Path(*parts[i+1:-1]))
                        else:
                            remaining_path = ''
                        break
                
                # Falls keine Log-Kategorie gefunden, nutze das erste Unterverzeichnis
                if not log_category and len(parts) > 1:
                    log_category = parts[-2] if len(parts) > 1 else ''
                    remaining_path = str(path.parent) if path.parent != Path('.') else ''
                
                writer.writerow([log_category, remaining_path, filename, date, time, severity, log_type, description])
        
        return output_file
