"""Test für Pattern-basierte Normalisierung"""
from core.avstumpfl_parser import AVStumpflLogParser

# Test-Fälle aus dem realen CSV
test_cases = [
    # Transferring file patterns
    ("transferring file from 'D:\\UnrealProjects\\GH_UNREAL_COAT_202412091003\\HOUS_COAT\\Saved\\Logs\\192.168.210.2_preview-backup-2025.07.30-20.16.55.log' to '<bundling>D:\\UnrealProjects\\GH_UNREAL_COAT_202412091003\\HOUS_COAT\\Saved\\Logs\\192.168.210.2_preview-backup-2025.07.30-20.16.55.log' failed: copying failed (LocalHost: error reading src file)",
     "transferring file from '<SOURCE>' to '<DEST>' failed: <ERROR>"),
    
    ("transferring file from 'Projects/.../*.log' to '<utility>HOUS_COAT\\Saved\\Logs\\192.168.210.2_preview.log' failed: copying failed (Receiver: received error signal)",
     "transferring file from '<SOURCE>' to '<DEST>' failed: <ERROR>"),
    
    ("transferring file from 'Data/.../*.mov' to '<default>Data/.../*.mov' failed: file not found (localhost)",
     "transferring file from '<SOURCE>' to '<DEST>' failed: <ERROR>"),
    
    # Loading patterns
    ("loading '<?>\\\\10.0.0.10\\share_0\\cms-media\\GH_DP6_TERA_LOOP_5476x1416_202510032056.mov' failed: opening file '\\\\10.0.0.10\\share_0\\cms-media\\GH_DP6_TERA_LOOP_5476x1416_202510032056.mov' failed",
     "loading '<FILE>' failed: opening file '<FILE>' failed"),
    
    ("loading '<?>Content/.../*.mov' failed: opening file 'Content/.../*.mov' failed",
     "loading '<FILE>' failed: opening file '<FILE>' failed"),
    
    # Error while enumerating
    ("error while enumerating Data/...* : The network path was not found. (53)",
     "error while enumerating <PATH> : <ERROR>"),
    
    ("error while enumerating Data/...* : The user name or password is incorrect. (1326)",
     "error while enumerating <PATH> : <ERROR>"),
    
    ("error while enumerating Data/...* : No more connections can be made to this remote computer at this time because there are already as many connections as the computer can accept. (71)",
     "error while enumerating <PATH> : <ERROR>"),
    
    # Decoding patterns
    ("decoding 'Data/...%3A\\GH_Integration_Delivery\\MURA_STILLS\\MURA_DP1_STILL.jpg' failed",
     "decoding '<FILE>' failed: <ERROR>"),
    
    ("decoding 'Data/.../*.mov' failed: Invalid data found when processing input",
     "decoding '<FILE>' failed: <ERROR>"),
    
    # Create directories
    ('create_directories: The system cannot find the path specified.: "Content/..."',
     "create_directories: <ERROR>"),
    
    # Directory iterator
    ('directory_iterator::directory_iterator: The system cannot find the path specified.: "Data/..."',
     "directory_iterator: <ERROR>"),
    
    # Authenticating
    ("authenticating on '\\\\10.0.0.6\\share_0' failed: Multiple connections to a server or shared resource by the same user, using more than one user name, are not allowed.",
     "authenticating on '<PATH>' failed: <ERROR>"),
    
    # Additional patterns from CSV
    ("updating render task failed: importing texture memory failed",
     "updating render task failed: <ERROR>"),
    
    ("updating render task failed: importing semaphore failed",
     "updating render task failed: <ERROR>"),
    
    ("encoding frame failed: software scaling failed",
     "encoding frame failed: <ERROR>"),
    
    ("assertion 'referenced' failed in graph::GraphImpl::create_referenced_node",
     "assertion failed in <LOCATION>"),
    
    ("loading module 'ModDatapath' failed: linking shared object failed",
     "loading module failed: <ERROR>"),
    
    ("invalid projection matrix (LRTB: 0, 0, 0, 0 / Z-NF: 10, 5e+13)",
     "invalid projection matrix"),
    
    ("invalid projection matrix (LRTB: -0.0487481, -0.0487481, 0, 0 / Z-NF: 10, 5e+13)",
     "invalid projection matrix"),
    
    ("automatically reloaded texture 'srv:Data/.../*.pfm' disappeared",
     "automatically reloaded texture disappeared"),
    
    ("display sync timed out (10.0.0.3 / Output 1)",
     "display sync timed out"),
]

print("=== Test: Pattern-basierte Normalisierung ===\n")
print(f"{'Status':<8} {'Original':<80} → Normalisiert")
print("-" * 180)

passed = 0
failed = 0

for original, expected in test_cases:
    normalized = AVStumpflLogParser._normalize_for_deduplication(original)
    
    if normalized == expected:
        status = "✓ PASS"
        passed += 1
    else:
        status = "✗ FAIL"
        failed += 1
    
    # Kürze Original für bessere Darstellung
    short_original = original[:77] + "..." if len(original) > 80 else original
    
    print(f"{status:<8} {short_original:<80}")
    if normalized != expected:
        print(f"         Expected: {expected}")
        print(f"         Got:      {normalized}")
        print()

print("\n" + "=" * 180)
print(f"Ergebnis: {passed} passed, {failed} failed")
print(f"\nVorher hätten diese {len(test_cases)} Einträge {len(test_cases)} separate Zeilen im CSV.")
print(f"Nach Normalisierung: Viele werden zu denselben Patterns → drastisch weniger Zeilen!")
