"""
Test für Anzahl-Präfix Normalisierung
"""

from core.avstumpfl_parser import AVStumpflLogParser

# Test-Nachrichten mit verschiedenen Anzahlen
test_messages = [
    "17x similar to 'display sync timed out (10.0.0.10 / Output 1)'",
    "9x similar to 'display sync timed out (10.0.0.10 / Output 1)'",
    "23x similar to 'display sync timed out (10.0.0.20 / Output 2)'",
    "5x similar to 'display sync timed out (10.0.0.10 / Output 1)'",
    "display sync timed out (10.0.0.10 / Output 1)",  # Ohne Präfix
    "48x similar to 'display sync timed out (10.0.0.10 / Output 1)'",
]

print("=" * 80)
print("TEST: ANZAHL-PRÄFIX NORMALISIERUNG")
print("=" * 80)
print()

# Normalisiere alle Nachrichten
normalized_messages = {}
for msg in test_messages:
    normalized = AVStumpflLogParser._normalize_for_deduplication(msg)
    
    if normalized not in normalized_messages:
        normalized_messages[normalized] = []
        status = "UNIQUE"
    else:
        status = "DUPLIKAT"
    
    normalized_messages[normalized].append(msg)
    
    print(f"{status}:")
    print(f"  Original:     {msg[:70]}...")
    print(f"  Normalisiert: {normalized[:70]}...")
    print()

print("=" * 80)
print(f"Ergebnis: {len(normalized_messages)} unique, {len(test_messages) - len(normalized_messages)} Duplikate erkannt")
print("=" * 80)
print()
print("Alle unique normalisierten Fehler:")
print("-" * 80)
for i, (normalized, originals) in enumerate(normalized_messages.items(), 1):
    print(f"{i}. {normalized}")
    print(f"   → {len(originals)} Vorkommen")
