"""
Test-Skript zum Debuggen des AV Stumpfl Parsers
"""

from core.avstumpfl_parser import AVStumpflLogParser

def test_callback(msg):
    print(f"  -> {msg}")

parser = AVStumpflLogParser(progress_callback=test_callback)

print("Starte Parsing von C:\\ProgramData\\AV Stumpfl...")
print("=" * 60)

results = parser.parse_directory("C:\\ProgramData\\AV Stumpfl")

print("=" * 60)
print(f"\nErgebnisse:")
print(f"Gefundene Einträge: {len(results)}")
print(f"Übersprungene Duplikate: {parser.skipped_duplicates}")

if len(results) > 0:
    print(f"\nErste 5 Einträge:")
    for i, (logfile, date, time, severity, log_type, description) in enumerate(results[:5], 1):
        print(f"\n{i}. {severity.upper()} - {log_type}")
        print(f"   Datei: {logfile}")
        print(f"   Zeit: {date} {time}")
        print(f"   Beschreibung: {description[:100]}...")
else:
    print("\nKEINE Einträge gefunden!")
    print("\nPrüfe Filter-Einstellungen:")
    print(f"FILTER_SEVERITIES: {parser.FILTER_SEVERITIES}")
    print(f"LOG_ENTRY_PATTERN: {parser.LOG_ENTRY_PATTERN.pattern}")
