# LogfileParser - AI Coding Agent Instructions

## Project Purpose
Automated log analysis tool optimized for **AV Stumpfl logfile formats**. Extracts errors, warnings, and critical events from support bundles, normalizes and anonymizes them for LLM training and GDPR compliance, then exports structured CSV data with categorization.

## Architecture Overview

### Module Structure
```
LogfileParser/
├── main.py                     # Entry point - launches Tkinter GUI
├── config.json                 # Persistent settings (database path, temp dir)
├── gui/
│   └── main_window.py          # Tkinter UI with collapsible sections
├── core/
│   ├── avstumpfl_parser.py     # AV Stumpfl format parser (3 date formats, multi-line)
│   ├── avstumpfl_exporter.py   # CSV export with normalization
│   ├── summary_exporter.py     # Grouped summary + statistics export
│   ├── error_categorizer.py    # 7-category semantic classification
│   ├── log_parser.py           # Generic keyword-based parser + path generalization
│   └── csv_exporter.py         # Base CSV export functionality
└── docs/
    └── PATH_GENERALIZATION.md  # Path normalization patterns
```

### Critical Data Flow
1. **File Selection**: GUI → Directory browser → Auto-detect .log/.txt/.zip files
2. **Parsing**: `AVStumpflLogParser.parse()` → Multi-line assembly → Date/Time/Severity extraction
3. **Normalization**: `_normalize_for_deduplication()` → Path/IP placeholders → Duplicate detection
4. **Categorization**: `ErrorCategorizer.categorize()` → Regex-based semantic classification
5. **Export**: CSV with 3 modes (Detailed, Summary, Statistics)

## Development Workflows

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Launch GUI (from project root)
python main.py
```

### Running Tests
```bash
# Run specific test file
python test_normalization.py
python test_count_deduplication.py

# Tests are standalone scripts (no pytest framework)
```

### Database Mode
LogfileParser supports persistent error collection across multiple parsing sessions:
```json
// config.json
{
  "database_file": "C:/path/to/fehler_datenbank.csv",
  "use_database_mode": true,
  "custom_temp_dir": null
}
```

## Critical Patterns & Conventions

### 1. AV Stumpfl Log Format Recognition
Parser detects **3 date formats** automatically:

```
# Format 1: DD.MM.YYYY HH:MM:SS [TAB] SEVERITY [TAB] Type/Source [TAB] Description
04.10.2024 18:50:29	E	Network Error	Connection closed by remote host

# Format 2: YYYY-MM-DD HH:MM:SS [TAB] SEVERITY [TAB] Description
2024-10-04 18:50:29	E	Connection closed by remote host

# Format 3: Day DD.Mon. HH:MM:SS [TAB] SEVERITY [TAB] Type/Source [TAB] Description
Sat 04.Oct. 18:50:29	E	Network Error	Connection closed by remote host
```

**Severity Codes** (case-insensitive):
- `V` = Verbose (skipped)
- `I` = Info (skipped)
- `E` = Error/Event
- `W` = Warning
- `F` = Fatal
- `C` = Critical

**Multi-line Support**: Lines starting with TAB are appended to previous entry (stacktraces)

### 2. Normalization for Deduplication
**Location**: `core/avstumpfl_parser.py::_normalize_for_deduplication()`

Applies **42+ regex patterns** to normalize variable data:

```python
# Count prefixes (MUST be first)
"17x similar to 'error'" → "error"
"9x Connection failed" → "Connection failed"

# Pattern-specific replacements
"Polling6: Module has no input!" → "Polling<NUM>: Module has no input!"
"Live Input 2" → "Live Input <NUM>"

