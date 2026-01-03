# LogfileParser - AI Coding Agent Instructions

## Project Purpose
Professional log file parsing and analysis tool optimized for **AV Stumpfl Pixera log files**. Extracts, categorizes, anonymizes, and exports error information for LLM training and system analysis.

## Architecture Overview

### Module Structure
```
LogfileParser/
├── main.py                         # Entry point - launches GUI
├── requirements.txt                # Python dependencies (pandas>=2.0.0)
├── core/                           # Core business logic
│   ├── log_parser.py              # Generic log parser with path generalization
│   ├── csv_exporter.py            # Generic CSV export
│   ├── avstumpfl_parser.py        # AV Stumpfl format parser with normalization
│   ├── avstumpfl_exporter.py      # AV Stumpfl CSV export
│   ├── error_categorizer.py       # Error classification (7 categories)
│   └── summary_exporter.py        # Summary and statistics export
├── gui/                            # User interface
│   └── main_window.py             # Tkinter-based GUI
├── docs/                           # Documentation
│   └── PATH_GENERALIZATION.md     # Path normalization documentation
├── tests/                          # Integration tests
│   └── test_cross_logfile_deduplication.py
└── test_*.py                       # Unit tests for specific features
```

### Critical Data Flow
1. **Log Loading**: User selects directories → Parser scans for .txt/.log/.zip files → Extracts ZIP archives to temp directory
2. **Parsing**: Raw log lines → Format detection (AV Stumpfl vs Generic) → Pattern normalization → Deduplication → Error categorization
3. **Export**: Parsed errors → Multiple formats (Detail CSV, Summary CSV, Statistics TXT) → Optional anonymization

## Development Workflows

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run from project root
python main.py
```

### Testing
```bash
# Run specific test files
python test_normalization.py
python test_count_deduplication.py
python test_pattern_normalization.py
python test_similar_to_fix.py
python test_global_deduplication.py

# Run integration tests
python tests/test_cross_logfile_deduplication.py

# All tests are standalone scripts, no pytest infrastructure
```

### Python Environment
- **Python 3.8+** required
- Dependencies: pandas>=2.0.0 (for CSV export with improved datetime handling and performance)
- GUI: Tkinter (included in standard Python installation)
- No virtual environment configuration in repository

## Critical Patterns & Conventions

### 1. AV Stumpfl Log Format
The parser recognizes three timestamp formats:
```
Format 1: DD.MM.YYYY HH:MM:SS[.mmm] [TAB] SEVERITY [TAB] Type/Source [TAB] Description
Format 2: YYYY-MM-DD HH:MM:SS[.mmm] [TAB] SEVERITY [TAB] Type/Source [TAB] Description
Format 3: Day DD.Mon. HH:MM:SS[.mmm] [TAB] SEVERITY [TAB] Description
```

**Severity Codes** (case-insensitive):
- `V` = Verbose (skipped)
- `I` = Info (skipped)
- `E` = Error/Event (collected)
- `W` = Warning (collected)
- `F` = Fatal (collected)
- `C` = Critical (collected)

**Multi-line Support**: Continuation lines (starting with tab) are appended to previous error.

### 2. Path Generalization (Deduplication Core)
**CRITICAL**: Path generalization happens BEFORE duplicate detection to identify identical error patterns.

```python
from core.log_parser import generalize_file_paths

# Input:  "loading 'D:\project\video.mp4' failed"
# Output: "loading '<DRIVE_PATH>' failed"

# Input:  "\\192.168.1.5\share\file.mov"
# Output: "<UNC_PATH>"
```

**Supported Placeholders** (in order of application):
1. `<URL_PATH>` - URL-encoded paths (`<?>D:\...`)
2. `<UNC_PATH>` - UNC network paths (`\\server\share\...`)
3. `<SRV_PATH>` - Network srv paths (`srv://192.168.x.x/...`)
4. `<DRIVE_PATH>` - Windows drive paths (`C:\...`, `D:\...`)
5. `<IP>` - IP addresses with ports (`192.168.x.x:port`)
6. `<FILE_ID>` - Numeric file IDs (`4536398972959022`)
7. `<HASH>` - Hash values (hex strings 16+ chars)

**WHY**: Achieves 90%+ deduplication of identical errors with different file paths (see `docs/PATH_GENERALIZATION.md`).

**IMPORTANT**: Original error text is preserved in CSV export - generalization is ONLY used for duplicate detection.

### 3. Pattern-Based Normalization (avstumpfl_parser.py)
Before path generalization, the parser applies **pattern-specific normalization**:

```python
# Count prefix removal (MUST be first)
"17x similar to 'error text'" → "error text"
"9x error occurred" → "error occurred"

# Pattern-specific normalization
"transferring file from 'X' to 'Y' failed: Z" → "transferring file from '<SOURCE>' to '<DEST>' failed: <ERROR>"
"Polling6: connection closed" → "Polling<NUM>: connection closed"
"Module.SubModule.Class: error" → "Module.Class: error"
"Module::SubModule::Class: error" → "Module::Class: error"

# Generic replacements
"192.168.1.5" → "<IP>"
"C:\path\file.ext" → "<DRIVE_PATH>"
```

**Order is critical**: Count removal → Pattern-specific → Path generalization → Generic replacements

### 4. Error Categorization
Automatic classification into 7 categories via regex patterns:

| Category | Examples |
|----------|----------|
| **Netzwerk** | connection closed, timeout, UNC paths |
| **Datei** | file not found, transfer failed, permission denied |
| **System** | I/O operation aborted, memory error, thread exit |
| **Authentifizierung** | login failed, access denied |
| **Media** | encoding/decoding failed, codec error |
| **Modul** | module loading failed, linking error |
| **Zeitbezogen** | system time error, timestamp invalid |
| **Sonstige** | Uncategorized errors |

