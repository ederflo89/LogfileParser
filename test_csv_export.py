#!/usr/bin/env python3
"""
Test CSV export with source combining for identical errors
"""

from core.avstumpfl_exporter import AVStumpflCSVExporter
from core.log_parser import generalize_file_paths

# Test data: 7 errors that should deduplicate to 2 unique errors
# Format: (logfile_path, date, time, severity, log_type, description)
# WICHTIG: Daten müssen durch generalize_file_paths() normalisiert werden BEVOR CSV-Export!
test_errors_raw = [
    # Group 1: Should combine into ONE entry (5 occurrences from different sources)
    (
        'pixera_logs/log1.txt',
        '2025-01-15',
        '10:30:45',
        'ERROR',
        'MU::RemoteStepping::distributeResourceSideA',
        'Pending steps timed out    side A time: 10:30:44:123   path: /path/to/file1.ext'
    ),
    (
        'rx_logs/log2.txt',
        '2025-01-15',
        '10:30:46',
        'ERROR',
        'MU::RemoteStepping::distributeResourceSideA',
        'Pending steps timed out    side A time: 10:30:45:456   path: /path/to/file2.ext'
    ),
    (
        'pixera_logs/log3.txt',
        '2025-01-15',
        '10:30:47',
        'ERROR',
        'MU::RemoteStepping::distributeResourceSideA',
        'Pending steps timed out    side A time: 10:30:46:789   path: /path/to/file3.ext'
    ),
    (
        'rx_logs/log4.txt',
        '2025-01-15',
        '10:30:48',
        'ERROR',
        'MU::RemoteStepping::distributeResourceSideA',
        'Pending steps timed out    side A time: 10:30:47:012   path: /path/to/file4.ext'
    ),
    (
        'pixera_logs/log5.txt',
        '2025-01-15',
        '10:30:49',
        'ERROR',
        'MU::RemoteStepping::distributeResourceSideA',
        'Pending steps timed out    side A time: 10:30:48:345   path: /path/to/file5.ext'
    ),
    
    # Group 2: Should combine into ONE entry (2 occurrences from different sources)
    (
        'pixera_logs/log6.txt',
        '2025-01-15',
        '11:00:00',
        'ERROR',
        'RX::Manager::dataReceived',
        'Error when applying current usage UsageName1 to computer <IP>'
    ),
    (
        'rx_logs/log7.txt',
        '2025-01-15',
        '11:00:01',
        'ERROR',
        'RX::Manager::dataReceived',
        'Error when applying current usage UsageName2 to computer <IP>'
    )
]

# Normalisiere die Daten wie der Parser es tut
test_errors = []
for logfile, date, time, severity, log_type, description in test_errors_raw:
    normalized_type = generalize_file_paths(log_type)
    normalized_desc = generalize_file_paths(description)
    test_errors.append((logfile, date, time, severity, normalized_type, normalized_desc))

# Export to CSV
output_file = 'd:\\OneDrive - AV Stumpfl GmbH\\01_Projektdateien\\Coding Projekte\\Tools\\LogfileParser\\test_output.csv'
AVStumpflCSVExporter.export(test_errors, output_file)

# Read and analyze output
with open(output_file, 'r', encoding='utf-8-sig') as f:
    lines = f.readlines()

print(f"\n=== CSV Export Test Results ===")
print(f"Input errors: {len(test_errors)}")
print(f"Output lines: {len(lines) - 1}")  # -1 for header
print(f"\nExpected: 2 unique errors (1 with 5 sources, 1 with 2 sources)")
print(f"Actual: {len(lines) - 1} unique errors")
print(f"\nOutput CSV Content:")
print(''.join(lines))

if len(lines) - 1 == 2:
    print("\n✅ TEST PASSED: Correct number of unique errors!")
    
    # Verify sources are combined
    line1_parts = lines[1].split(';')
    line2_parts = lines[2].split(';')
    
    source1 = line1_parts[0]
    source2 = line2_parts[0]
    
    print(f"\nSource 1: {source1}")
    print(f"Source 2: {source2}")
    
    if ',' in source1 and ',' in source2:
        print("✅ Sources are combined with commas")
    else:
        print("❌ Sources are NOT combined correctly")
else:
    print(f"\n❌ TEST FAILED: Expected 2 unique errors, got {len(lines) - 1}")