# Generic placeholders (via generalize_file_paths())
"D:\Shows\2024\MyShow\bg.jpg" → "<DRIVE_PATH>"
"\\192.168.1.5\share\file.mov" → "<UNC_PATH>"
"192.168.210.10:27102" → "<IP>"
```

**Result**: 90-95% reduction in CSV rows through deduplication

**SEE**: `docs/PATH_GENERALIZATION.md` for all 8 path placeholder types

### 3. Error Categorization
**Location**: `core/error_categorizer.py`

**7 Semantic Categories** (regex-based):

| Category | Examples | Patterns |
|----------|----------|----------|
| 🌐 **Netzwerk** | Connection closed, timeout | `connection.*closed`, `network.*path.*not.*found` |
| 📁 **Datei** | File not found, permission denied | `file.*not.*found`, `transferring.*file.*failed` |
| ⚙️ **System** | I/O error, thread exit | `i/o.*operation.*aborted`, `memory.*error` |
| 🔐 **Authentifizierung** | Login failed, access denied | `authenticating`, `login.*failed` |
| 🎬 **Media** | Encoding failed, codec error | `encoding.*failed`, `decoder.*error` |
| 🔧 **Modul** | Module loading failed | `loading.*module.*failed` |
| ⏰ **Zeitbezogen** | Timestamp errors | `timestamp`, `system.*time` |

```python
categorizer = ErrorCategorizer()
category = categorizer.categorize("Connection forcibly closed", "")
# Returns: "Netzwerk"
```

### 4. Export Modes

#### Detailed CSV
**Columns**: Log-Kategorie, Ordner, Dateiname, Fehler-Kategorie, Datum, Zeit, Severity, Type/Source, Description

**Use Case**: Full error listing with categorization

#### Summary CSV
**Columns**: Fehler-Kategorie, Fehlertyp, Anzahl, Severity, Erste Occurrence, Letzte Occurrence, Betroffene Dateien, Beispiel-Beschreibung

**Use Case**: Deduplicated overview grouped by error type

**Example**:
```csv
Fehler-Kategorie,Fehlertyp,Anzahl,Severity,Erste Occurrence,Letzte Occurrence,Betroffene Dateien,Beispiel-Beschreibung
Netzwerk,Connection closed,87,error,Sat 04.Oct.,Sat 11.Oct.,"file_1.log, file_2.log","Connection forcibly closed by remote host"
```

#### Statistics TXT
**Content**: Top errors by count, category distribution, severity breakdown

**Use Case**: Quick overview for support ticket analysis

### 5. Anonymization for GDPR/LLM Training
**Optional Feature** (checkbox in GUI)

Replaces sensitive data:
- IPs: `192.168.200.5` → `10.0.0.1` (consistent mapping)
- Paths: `D:\Shows\MyShow\file.mov` → `<DRIVE_PATH>`
- UNC: `\\server\share\file` → `<UNC_PATH>`
- Hostnames: `pixera-server-5` → `server_1`

### 6. Database Mode Workflow
**Purpose**: Accumulate errors across multiple support bundles

**Workflow**:
1. First run: Select output file → Create initial database CSV
2. GUI checkbox: "Use as Database" (stores path in `config.json`)
3. Subsequent runs: Parser loads existing CSV → Merges new errors → Deduplicates
4. Export: Unified CSV with all historical errors

**Global Deduplication Key**: `(error_text, logfile_name)` - same error in different files counts separately

## Common Pitfalls

1. **Count Prefix Normalization Order**: MUST remove "17x similar to..." BEFORE other patterns (see line 29 in avstumpfl_parser.py)
2. **Multi-line Assembly**: TAB-prefixed lines are NOT separate entries - they extend previous entry's description
3. **Severity Filtering**: Only E/W/F/C are exported (V/I are skipped at parse time)
4. **ZIP Handling**: Extracted to temp directory - cleanup happens at start/exit (tracked in `self.temp_dirs`)
5. **Config Persistence**: `config.json` auto-loads on startup - UI state reflects saved settings

## Key Files to Understand

- [core/avstumpfl_parser.py](core/avstumpfl_parser.py#L17) - All 42+ normalization patterns with comments
- [docs/PATH_GENERALIZATION.md](docs/PATH_GENERALIZATION.md) - Path placeholder types and examples
- [core/error_categorizer.py](core/error_categorizer.py) - Regex patterns for 7 categories
- [FEATURES.md](FEATURES.md) - Complete feature documentation with examples
- [README.md](README.md) - User-facing documentation and workflow guide

## Testing Strategy
- **Standalone test scripts** in project root (no pytest)
- `test_normalization.py` - Validates all 42+ normalization patterns
- `test_count_deduplication.py` - Verifies count prefix removal
- `test_database_mode.py` - Tests database merge logic
- `test_global_deduplication.py` - Cross-logfile duplicate detection

**Run tests individually**: `python test_<name>.py`

## GUI Architecture (Tkinter)
- **Collapsible Sections**: Export Options, Database Mode, Temp Directory
- **Threading**: Long operations run in background thread (see `_start_parsing()`)
- **Progress Updates**: `_update_progress()` called from worker thread via queue
- **Settings Persistence**: `_save_settings()` / `_load_settings()` → `config.json`

## CSV Output Conventions
- **Encoding**: UTF-8 with BOM (Excel compatibility)
- **Delimiter**: Comma (standard CSV)
- **Timestamp Format**: Original format preserved from logs
- **Filename Pattern**: `parsed_errors_YYYYMMDD_HHMMSS.csv`

## Documentation Standards
- Document regex patterns with inline comments showing input → output
- Include category classification rationale in error_categorizer.py
- Update PATH_GENERALIZATION.md when adding new placeholder types
- Keep FEATURES.md examples in sync with actual output
