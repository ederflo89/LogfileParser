"""Test für 'similar to' Normalisierung"""
from core.avstumpfl_parser import AVStumpflLogParser

# Test-Fälle
test_cases = [
    ("display sync timed out (192.168.210.6 / Output 1)", "Ohne Prefix"),
    ("24x similar to 'display sync timed out (192.168.210.6 / Output 1)'", "Mit Count+Similar"),
    ("invalid projection matrix (LRTB: 0, 0, 0, 0 / Z-NF: 10, 5e+13)", "Ohne Prefix"),
    ("335x similar to 'invalid projection matrix (LRTB: -0.0487481, -0.0487481, 0, 0 / Z-NF: 10, 5e+13)'", "Mit Count+Similar"),
    ("automatically reloaded texture 'srv://192.168.210.2/SHM/warp_22697_11.pfm' disappeared", "Ohne Prefix"),
]

print("=== Test: 'similar to' Prefix Normalisierung ===\n")

for original, description in test_cases:
    normalized = AVStumpflLogParser._normalize_for_deduplication(original)
    print(f"{description:20} | {original[:60]:60} -> {normalized}")

print("\n=== Duplikat-Check ===\n")

# Display Sync
norm1 = AVStumpflLogParser._normalize_for_deduplication("display sync timed out (192.168.210.6 / Output 1)")
norm2 = AVStumpflLogParser._normalize_for_deduplication("24x similar to 'display sync timed out (192.168.210.6 / Output 1)'")
print(f"Display Sync:")
print(f"  Variante 1: '{norm1}'")
print(f"  Variante 2: '{norm2}'")
print(f"  Match: {norm1 == norm2} {'PASS' if norm1 == norm2 else 'FAIL'}\n")

# Projection Matrix
norm3 = AVStumpflLogParser._normalize_for_deduplication("invalid projection matrix (LRTB: 0, 0, 0, 0 / Z-NF: 10, 5e+13)")
norm4 = AVStumpflLogParser._normalize_for_deduplication("335x similar to 'invalid projection matrix (LRTB: -0.0487481, -0.0487481, 0, 0 / Z-NF: 10, 5e+13)'")
print(f"Projection Matrix:")
print(f"  Variante 1: '{norm3}'")
print(f"  Variante 2: '{norm4}'")
print(f"  Match: {norm3 == norm4} {'PASS' if norm3 == norm4 else 'FAIL'}")
