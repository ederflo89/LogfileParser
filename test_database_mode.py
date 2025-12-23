"""Test für Datenbank-Modus (Persistente Fehlersammlung)"""
from pathlib import Path
from core.avstumpfl_exporter import AVStumpflCSVExporter
import csv

# Test-Daten
test_results_1 = [
    ("rx_logs/playback.log", "2025-12-23", "10:00:00", "E", "End of file", "Error reading file"),
    ("rx_logs/playback.log", "2025-12-23", "10:01:00", "W", "WATCHDOG TIMEOUT", "Connection lost"),
    ("rx_logs/manager.log", "2025-12-23", "10:02:00", "E", "System error", "Out of memory"),
]

test_results_2 = [
    ("rx_logs/playback.log", "2025-12-23", "11:00:00", "E", "End of file", "Error reading file"),  # DUPLIKAT
    ("rx_logs/utility.log", "2025-12-23", "11:01:00", "E", "Network error", "Connection refused"),  # NEU
    ("pixera_logs/rx_log.txt", "2025-12-23", "11:02:00", "F", "Fatal error", "System crash"),  # NEU
]

def test_database_mode():
    """Testet die Datenbank-Funktionalität"""
    print("=" * 70)
    print("TEST: Datenbank-Modus (Persistente Fehlersammlung)")
    print("=" * 70)
    print()
    
    # 1. Erstelle neue Datenbank mit ersten Einträgen
    print("1. ERSTER SCAN - Neue Datenbank erstellen")
    print("-" * 70)
    db_path = "test_database.csv"
    
    db_file, new_entries, total_entries = AVStumpflCSVExporter.export_to_database(
        test_results_1,
        db_path,
        anonymizer=None,
        add_category=True
    )
    
    print(f"✓ Datenbank erstellt: {db_file.name}")
    print(f"  • Neue Einträge: {new_entries}")
    print(f"  • Gesamt: {total_entries}")
    print()
    
    # Zeige Inhalt
    with open(db_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"  Inhalt ({len(rows)} Zeilen):")
        for i, row in enumerate(rows, 1):
            print(f"    {i}. [{row['Severity']}] {row['Type/Source']}: {row['Description']}")
    print()
    
    # 2. Zweiter Scan - Datenbank erweitern
    print("2. ZWEITER SCAN - Datenbank erweitern")
    print("-" * 70)
    
    db_file, new_entries, total_entries = AVStumpflCSVExporter.export_to_database(
        test_results_2,
        db_path,
        anonymizer=None,
        add_category=True
    )
    
    print(f"✓ Datenbank erweitert: {db_file.name}")
    print(f"  • Neue Einträge: {new_entries} (1 Duplikat erkannt)")
    print(f"  • Gesamt: {total_entries}")
    print()
    
    # Zeige Inhalt
    with open(db_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"  Inhalt ({len(rows)} Zeilen):")
        for i, row in enumerate(rows, 1):
            log_cat = row['Log-Kategorie'] if row['Log-Kategorie'] else '?'
            print(f"    {i}. [{row['Severity']}] [{log_cat}] {row['Type/Source']}: {row['Description']}")
    print()
    
    # 3. Validierung
    print("3. VALIDIERUNG")
    print("-" * 70)
    
    expected_total = 5  # 3 aus Scan 1 + 2 neue aus Scan 2 (1 Duplikat)
    
    if total_entries == expected_total:
        print(f"✓ SUCCESS: Korrekte Anzahl ({expected_total} Einträge)")
    else:
        print(f"✗ FEHLER: Erwartete {expected_total}, aber {total_entries} gefunden")
    
    if new_entries == 2:
        print(f"✓ SUCCESS: Duplikaterkennung funktioniert (2 neue, 1 ignoriert)")
    else:
        print(f"✗ FEHLER: Erwartete 2 neue Einträge, aber {new_entries} gefunden")
    
    # Cleanup
    Path(db_path).unlink()
    print()
    print(f"✓ Test-Datenbank gelöscht: {db_path}")
    print()
    print("=" * 70)

if __name__ == "__main__":
    test_database_mode()
