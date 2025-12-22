"""
Test für verbesserte Duplikatserkennung
"""

from core.avstumpfl_parser import AVStumpflLogParser

# Test Normalisierungsfunktion
parser = AVStumpflLogParser()

test_messages = [
    "transferring file from '\\\\192.168.200.5\\DriveShareD\\GH_Integration_Delivery\\SKIE_A\\GH_DP4_SKIE_A_5760X1416_202510021510.mov' failed",
    "transferring file from '\\\\192.168.200.5\\DriveShareD\\GH_Integration_Delivery\\SKIE_A\\GH_DP5_SKIE_A_5760X1416_202510021510.mov' failed",
    "transferring file from '\\\\192.168.200.5\\DriveShareD\\GH_Integration_Delivery\\TOWN\\GH_DP1_TOWN_5760x1416_202510021426.mov' failed",
    "transferring file from 'SHM/warp_24984_104.pfm' to 'srv://192.168.210.2/SHM/warp_24984_104.pfm' failed",
    "transferring file from 'SHM/warp_25000_112.pfm' to 'srv://192.168.210.2/SHM/warp_25000_112.pfm' failed",
    "automatically reloaded texture 'srv://192.168.210.2/SHM/warp_22811_40.pfm' disappeared",
    "automatically reloaded texture 'srv://192.168.210.2/SHM/warp_22815_46.pfm' disappeared",
]

print("=" * 80)
print("NORMALISIERUNGS-TEST FÜR DUPLIKATSERKENNUNG")
print("=" * 80)

normalized_set = set()
duplicates = 0
unique = 0

for msg in test_messages:
    normalized = parser._normalize_for_deduplication(msg)
    
    if normalized in normalized_set:
        duplicates += 1
        status = "DUPLIKAT"
    else:
        normalized_set.add(normalized)
        unique += 1
        status = "UNIQUE"
    
    print(f"\n{status}:")
    print(f"  Original:     {msg[:70]}...")
    print(f"  Normalisiert: {normalized[:70]}...")

print("\n" + "=" * 80)
print(f"Ergebnis: {unique} unique, {duplicates} Duplikate erkannt")
print("=" * 80)

# Zeige alle unique normalisierten Fehler
print("\nAlle unique normalisierten Fehler:")
print("-" * 80)
for i, norm in enumerate(sorted(normalized_set), 1):
    print(f"{i}. {norm}")
