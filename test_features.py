"""
Test-Script für die neuen Features
"""

from core.error_categorizer import ErrorCategorizer
from core.anonymizer import DataAnonymizer

# Test Fehler-Kategorisierung
categorizer = ErrorCategorizer()

test_errors = [
    "Connection forcibly closed by the remote host",
    "transferring file from '\\\\192.168.200.5\\share\\file.mov' failed",
    "End of file",
    "authenticating on '\\\\server\\share' failed",
    "decoding 'video.mov' failed: Invalid data",
    "loading module 'ModDatapath' failed"
]

print("=" * 80)
print("FEHLER-KATEGORISIERUNG TEST")
print("=" * 80)

for error in test_errors:
    category = categorizer.categorize(error, '')
    short = categorizer.get_short_type(error)
    print(f"{category:20s} | {short}")

print("\n" + "=" * 80)
print("ANONYMISIERUNGS TEST")
print("=" * 80)

anonymizer = DataAnonymizer()

test_messages = [
    "transferring file from '\\\\192.168.200.5\\DriveShareD\\GH_Integration\\file.mov' to 'D:\\Content\\file.mov' failed",
    "authenticating on '\\\\192.168.205.3\\smb01' failed",
    "decoding 'E:\\HOUS_graded\\GH_LHUB_integration.mov' failed",
]

for msg in test_messages:
    anon = anonymizer.anonymize_message(msg)
    print(f"\nOriginal:     {msg[:80]}...")
    print(f"Anonymisiert: {anon[:80]}...")

print("\n" + "=" * 80)
print("ANONYMISIERUNGS-STATISTIK")
print("=" * 80)

stats = anonymizer.get_stats()
for key, value in stats.items():
    print(f"{key:30s}: {value}")

print("\n✓ Alle Tests erfolgreich!")
