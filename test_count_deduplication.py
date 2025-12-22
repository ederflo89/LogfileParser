"""Test für Count-Präfix Duplikaterkennung"""
from core.avstumpfl_parser import AVStumpflLogParser

# Test der Normalisierungsfunktion
test_cases = [
    "9x End of file",
    "123 x End of file",
    "17x similar to previous error",
    "5x 'Some error message'",
    "End of file",  # ohne Präfix
    "21552x similar to previous...",
    "1x Single occurrence",
]

print("=== Test: Count-Präfix Normalisierung ===\n")
print("Original → Normalisiert")
print("-" * 60)

for text in test_cases:
    normalized = AVStumpflLogParser._normalize_for_deduplication(text)
    print(f"{text:40} → {normalized}")

print("\n" + "=" * 60)
print("Ergebnis: Alle sollten zu 'End of file', 'previous error', etc. normalisiert werden")
