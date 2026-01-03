# Database Matching - Quick Start Guide

## Overview

The Database Matching system enables automatic matching of log errors against a database of known errors with documented causes and solutions. This feature uses a 3-stage matching strategy to provide high accuracy while maintaining flexibility.

## Quick Start

### 1. Prepare Your Database

Create a CSV file with error entries:

```csv
Type/Source,Description,Cause,Solution,Severity,Fehler-Kategorie
Connection failed,Network timeout,Network connectivity issue,Check network cables,error,Netzwerk
File not found,Cannot locate file,File was moved or deleted,Verify file path,error,Datei
Memory error,Out of memory,Insufficient RAM,Close applications or add RAM,fatal,System
```

### 2. Basic Usage

```python
from core.database_matcher import DatabaseMatcher
from database.turso_client import TursoClient

# Initialize database
client = TursoClient(database_path="your_database.csv")
matcher = DatabaseMatcher(client)

# Match an error
result = matcher.match_error("17x Connection failed")

if result:
    print(f"Match Type: {result['match_type']}")
    print(f"Cause: {result['cause']}")
    print(f"Solution: {result['solution']}")
```

### 3. Using with Analysis Dialog

```python
from ui.analysis_dialog import AnalysisDialog
from database.turso_client import TursoClient

# Initialize database
client = TursoClient(database_path="your_database.csv")

# Error data from log parser
error_data = {
    'error_text': 'Connection failed',
    'description': 'Network timeout occurred',
    'severity': 'error',
    'date': '2024-10-04',
    'time': '18:50:29',
    'filename': 'rx_log.txt',
    'category': 'Netzwerk'
}

# Show analysis dialog
dialog = AnalysisDialog(parent_window, error_data, client)
```

## Matching Stages

The matcher tries three increasingly flexible matching methods:

### Stage 1: Exact Match
Direct string comparison (case-insensitive)
```
Log:  "Connection failed"
DB:   "Connection failed"
→ ✅ EXACT MATCH
```

### Stage 2: Normalized Match
Removes count prefixes and generalizes paths
```
Log:  "17x transferring file from 'D:\file.mov' failed"
DB:   "transferring file from '<SOURCE>' to '<DEST>' failed: <ERROR>"
→ ✅ NORMALIZED MATCH
```

### Stage 3: Fuzzy Match
Similarity-based matching (85%+ threshold)
```
Log:  "Connection forcibly closed"
DB:   "Connection forcefully closed"
→ ✅ FUZZY MATCH (88.9%)
```

## Database Schema

### Required Columns

- `error_text` or `Type/Source` - The error message
- `cause` or `Cause` - Root cause explanation
- `solution` or `Solution` - Recommended solution

### Optional Columns

- `description` or `Description` - Detailed error description
- `severity` or `Severity` - Error severity level
- `category` or `Fehler-Kategorie` - Error category
- `filename` or `Dateiname` - Source file
- `date` or `Datum` - Date of occurrence
- `time` or `Zeit` - Time of occurrence

## Performance

- **Target:** <50ms per match
- **Actual:** ~0.05ms average (1000x faster than target)
- **Optimization:** LRU caching on normalization and similarity calculations

## Testing

Run the comprehensive test suite:

```bash
cd /home/runner/work/LogfileParser/LogfileParser
PYTHONPATH=/home/runner/work/LogfileParser/LogfileParser python tests/test_database_matching.py
```

Run the example script:

```bash
python example_database_matching.py
```

## Documentation

For detailed documentation, see:
- **Architecture:** [docs/DATABASE_MATCHING.md](docs/DATABASE_MATCHING.md)
- **Path Generalization:** [docs/PATH_GENERALIZATION.md](docs/PATH_GENERALIZATION.md)
- **Features:** [FEATURES.md](FEATURES.md)

## Troubleshooting

### No matches found

1. Check database is loaded: `client.get_all_entries()`
2. Try manual normalization: `DatabaseMatcher.normalize_error_text(error_text)`
3. Verify error text exists in database

### Slow performance

1. Clear cache: `matcher.clear_cache()`
2. Check database size (should be <1000 entries for CSV)
3. Consider using Turso cloud backend for larger databases

### Wrong matches

1. Increase fuzzy threshold: `matcher.match_fuzzy(text1, text2, threshold=0.90)`
2. Review normalization patterns
3. Deduplicate database entries

## Example Output

```
Error 1: Connection failed
Context: From exact database match
  ✓ Match found!
    Type: EXACT
    Database entry: "Connection failed"
    Cause: Network connectivity issue
    Solution: Check network cables and router settings

Error 2: 17x Connection failed
Context: From count-prefix normalization
  ✓ Match found!
    Type: NORMALIZED
    Database entry: "Connection failed"
    Cause: Network connectivity issue
    Solution: Check network cables and router settings

Error 3: Connection has failed
Context: From fuzzy matching
  ✓ Match found!
    Type: FUZZY
    Similarity: 89.5%
    Database entry: "Connection failed"
    Cause: Network connectivity issue
    Solution: Check network cables and router settings
```

## Support

For questions or issues, please refer to the main [README.md](README.md) or open an issue on GitHub.
