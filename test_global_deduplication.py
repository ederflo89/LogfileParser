"""Test für globale Duplikaterkennung über mehrere Logfiles"""
import tempfile
from pathlib import Path
from core.avstumpfl_parser import AVStumpflLogParser

# Erstelle temporäre Test-Logfiles
with tempfile.TemporaryDirectory() as temp_dir:
    temp_path = Path(temp_dir)
    
    # Logfile 1: utility-27110.log
    log1_path = temp_path / "utility-27110.log"
    log1_content = """Sat 04.Oct.  14:08:41.323 ERROR The file handle supplied is not valid.
Sat 04.Oct.  14:08:42.100 ERROR display sync timed out (192.168.210.6 / Output 1)
Sat 04.Oct.  14:08:43.200 ERROR invalid projection matrix (LRTB: 0, 0, 0, 0 / Z-NF: 10, 5e+13)
"""
    log1_path.write_text(log1_content, encoding='utf-8')
    
    # Logfile 2: utility-27110-1.log (Split-File mit identischen Fehlern aber andere Werte!)
    log2_path = temp_path / "utility-27110-1.log"
    log2_content = """Sat 04.Oct.  14:09:10.500 ERROR The file handle supplied is not valid.
Sat 04.Oct.  14:09:11.600 ERROR display sync timed out (10.1.20.88 / Output 1)
Sat 04.Oct.  14:09:12.700 ERROR invalid projection matrix (LRTB: -nan(ind), -nan(ind), -nan(ind), -nan(ind) / Z-NF: 10, 5e+13)
"""
    log2_path.write_text(log2_content, encoding='utf-8')
    
    # Logfile 3: playback-27103.log (anderer Logfile-Typ, wieder gleiche Fehler)
    log3_path = temp_path / "playback-27103.log"
    log3_content = """Sat 11.Oct.  08:59:58.100 ERROR The file handle supplied is not valid.
Sat 11.Oct.  08:59:59.200 ERROR display sync timed out (192.168.210.9 / Output 1)
Sat 11.Oct.  09:00:00.300 ERROR invalid projection matrix (LRTB: 22.3848, -22.3849, 5.77201, -5.77202 / Z-NF: 10, 1e+14)
"""
    log3_path.write_text(log3_content, encoding='utf-8')
    
    print("=== Test: Globale Duplikaterkennung über alle Logfiles ===\n")
    print("Erstellt 3 Testdateien:")
    print(f"  1. {log1_path.name} - 3 Fehler")
    print(f"  2. {log2_path.name} - 3 Fehler (2 identisch mit Datei 1)")
    print(f"  3. {log3_path.name} - 2 Fehler (1 identisch mit Datei 1+2)")
    print()
    print("Erwartung: Nach Pattern-Normalisierung nur 3 unique Fehler:")
    print("  1. 'The file handle supplied is not valid.'")
    print("  2. 'display sync timed out' (normalisiert, IP-Adressen entfernt)")
    print("  3. 'invalid projection matrix' (normalisiert, Parameter entfernt)")
    print()
    print("-" * 80)
    
    # Parse mit EINEM Parser (globale Duplikaterkennung)
    parser = AVStumpflLogParser()
    results = parser.parse_directory(str(temp_path))
    
    print(f"\nErgebnis:")
    print(f"  Unique Fehler in CSV: {len(results)}")
    print(f"  Übersprungene Duplikate: {parser.skipped_duplicates}")
    print()
    
    print("Details der unique Fehler:")
    for i, (logfile, date, time, severity, log_type, desc) in enumerate(results, 1):
        filename = Path(logfile).name
        print(f"  {i}. [{filename}] {log_type}")
    
    print("\n" + "=" * 80)
    
    if len(results) == 3:
        print("✓ TEST BESTANDEN: Nur 3 unique Fehler trotz 8 Gesamt-Fehlern in 3 Dateien!")
        print("✓ Globale Duplikaterkennung funktioniert korrekt!")
    else:
        print(f"✗ TEST FEHLGESCHLAGEN: Erwartet 3, aber {len(results)} gefunden")
    
    print(f"\nReduzierung: {parser.skipped_duplicates + len(results)} → {len(results)} Einträge")
    if parser.skipped_duplicates + len(results) > 0:
        print(f"Das entspricht {len(results) / (parser.skipped_duplicates + len(results)) * 100:.1f}% der Originalgröße")
