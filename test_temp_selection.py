"""Test für Temp-Ordner-Auswahl-Feature"""
import tempfile
from pathlib import Path
import shutil

def test_temp_space_info(custom_path=None):
    """Zeigt Speicherplatz-Info für einen Pfad"""
    if custom_path:
        temp_path = Path(custom_path)
    else:
        temp_path = Path(tempfile.gettempdir())
    
    print(f"Temp-Pfad: {temp_path}")
    print(f"Existiert: {temp_path.exists()}")
    
    if temp_path.exists():
        usage = shutil.disk_usage(temp_path)
        free_gb = usage.free / (1024**3)
        total_gb = usage.total / (1024**3)
        percent_free = (usage.free / usage.total) * 100
        
        # Farbe basierend auf verfügbarem Speicher
        if free_gb < 5:
            status = '⚠️ WENIG SPEICHER!'
        elif free_gb < 20:
            status = '⚠️'
        else:
            status = '✓'
        
        drive_info = f"Laufwerk: {temp_path.drive if hasattr(temp_path, 'drive') else temp_path}"
        
        print(f"\n{status} {drive_info}")
        print(f"  Frei:    {free_gb:.1f} GB")
        print(f"  Gesamt:  {total_gb:.1f} GB")
        print(f"  Prozent: {percent_free:.1f}%")
        print()

# Test System-Temp
print("=" * 60)
print("SYSTEM-TEMP (Standard)")
print("=" * 60)
test_temp_space_info()

# Test D-Laufwerk
print("=" * 60)
print("D-LAUFWERK (Alternative)")
print("=" * 60)
test_temp_space_info("D:\\")

# Test mit nicht existierendem Pfad
print("=" * 60)
print("NICHT EXISTIEREND")
print("=" * 60)
test_temp_space_info("X:\\NonExistent")
