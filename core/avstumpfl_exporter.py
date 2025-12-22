"""
CSV Exporter für AV Stumpfl Log-Parsing-Ergebnisse
"""

import csv
import re
from typing import List, Tuple, Optional
from pathlib import Path
from .error_categorizer import ErrorCategorizer


class AVStumpflCSVExporter:
    """Exportiert AV Stumpfl Log-Parsing-Ergebnisse in CSV-Dateien"""
    
    @staticmethod
    def _normalize_filename(filename: str) -> str:
        """Entfernt Split-Suffixe aus Dateinamen"""
        # Entferne -1, -2, -3 etc. und -WRITEABLE Suffixe
        normalized = re.sub(r'-\d+\.log$', '.log', filename)
        normalized = re.sub(r'-WRITEABLE\.log$', '.log', normalized)
        return normalized
    
    @staticmethod
    def _extract_count_from_description(description: str) -> Tuple[int, str]:
        """Extrahiert Anzahl aus Description wie '7x 'End of file''"""
        match = re.match(r'^(\d+)x\s+(.+)$', description)
        if match:
            count = int(match.group(1))
            clean_desc = match.group(2).strip("'\"")
            return count, clean_desc
        return 1, description
    
    @staticmethod
    def _shorten_path_in_description(description: str) -> str:
        """Kürzt lange Pfade in Beschreibungen"""
        # Kürze Windows-Pfade (behalte nur letzten Teil)
        description = re.sub(
            r'[A-Z]:[\\\\][^\\\\]+[\\\\][^\\\\]+[\\\\]([^\\\\]+[\\\\])*',
            lambda m: '..\\\\',
            description
        )
        # Kürze UNC-Pfade
        description = re.sub(
            r'\\\\\\\\[^\\\\]+\\\\[^\\\\]+\\\\([^\\\\]+\\\\)*',
            lambda m: '\\\\\\\\...\\\\',
            description
        )
        return description
    
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
        
        # Sammle Zeilen für Duplikaterkennung nach Anonymisierung
        processed_rows = []
        seen_after_anonymization = set()
        
        # Verarbeite alle Einträge
        for logfile, date, time, severity, log_type, description in results:
                # Teile Pfad in Komponenten auf
                path = Path(logfile)
                filename_original = path.name
                
                # Normalisiere Dateinamen (entferne Split-Suffixe)
                filename_normalized = AVStumpflCSVExporter._normalize_filename(filename_original)
                
                # Extrahiere Anzahl aus Description
                count, clean_description = AVStumpflCSVExporter._extract_count_from_description(description)
                
                # Kürze Pfade in Description
                clean_description = AVStumpflCSVExporter._shorten_path_in_description(clean_description)
                
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
                # WICHTIG: Logfile-Gruppe und Dateiname-Original werden NICHT anonymisiert
                # damit man nachvollziehen kann, aus welcher Datei die Fehler stammen
                if anonymizer:
                    remaining_path = anonymizer.anonymize_path(remaining_path) if remaining_path else ''
                    # filename_normalized und filename_original NICHT anonymisieren
                    log_type = anonymizer.anonymize_message(log_type)
                    clean_description = anonymizer.anonymize_message(clean_description)
                
                # Fehler-Kategorie ermitteln wenn aktiviert
                error_category = ''
                if add_category and categorizer:
                    error_category = categorizer.categorize(clean_description, log_type)
                
                # Erstelle Zeile
                row = [log_category, remaining_path, filename_normalized, filename_original, count]
                if add_category:
                    row.append(error_category)
                row.extend([date, time, severity, log_type, clean_description])
                
                # Duplikaterkennung nach Anonymisierung
                # Nutze Severity + Type + Description als Schlüssel
                if anonymizer:
                    dedup_key = f"{severity}|{log_type}|{clean_description}"
                    if dedup_key not in seen_after_anonymization:
                        seen_after_anonymization.add(dedup_key)
                        processed_rows.append(row)
                else:
                    processed_rows.append(row)
        
        # Schreibe alle unique Zeilen
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header schreiben
            header = ['Log-Kategorie', 'Ordner', 'Logfile-Gruppe', 'Dateiname-Original', 'Anzahl']
            if add_category:
                header.append('Fehler-Kategorie')
            header.extend(['Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
            writer.writerow(header)
            
            # Daten schreiben
            for row in processed_rows:
                writer.writerow(row)
        
        return output_file
