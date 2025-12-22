"""
Summary Exporter - Erstellt zusammengefasste Berichte und Statistiken
"""

import csv
import re
from typing import List, Tuple, Dict
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
from .error_categorizer import ErrorCategorizer


class SummaryExporter:
    """Erstellt zusammengefasste Berichte aus Log-Parsing-Ergebnissen"""
    
    @staticmethod
    def _normalize_filename(filename: str) -> str:
        """Entfernt Split-Suffixe aus Dateinamen"""
        normalized = re.sub(r'-\d+\.log$', '.log', filename)
        normalized = re.sub(r'-WRITEABLE\.log$', '.log', normalized)
        return normalized
    
    @staticmethod
    def _extract_count_from_description(description: str) -> Tuple[int, str]:
        """Extrahiert Anzahl aus Description"""
        match = re.match(r'^(\d+)x\s+(.+)$', description)
        if match:
            count = int(match.group(1))
            clean_desc = match.group(2).strip("'\"")
            return count, clean_desc
        return 1, description
    
    @staticmethod
    def export_grouped_csv(results: List[Tuple], output_path: str, anonymizer=None):
        """
        Exportiert gruppierte/zusammengefasste Fehler mit Logfile-Gruppierung
        
        Args:
            results: Liste von Tupeln (Logfilename, Datum, Zeit, Severity, Type, Description)
            output_path: Pfad zur Ausgabe-CSV-Datei
            anonymizer: Optionaler DataAnonymizer für Anonymisierung
        """
        output_file = Path(output_path)
        
        # Gruppiere Fehler nach Kategorie + Kurz-Typ + Logfile-Gruppe
        grouped_errors = defaultdict(lambda: {
            'count': 0,
            'total_occurrences': 0,  # Summe aller Counts inkl. "7x similar"
            'severity': '',
            'first_occurrence': '',
            'last_occurrence': '',
            'logfile_groups': Counter(),  # Count pro Logfile-Gruppe
            'full_description': '',
            'category': ''
        })
        
        categorizer = ErrorCategorizer()
        
        for logfile, date, time, severity, log_type, description in results:
            # Kategorisiere Fehler
            category = categorizer.categorize(description, log_type)
            short_type = categorizer.get_short_type(description)
            
            # Extrahiere Anzahl aus Description
            count, clean_desc = SummaryExporter._extract_count_from_description(description)
            
            # Normalisiere Dateinamen
            filename = Path(logfile).name
            normalized_filename = SummaryExporter._normalize_filename(filename)
            
            # Verwende Kategorie + Short-Type als Schlüssel
            key = f"{category}|{short_type}"
            
            grouped_errors[key]['count'] += 1
            grouped_errors[key]['total_occurrences'] += count
            grouped_errors[key]['severity'] = severity
            grouped_errors[key]['category'] = category
            
            # Zeitstempel
            occurrence = f"{date} {time}"
            if not grouped_errors[key]['first_occurrence']:
                grouped_errors[key]['first_occurrence'] = occurrence
            grouped_errors[key]['last_occurrence'] = occurrence
            
            # Logfile-Gruppen sammeln
            grouped_errors[key]['logfile_groups'][normalized_filename] += count
            
            # Behalte erste vollständige Description
            if not grouped_errors[key]['full_description']:
                grouped_errors[key]['full_description'] = clean_desc
        
        # Schreibe gruppierte CSV
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Header
            writer.writerow([
                'Fehler-Kategorie',
                'Fehlertyp',
                'Unique Einträge',
                'Gesamt-Vorkommen',
                'Severity',
                'Erste Occurrence',
                'Letzte Occurrence',
                'Betroffene Logfiles',
                'Top Logfiles (Count)',
                'Beispiel-Beschreibung'
            ])
            
            # Sortiere nach Gesamt-Vorkommen (häufigste zuerst)
            sorted_errors = sorted(
                grouped_errors.items(),
                key=lambda x: x[1]['total_occurrences'],
                reverse=True
            )
            
            for key, data in sorted_errors:
                category, short_type = key.split('|', 1)
                
                # Anonymisiere Beschreibung wenn Anonymizer vorhanden
                description = data['full_description']
                if anonymizer:
                    description = anonymizer.anonymize_message(description)
                
                # Top 3 Logfiles mit höchsten Counts
                top_logfiles = data['logfile_groups'].most_common(3)
                top_logfiles_str = ', '.join([f"{lf} ({cnt})" for lf, cnt in top_logfiles])
                
                writer.writerow([
                    category,
                    short_type,
                    data['count'],
                    data['total_occurrences'],
                    data['severity'],
                    data['first_occurrence'],
                    data['last_occurrence'],
                    len(data['logfile_groups']),
                    top_logfiles_str[:150],  # Max 150 Zeichen
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
        logfile_groups = Counter()
        total_occurrences = 0
        categorizer = ErrorCategorizer()
        
        for logfile, date, time, severity, log_type, description in results:
            # Extrahiere Anzahl
            count, clean_desc = SummaryExporter._extract_count_from_description(description)
            total_occurrences += count
            
            category = categorizer.categorize(clean_desc, log_type)
            categories[category] += count
            severities[severity.upper()] += count
            
            # Normalisiere Dateinamen für Gruppierung
            filename = Path(logfile).name
            normalized = SummaryExporter._normalize_filename(filename)
            logfile_groups[normalized] += count
        
        # Schreibe Statistik
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("LOG ANALYSE STATISTIK\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generiert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\nUnique Fehlereinträge: {total_errors:,}\n")
            f.write(f"Gesamt-Vorkommen (inkl. Counts): {total_occurrences:,}\n")
            f.write(f"Unique Logfile-Gruppen: {len(logfile_groups)}\n")
            
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
                percentage = (count / total_occurrences * 100) if total_occurrences > 0 else 0
                f.write(f"{category:20s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Fehler nach Severity
            f.write("\n" + "-" * 80 + "\n")
            f.write("FEHLER NACH SEVERITY\n")
            f.write("-" * 80 + "\n")
            for severity, count in severities.most_common():
                percentage = (count / total_occurrences * 100) if total_occurrences > 0 else 0
                f.write(f"{severity:20s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Top 10 betroffene Logfile-Gruppen
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 BETROFFENE LOGFILE-GRUPPEN\n")
            f.write("-" * 80 + "\n")
            for filename, count in logfile_groups.most_common(10):
                percentage = (count / total_occurrences * 100) if total_occurrences > 0 else 0
                # Anonymisiere Dateinamen wenn gewünscht
                display_name = anonymizer.anonymize_filename(filename) if anonymizer else filename
                f.write(f"{display_name:40s}: {count:6,} ({percentage:5.1f}%)\n")
            
            # Top 10 häufigste Fehlertypen
            f.write("\n" + "-" * 80 + "\n")
            f.write("TOP 10 HÄUFIGSTE FEHLERTYPEN\n")
            f.write("-" * 80 + "\n")
            
            error_types = Counter()
            for logfile, date, time, severity, log_type, description in results:
                count, clean_desc = SummaryExporter._extract_count_from_description(description)
                short_type = categorizer.get_short_type(clean_desc)
                error_types[short_type] += count
            
            for error_type, count in error_types.most_common(10):
                percentage = (count / total_occurrences * 100) if total_occurrences > 0 else 0
                # Anonymisiere wenn nötig
                display_type = anonymizer.anonymize_message(error_type) if anonymizer else error_type
                f.write(f"{count:6,} ({percentage:5.1f}%) - {display_type}\n")
            
            f.write("\n" + "=" * 80 + "\n")
