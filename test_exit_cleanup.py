"""Test für automatisches Cache-Cleanup beim Beenden"""
import tempfile
from pathlib import Path
import shutil
import os

def create_test_cache_dirs(count=3):
    """Erstellt Test-Cache-Verzeichnisse"""
    created = []
    for i in range(count):
        temp_dir = tempfile.mkdtemp(prefix="logparser_zip_")
        # Erstelle eine Testdatei
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Test content " * 100)  # ~1.3 KB
        created.append(temp_dir)
    return created

def simulate_exit_cleanup():
    """Simuliert das Exit-Cleanup"""
    try:
        # Sammle alle logparser_zip_* Verzeichnisse
        all_temp_dirs = []
        
        # System-Temp
        temp_base = Path(tempfile.gettempdir())
        all_temp_dirs.extend(list(temp_base.glob("logparser_zip_*")))
        
        # Duplikate entfernen
        all_temp_dirs = list(set(all_temp_dirs))
        
        print(f"Gefundene Cache-Verzeichnisse: {len(all_temp_dirs)}")
        
        # Lösche alle gefundenen Verzeichnisse
        if all_temp_dirs:
            deleted_count = 0
            total_size = 0
            
            for temp_dir in all_temp_dirs:
                try:
                    # Berechne Größe vor dem Löschen
                    size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                    total_size += size
                    print(f"  Lösche: {temp_dir.name} ({size / 1024:.1f} KB)")
                    shutil.rmtree(temp_dir)
                    deleted_count += 1
                except Exception as e:
                    print(f"  Fehler bei {temp_dir.name}: {e}")
            
            if deleted_count > 0:
                size_mb = total_size / (1024 * 1024)
                print(f"\nExit cleanup: {deleted_count} Cache-Verzeichnisse gelöscht ({size_mb:.2f} MB freigegeben)")
                return deleted_count
        else:
            print("Keine Cache-Verzeichnisse gefunden - Cache ist leer")
            return 0
    
    except Exception as e:
        print(f"Exit cleanup warning: {e}")
        return 0

# Test durchführen
print("=" * 60)
print("TEST: Automatisches Cache-Cleanup beim Beenden")
print("=" * 60)
print()

# 1. Erstelle Test-Cache-Verzeichnisse
print("1. Erstelle 3 Test-Cache-Verzeichnisse...")
test_dirs = create_test_cache_dirs(3)
print(f"   Erstellt: {len(test_dirs)} Verzeichnisse")
for d in test_dirs:
    print(f"   - {Path(d).name}")
print()

# 2. Prüfe ob sie existieren
print("2. Prüfe Existenz...")
existing = sum(1 for d in test_dirs if Path(d).exists())
print(f"   {existing} von {len(test_dirs)} existieren")
print()

# 3. Simuliere Exit-Cleanup
print("3. Simuliere Exit-Cleanup...")
deleted = simulate_exit_cleanup()
print()

# 4. Prüfe ob gelöscht
print("4. Prüfe nach Cleanup...")
remaining = sum(1 for d in test_dirs if Path(d).exists())
print(f"   {remaining} von {len(test_dirs)} existieren noch")
print()

if remaining == 0:
    print("✓ SUCCESS: Alle Test-Verzeichnisse wurden gelöscht!")
else:
    print("✗ FEHLER: Einige Verzeichnisse existieren noch!")
