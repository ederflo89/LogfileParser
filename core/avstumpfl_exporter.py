"""
CSV Exporter für AV Stumpfl Log-Parsing-Ergebnisse
"""

import csv
from typing import List, Tuple, Optional
from pathlib import Path
from .error_categorizer import ErrorCategorizer


class AVStumpflCSVExporter:
    """Exportiert AV Stumpfl Log-Parsing-Ergebnisse in CSV-Dateien"""
    
    @staticmethod
    def export(results: List[Tuple[str, str, str, str, str, str]], output_path: str, 
               anonymizer=None, add_category: bool = True):
        """
        Exportiert Ergebnisse in eine CSV-Datei
        
        Args:
            results: Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
            output_path: Pfad zur Ausgabe-CSV-Datei
            anonymizer: Optionaler DataAnonymizer für Anonymisierung
            add_category: Wenn True, fügt Fehler-Kategorie-Spalte hinzu
        """
        output_file = Path(output_path)
        categorizer = ErrorCategorizer() if add_category else None
        
        # Erstelle Verzeichnis falls nicht vorhanden
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header schreiben
            header = ['Log-Kategorie', 'Ordner', 'Dateiname']
            if add_category:
                header.append('Fehler-Kategorie')
            header.extend(['Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
            writer.writerow(header)
            
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
                
                # Anonymisiere Daten wenn Anonymizer vorhanden
                if anonymizer:
                    remaining_path = anonymizer.anonymize_path(remaining_path) if remaining_path else ''
                    filename = anonymizer.anonymize_filename(filename)
                    log_type = anonymizer.anonymize_message(log_type)
                    description = anonymizer.anonymize_message(description)
                
                # Erstelle Zeile
                row = [log_category, remaining_path, filename]
                
                # Fehler-Kategorie hinzufügen wenn aktiviert
                if add_category and categorizer:
                    error_category = categorizer.categorize(description, log_type)
                    row.append(error_category)
                
                row.extend([date, time, severity, log_type, description])
                writer.writerow(row)
        
        return output_file
