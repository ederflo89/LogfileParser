"""
Summary Exporter - Erstellt zusammengefasste Berichte und Statistiken
"""

import csv
from typing import List, Tuple, Dict
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from .error_categorizer import ErrorCategorizer


class SummaryExporter:
    """Erstellt zusammengefasste Berichte aus Log-Parsing-Ergebnissen"""
    
    @staticmethod
    def export_grouped_csv(results: List[Tuple], output_path: str, anonymizer=None):
        """
        Exportiert gruppierte/zusammengefasste Fehler
        
        Args:
            results: Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
            output_path: Pfad zur Ausgabe-CSV-Datei
            anonymizer: Optionaler DataAnonymizer für Anonymisierung
        """
        output_file = Path(output_path)
        
        # Gruppiere Fehler nach Kategorie + Kurz-Typ
        grouped_errors = defaultdict(lambda: {
            'count': 0,
            'severity': '',
            'first_occurrence': '',
            'last_occurrence': '',
            'files': set(),
            'full_description': '',
            'category': ''
        })
        
        categorizer = ErrorCategorizer()
        
        for logfile, date, time, severity, log_type, description in results:
            # Kategorisiere Fehler
            category = categorizer.categorize(description, log_type)
            short_type = categorizer.get_short_type(description)
            
            # Verwende Kategorie + Short-Type als Schlüssel
            key = f"{category}|{short_type}"
            
            grouped_errors[key]['count'] += 1
            grouped_errors[key]['severity'] = severity
            grouped_errors[key]['category'] = category
            
            # Zeitstempel
            occurrence = f"{date} {time}"
            if not grouped_errors[key]['first_occurrence']:
                grouped_errors[key]['first_occurrence'] = occurrence
            grouped_errors[key]['last_occurrence'] = occurrence
            
            # Dateien sammeln
            filename = Path(logfile).name
            grouped_errors[key]['files'].add(filename)
            
            # Behalte erste vollständige Description
            if not grouped_errors[key]['full_description']:
                grouped_errors[key]['full_description'] = description
        
        # Schreibe gruppierte CSV
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header
            writer.writerow([
                'Fehler-Kategorie',
                'Fehlertyp',
                'Anzahl',
                'Severity',
                'Erste Occurrence',
                'Letzte Occurrence',
                'Betroffene Dateien',
                'Beispiel-Beschreibung'
            ])
            
            # Sortiere nach Anzahl (häufigste zuerst)
            sorted_errors = sorted(
                grouped_errors.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )
            
            for key, data in sorted_errors:
                category, short_type = key.split('|', 1)
                
                # Anonymisiere Beschreibung wenn Anonymizer vorhanden
                description = data['full_description']
                if anonymizer:
                    description = anonymizer.anonymize_message(description)
                
                writer.writerow([
                    category,
                    short_type,
                    data['count'],
                    data['severity'],
                    data['first_occurrence'],
                    data['last_occurrence'],
                    ', '.join(sorted(data['files']))[:100],  # Max 100 Zeichen
                    description[:200]  # Max 200 Zeichen
                ])
    
    @staticmethod
    def export_statistics(results: List[Tuple], output_path: str, anonymizer=None):
        """
        Erstellt eine Statistik-Textdatei
        
        Args:
            results: Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
            output_path: Pfad zur Ausgabe-Textdatei
            anonymizer: Optionaler DataAnonymizer für Anonymisierung
        """
        output_file = Path(output_path)
        
        # Sammle Statistiken
        total_errors = len(results)
        categories = Counter()
        severities = Counter()
        files = Counter()
        categorizer = ErrorCategorizer()
        
        for logfile, date, time, severity, log_type, description in results:
            category = categorizer.categorize(description, log_type)
            categories[category] += 1
            severities[severity.upper()] += 1
            files[Path(logfile).name] += 1
        
        # Schreibe Statistik
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LOG ANALYSE STATISTIK\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\nGesamt Fehlereinträge: {total_errors:,}\n")
            
            # Anonymisierungs-Stats
            if anonymizer:
                anon_stats = anonymizer.get_stats()
                f.write("\n" + "-" * 80 + "\n")
                f.write("ANONYMISIERUNG\n")
                f.write("-" * 80 + "\n")
                f.write(f"Anonymisierte IPs: {anon_stats['ips_anonymized']}\n")
                f.write(f"Anonymisierte Pfade: {anon_stats['paths_anonymized']}\n")
                f.write(f"Anonymisierte Hostnamen: {anon_stats['hostnames_anonymized']}\n")
                f.write(f"Anonymisierte Dateinamen: {anon_stats['filenames_anonymized']}\n")
            
            # Fehler nach Kategorie
            f.write("\n" + "-" * 80 + "\n")
            f.write("FEHLER NACH KATEGORIE\n")
            f.write("-" * 80 + "\n")
            for category, count in categories.most_common():
                percentage = (count / total_errors * 100) if total_errors > 0 else 0
                f.write(f"{category:20s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Fehler nach Severity
            f.write("\n" + "-" * 80 + "\n")
            f.write("FEHLER NACH SEVERITY\n")
            f.write("-" * 80 + "\n")
            for severity, count in severities.most_common():
                percentage = (count / total_errors * 100) if total_errors > 0 else 0
                f.write(f"{severity:20s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Top 10 betroffene Dateien
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 BETROFFENE LOGDATEIEN\n")
            f.write("-" * 80 + "\n")
            for filename, count in files.most_common(10):
                percentage = (count / total_errors * 100) if total_errors > 0 else 0
                # Anonymisiere Dateinamen wenn gewünscht
                display_name = anonymizer.anonymize_filename(filename) if anonymizer else filename
                f.write(f"{display_name:40s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Top 10 häufigste Fehlertypen
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 HÄUFIGSTE FEHLERTYPEN\n")
            f.write("-" * 80 + "\n")
            
            error_types = Counter()
            for logfile, date, time, severity, log_type, description in results:
                short_type = categorizer.get_short_type(description)
                error_types[short_type] += 1
            
            for error_type, count in error_types.most_common(10):
                percentage = (count / total_errors * 100) if total_errors > 0 else 0
                # Anonymisiere wenn nötig
                display_type = anonymizer.anonymize_message(error_type) if anonymizer else error_type
                f.write(f"{count:6,} ({percentage:5.1f}%) - {display_type}\n")
            
            f.write("\n" + "=" * 80 + "\n")
