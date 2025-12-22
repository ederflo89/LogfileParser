"""Test für Cache-Cleanup-Funktionalität"""
import tempfile
from pathlib import Path
import shutil

# Simuliere Cleanup-Logik
temp_base = Path(tempfile.gettempdir())
old_dirs = list(temp_base.glob("logparser_zip_*"))

print(f"Gefundene Cache-Verzeichnisse: {len(old_dirs)}")
print()

total_size = 0
for old_dir in old_dirs:
    try:
        size = sum(f.stat().st_size for f in old_dir.rglob('*') if f.is_file())
        total_size += size
        size_mb = size / (1024 * 1024)
        print(f"  {old_dir.name}: {size_mb:.2f} MB")
    except Exception as e:
        print(f"  {old_dir.name}: Fehler - {e}")

print()
print(f"Gesamtgröße: {total_size / (1024 * 1024):.2f} MB")
print()

# Cleanup durchführen
if old_dirs:
    print("Cleanup wird durchgeführt...")
    deleted = 0
    freed = 0
    
    for old_dir in old_dirs:
        try:
            size = sum(f.stat().st_size for f in old_dir.rglob('*') if f.is_file())
            shutil.rmtree(old_dir)
            deleted += 1
            freed += size
            print(f"  ✓ Gelöscht: {old_dir.name}")
        except Exception as e:
            print(f"  ✗ Fehler bei {old_dir.name}: {e}")
    
    print()
    print(f"Ergebnis: {deleted} Verzeichnisse gelöscht, {freed / (1024 * 1024):.2f} MB freigegeben")
else:
    print("Kein Cleanup nötig - Cache ist leer")
