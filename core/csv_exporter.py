"""
CSV Exporter - Exportiert Parsing-Ergebnisse in CSV-Format
"""

import csv
from typing import List, Tuple
from pathlib import Path
from .error_categorizer import ErrorCategorizer


class CSVExporter:
    """Exportiert Log-Parsing-Ergebnisse in CSV-Dateien"""
    
    @staticmethod
    def export(results: List[Tuple[str, str, str]], output_path: str, 
               add_category: bool = True):
        """
        Exportiert Ergebnisse in eine CSV-Datei
        
        Args:
            results: Liste von Tupeln (Logfilename, Severity, Eintragstext)
            output_path: Pfad zur Ausgabe-CSV-Datei
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
            header.extend(['Severity', 'Eintragstext'])
            writer.writerow(header)
            
            # Daten schreiben
            for logfile, severity, text in results:
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
                
                # Erstelle Zeile
                row = [log_category, remaining_path, filename]
                
                # Fehler-Kategorie hinzufügen wenn aktiviert
                if add_category and categorizer:
                    error_category = categorizer.categorize(text, '')
                    row.append(error_category)
                
                row.extend([severity, text])
                writer.writerow(row)
        
        return output_file