**Usage**:
```python
from core.error_categorizer import ErrorCategorizer

categorizer = ErrorCategorizer()
category = categorizer.categorize("Connection forcibly closed", "")  # Returns: "Netzwerk"
short_type = categorizer.get_short_type("7x 'End of file'")  # Returns: "End of file"
```

### 5. Export Formats

#### Detail CSV (`*_detail.csv`)
All individual errors with optional categorization:
```csv
Log-Kategorie,Ordner,Dateiname,Fehler-Kategorie,Datum,Zeit,Severity,Type/Source,Description
rx_logs,,file.log,Netzwerk,04.Oct.,14:08:41,error,,Connection closed
```

#### Summary CSV (`*_summary.csv`)
Grouped by error type with counts:
```csv
Fehler-Kategorie,Fehlertyp,Anzahl,Severity,Erste Occurrence,Letzte Occurrence,Betroffene Dateien,Beispiel-Beschreibung
Netzwerk,Connection closed,87,error,04.Oct. 14:08,11.Oct. 09:24,file1.log; file2.log,Connection forcibly closed
```

#### Statistics TXT (`*_statistics.txt`)
Overview with top errors and category distribution:
```
=================================================================================
LOG ANALYSE STATISTIK
=================================================================================
Gesamt Fehlereinträge: 119

FEHLER NACH KATEGORIE
---------------------------------------------------------------------------------
Datei               :    89 ( 74.8%)
Netzwerk            :    38 ( 31.9%)
```

### 6. Database Mode (Persistent Collection)
- Stores all errors in a central CSV file (`fehler_datenbank.csv`)
- Enables **cross-logfile deduplication** across multiple parsing sessions
- Tracks first/last occurrence, affected files, and total count
- Updates existing entries when duplicates found
- Use for long-term error tracking across multiple support bundles

### 7. ZIP Archive Handling
- Automatically extracts .zip files to temporary directory
- Default: System temp directory
- Optional: User-defined temp folder (collapsible UI section)
- **CRITICAL**: Cleanup on exit via `_cleanup_temp_dirs()` - DO NOT modify without ensuring cleanup

## Common Pitfalls

1. **Modifying normalization order**: Count removal MUST come before pattern normalization
2. **Path generalization timing**: Must happen BEFORE duplicate detection, but AFTER storing original text
3. **Severity filtering**: Only E/W/F/C are collected; V/I are intentionally skipped
4. **Multi-line handling**: Continuation lines start with tab - don't break this assumption
5. **ZIP cleanup**: Temp directories MUST be cleaned up in `_cleanup_temp_dirs()` and on exit
6. **Pattern regex order**: URL-encoded paths before UNC, UNC before drive paths (prevents false matches)
7. **Error categorization**: Case-insensitive matching - all patterns use `re.IGNORECASE`

## Key Files to Understand

- [README.md](README.md) - Project overview and usage guide
- [FEATURES.md](FEATURES.md) - Detailed feature descriptions with examples
- [docs/PATH_GENERALIZATION.md](docs/PATH_GENERALIZATION.md) - Path normalization deep dive
- [core/avstumpfl_parser.py](core/avstumpfl_parser.py) - All normalization patterns (see `_normalize_for_deduplication` method)
- [core/log_parser.py](core/log_parser.py) - `generalize_file_paths()` function
- [core/error_categorizer.py](core/error_categorizer.py) - Category regex patterns
- [gui/main_window.py](gui/main_window.py) - GUI implementation with collapsible sections

## Testing Strategy
- **Unit tests**: `test_*.py` files in root directory (standalone scripts)
- **Pattern tests**: `test_pattern_normalization.py`, `test_normalization.py`
- **Deduplication tests**: `test_count_deduplication.py`, `test_global_deduplication.py`
- **Integration tests**: `tests/test_cross_logfile_deduplication.py`
- No pytest infrastructure - all tests are runnable Python scripts

## Code Quality Guidelines
- Use type hints for function parameters and return values
- Document regex patterns with comments explaining what they match
- Preserve backward compatibility - existing CSV exports should not change format
- Follow existing naming conventions: snake_case for functions/variables
- Add examples to docstrings for complex functions

## Documentation Standards
- Document **why** decisions were made (e.g., "Count removal must be first to prevent false pattern matches")
- Include regex examples in comments (input → output)
- Update FEATURES.md when adding new export options or categorization
- Keep README.md synchronized with GUI changes
- Add test cases for new normalization patterns

## LLM Training Best Practices
1. ✅ **Enable Error Categorization**: Structures training data
2. ✅ **Enable All Export Formats**: Detail for examples, Summary for patterns, Statistics for overview
3. ✅ **Use Database Mode**: Cross-session deduplication improves data quality
4. ✅ **Anonymization**: Currently removed - planned replacement with enhanced path generalization
5. ✅ **Process Multiple Sources**: Diverse logs increase training quality

## Memory Optimization
- Path generalization reduces in-memory `seen_errors` set size by 90%+
- Database mode offloads deduplication to persistent storage
- ZIP extraction uses temporary files (auto-cleaned) instead of loading to memory
- Large log files are processed line-by-line (no full file loading)

## Future Enhancements (Known Gaps)
- Enhanced anonymization system planned as replacement for removed anonymizer.py
- Performance optimization for >10GB log collections
- Real-time progress updates during parsing (currently shows after completion)
- Export to JSON/SQLite formats
- Command-line interface for batch processing
