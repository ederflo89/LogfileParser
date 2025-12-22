"""
Test-Skript für die neuen Log-Verzeichnisse
"""

from core.avstumpfl_parser import AVStumpflLogParser

def test_callback(msg):
    print(f"  -> {msg}")

parser = AVStumpflLogParser(progress_callback=test_callback)

test_dirs = [
    r"D:\Unconfirmed 536085 - Copy\PX4-26536-DIR-01",
    r"D:\Unconfirmed 536085 - Copy\PX4-26538-DUAL-04"
]

for test_dir in test_dirs:
    print(f"\nStarte Parsing von {test_dir}...")
    print("=" * 60)
    
    try:
        results = parser.parse_directory(test_dir)
        
        print("=" * 60)
        print(f"\nErgebnisse für {test_dir}:")
        print(f"Gefundene Einträge: {len(results)}")
        print(f"Übersprungene Duplikate: {parser.skipped_duplicates}")
        
        if len(results) > 0:
            print(f"\nErste 3 Einträge:")
            for i, (logfile, date, time, severity, log_type, description) in enumerate(results[:3], 1):
                print(f"\n{i}. {severity.upper()} - {log_type[:50]}")
                print(f"   Zeit: {date} {time}")
                print(f"   Beschreibung: {description[:80]}...")
    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()
