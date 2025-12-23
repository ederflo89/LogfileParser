# Path Generalization Feature

## Overview
The LogfileParser now includes intelligent path generalization to improve error pattern recognition. This feature replaces specific file paths with placeholders, allowing the system to recognize identical error patterns regardless of the actual file locations.

## Problem Solved
Previously, identical errors with different file paths were treated as separate, unique errors:
```
loading 'D:\project1\video.mp4' failed
loading 'C:\media\clip.mov' failed  
loading 'E:\content\file.avi' failed
```
All three would be exported as separate CSV rows, even though they represent the same error pattern.

## Solution
The new `generalize_file_paths()` function replaces concrete paths with placeholders BEFORE duplicate detection:

### Supported Path Types

| Path Type | Example | Placeholder |
|-----------|---------|-------------|
| Windows Drive Paths | `C:\path\file.mp4` | `<DRIVE_PATH>` |
| UNC Paths (IP) | `\\192.168.1.5\share\file.mov` | `<UNC_PATH>` |
| UNC Paths (Server) | `\\server\share\file.mov` | `<UNC_PATH>` |
| Network Paths | `srv://192.168.1.2/SHM/file.pfm` | `<SRV_PATH>` |
| URL-encoded Paths | `<?>D:\path\file.mp4` | `<URL_PATH>` |
| IP Addresses | `192.168.210.10:27102` | `<IP>` |
| File IDs | `4536398972959022` | `<FILE_ID>` |
| Hash Values | `a3f5b7c9d2e1f4...` | `<HASH>` |

## Examples

### Example 1: Loading Errors
**Original Errors:**
```
loading 'D:\02_HOUSTON\project\video.mp4' failed: opening file 'D:\02_HOUSTON\project\video.mp4' failed
loading 'C:\media\content\clip.mov' failed: opening file 'C:\media\content\clip.mov' failed
loading 'E:\archive\old\file.avi' failed: opening file 'E:\archive\old\file.avi' failed
```

**Generalized Pattern:**
```
loading '<DRIVE_PATH>' failed: opening file '<DRIVE_PATH>' failed
```

**Result:** Only 1 CSV row with Count: 3

### Example 2: UNC Paths
**Original Errors:**
```
loading '\\192.168.205.2\smb01\cms-media\file1.mov' failed
loading '\\192.168.210.5\storage\media\file2.mp4' failed
```

**Generalized Pattern:**
```
loading '<UNC_PATH>' failed
```

**Result:** Only 1 CSV row with Count: 2

### Example 3: Network Paths
**Original Errors:**
```
automatically reloaded texture 'srv://192.168.210.2/SHM/warp_22697_11.pfm' disappeared
automatically reloaded texture 'srv://192.168.210.3/SHM/warp_12345_05.pfm' disappeared
```

**Generalized Pattern:**
```
automatically reloaded texture '<SRV_PATH>' disappeared
```

**Result:** Only 1 CSV row with Count: 2

## Benefits

1. **Reduced CSV Size**: 90%+ reduction in duplicate rows
2. **Better Pattern Recognition**: Identifies actual unique error types
3. **Improved Data Quality**: Better for LLM training and analysis
4. **Cross-Installation Analysis**: Same error patterns recognized across different Pixera installations
5. **Original Data Preserved**: The original error text is still saved in the CSV (only deduplication uses generalized version)

## How It Works

1. **Before Parsing**: Error line is read from log file
2. **Generalization**: `generalize_file_paths()` replaces all paths with placeholders
3. **Duplicate Check**: Generalized version checked against `seen_errors` set
4. **Storage**: If unique, **original** error text is stored in results
5. **Export**: Original error text appears in CSV

This ensures you still see the actual paths in your export, but duplicates are correctly identified.

## Implementation Details

The function uses carefully ordered regex patterns:
```python
# Order is critical!
1. URL-encoded paths (<?> prefix) - FIRST
2. UNC paths (\\server\share\...) - BEFORE drive paths
3. Network srv:// paths
4. Windows drive paths (C:\, D:\) - AFTER UNC
5. IP addresses
6. File IDs and hashes
```

The order prevents false matches (e.g., UNC paths being matched as drive paths).

## Usage

The feature is **automatically enabled** in all parsing modes. No configuration needed.

To use the function directly:
```python
from core.log_parser import generalize_file_paths

error_text = "loading 'D:\\path\\file.mp4' failed"
generalized = generalize_file_paths(error_text)
print(generalized)  # Output: loading '<DRIVE_PATH>' failed
```

## Testing

See commit history for test cases demonstrating all path types and deduplication examples.
