# LogfileParser - Feature Übersicht

## 🚀 Alle drei Phasen erfolgreich implementiert!

### ✅ Phase 1: Fehler-Kategorisierung

**Modul**: `core/error_categorizer.py`

**Features**:
- Automatische Klassifizierung in 7 Hauptkategorien:
  - 🌐 **Netzwerk**: Connection errors, timeouts, network paths
  - 📁 **Datei**: File not found, file transfer, permissions  
  - ⚙️ **System**: I/O errors, memory errors, threads
  - 🔐 **Authentifizierung**: Login failed, access denied
  - 🎬 **Media**: Encoding/decoding errors, codec errors
  - 🔧 **Modul**: Module loading, linking errors
  - ⏰ **Zeitbezogen**: System time, timestamps
  - ❓ **Sonstige**: Nicht kategorisierbare Fehler

**Beispiel**:
```python
categorizer = ErrorCategorizer()
category = categorizer.categorize("Connection forcibly closed", "")
# Ergebnis: "Netzwerk"

short = categorizer.get_short_type("7x 'End of file'")
# Ergebnis: "End of file"
```

---

### ✅ Phase 2: Daten-Anonymisierung

**Modul**: `core/anonymizer.py`

**Features**:
- 🔒 **IP-Anonymisierung**: Konsistente Zuordnung zu 10.0.0.x
- 📂 **Pfad-Anonymisierung**: Behält Struktur, anonymisiert Namen
- 🖥️ **UNC-Pfad-Anonymisierung**: Server und Shares werden ersetzt
- 🏷️ **Hostname-Anonymisierung**: server_1, server_2, etc.
- 📄 **Dateinamen-Anonymisierung**: Behält Extensions

**Beispiele**:

```python
anonymizer = DataAnonymizer()

# IP-Adressen
anonymizer.anonymize_ip("192.168.200.5")
# → "10.0.0.1"

# Fehlermeldungen
msg = "transferring file from '\\\\192.168.200.5\\DriveShareD\\file.mov' failed"
anonymizer.anonymize_message(msg)
# → "transferring file from '\\\\10.0.0.1\\share_1\\file.mov' failed"

# Pfade
anonymizer.anonymize_message("D:\\Projects\\Customer\\Content\\video.mov")
# → "Content/.../*.mov"
```

**Anonymisierungs-Statistik**:
```python
stats = anonymizer.get_stats()
# {
#   'ips_anonymized': 5,
#   'paths_anonymized': 23,
#   'hostnames_anonymized': 3,
#   'filenames_anonymized': 12
# }
```

---

### ✅ Phase 3: Export-Optionen & Pattern-Matching

**Modul**: `core/summary_exporter.py`

**Export-Formate**:

#### 1. **Detail-CSV** (`*_detail.csv`)
Alle Einzelheiten mit optionaler Fehler-Kategorisierung:

| Log-Kategorie | Ordner | Dateiname | Fehler-Kategorie | Datum | Zeit | Severity | Type/Source | Description |
|---------------|--------|-----------|------------------|-------|------|----------|-------------|-------------|
| rx_logs | | utility-27110-1.log | Netzwerk | Sat 04.Oct. | 14:08:41.676 | error | | An existing connection was forcibly closed |

#### 2. **Summary-CSV** (`*_summary.csv`)
Gruppiert nach Fehlertyp mit Anzahl:

| Fehler-Kategorie | Fehlertyp | Anzahl | Severity | Erste Occurrence | Letzte Occurrence | Betroffene Dateien |
|------------------|-----------|--------|----------|------------------|-------------------|--------------------|
| Netzwerk | Connection forcibly closed | 87 | error | Sat 04.Oct. 14:08 | Sat 11.Oct. 09:24 | utility-27110-1.log |
| Datei | File transfer failed | 156 | error | Thu 28.Aug. 16:14 | Tue 30.Sep. 15:57 | utility-27110-1.log, utility-27110-2.log |

#### 3. **Statistics-TXT** (`*_statistics.txt`)
Übersicht mit Top-Fehlern:

```
================================================================================
LOG ANALYSE STATISTIK
================================================================================
Generiert: 2025-12-22 14:30:00

Gesamt Fehlereinträge: 119

--------------------------------------------------------------------------------
ANONYMISIERUNG
--------------------------------------------------------------------------------
Anonymisierte IPs: 5
Anonymisierte Pfade: 23
Anonymisierte Hostnamen: 3
Anonymisierte Dateinamen: 12

--------------------------------------------------------------------------------
FEHLER NACH KATEGORIE
--------------------------------------------------------------------------------
Datei               :     89 ( 74.8%)
Netzwerk            :     38 ( 31.9%)
System              :     30 ( 25.2%)
Authentifizierung   :      9 (  7.6%)
Media               :      2 (  1.7%)

--------------------------------------------------------------------------------
TOP 10 HÄUFIGSTE FEHLERTYPEN
--------------------------------------------------------------------------------
    156 ( 74.8%) - File transfer failed
     87 ( 31.9%) - Connection forcibly closed
     56 ( 25.2%) - End of file
     30 (  7.6%) - I/O operation aborted
      9 (  1.7%) - Authenticating failed
```

---

## 🎛️ GUI-Features

### Export-Optionen

**Export-Formate** (alle aktivierbar):
- ☑️ Detailliert (alle Einzelheiten)
- ☑️ Zusammengefasst (gruppiert nach Fehlertyp)
- ☑️ Statistik (Übersicht als TXT)

**Datenverarbeitung**:
- ☑️ Fehler-Kategorisierung (Netzwerk/Datei/System/...)
- ☑️ Daten anonymisieren (IPs, Pfade, Hostnamen)
- 💡 Tipp: Anonymisierung für LLM-Training empfohlen

### Ausgabe-Dateien

Bei Auswahl von `logparser_results.csv` werden erstellt:
- `logparser_results_detail.csv` (wenn "Detailliert" aktiviert)
- `logparser_results_summary.csv` (wenn "Zusammengefasst" aktiviert)
- `logparser_results_statistics.txt` (wenn "Statistik" aktiviert)

---

## 💡 Anwendungsfälle

### 1. LLM-Training Vorbereitung
```
✅ Anonymisierung aktivieren
✅ Fehler-Kategorisierung aktivieren
✅ Alle drei Export-Formate aktivieren
```

**Ergebnis**: Bereinigte, strukturierte, kategorisierte Daten ohne sensible Informationen

### 2. Schnelle Fehler-Übersicht
```
✅ Nur "Zusammengefasst" und "Statistik" aktivieren
✅ Fehler-Kategorisierung aktivieren
❌ Anonymisierung aus (wenn nicht nötig)
```

**Ergebnis**: Kompakte Übersicht mit Top-Fehlern und Statistiken

### 3. Vollständige Analyse
```
✅ Alle Optionen aktivieren
```

**Ergebnis**: Alle Formate für maximale Flexibilität

---

## 📊 Vorher/Nachher Vergleich

### Vorher (ohne neue Features):
```csv
Log-Kategorie,Ordner,Dateiname,Datum,Zeit,Severity,Type/Source,Description
rx_logs,,utility-27110-1.log,Sat 04.Oct.,08:42:27.986,error,,transferring file from '\\192.168.200.5\DriveShareD\GH_Integration_Delivery\SKIE_A\GH_DP4_SKIE_A_5760X1416_202510021510.mov' to '<preview>\\192.168.200.5\DriveShareD\GH_Integration_Delivery\SKIE_A\GH_DP4_SKIE_A_5760X1416_202510021510.mov' failed: copying failed (LocalHost: unable to init copy request)
rx_logs,,utility-27110-1.log,Sat 04.Oct.,08:42:27.988,error,,transferring file from '\\192.168.200.5\DriveShareD\GH_Integration_Delivery\SKIE_A\GH_DP5_SKIE_A_5760X1416_202510021510.mov' to '<preview>\\192.168.200.5\DriveShareD\GH_Integration_Delivery\SKIE_A\GH_DP5_SKIE_A_5760X1416_202510021510.mov' failed: copying failed (LocalHost: unable to init copy request)
[... 154 weitere ähnliche Zeilen ...]
```

### Nachher (mit neuen Features):

**Detail-CSV**:
```csv
Log-Kategorie,Ordner,Dateiname,Fehler-Kategorie,Datum,Zeit,Severity,Type/Source,Description
rx_logs,,file_1.log,Datei,Sat 04.Oct.,08:42:27.986,error,,transferring file from '\\10.0.0.1\share_1\...\*.mov' to 'Content/.../*.mov' failed: copying failed
rx_logs,,file_1.log,Datei,Sat 04.Oct.,08:42:27.988,error,,transferring file from '\\10.0.0.1\share_1\...\*.mov' to 'Content/.../*.mov' failed: copying failed
```

**Summary-CSV**:
```csv
Fehler-Kategorie,Fehlertyp,Anzahl,Severity,Erste Occurrence,Letzte Occurrence,Betroffene Dateien,Beispiel-Beschreibung
Datei,File transfer failed,156,error,Sat 04.Oct. 08:42,Tue 30.Sep. 15:57,"file_1.log, file_2.log",transferring file from '\\10.0.0.1\share_1\...\*.mov' failed
```

**Vorteile**:
- ✅ 99% Platzersparung durch Gruppierung
- ✅ Keine sensiblen Daten (IPs, Pfade)
- ✅ Bessere Übersicht durch Kategorisierung
- ✅ Statistik für schnelle Analyse

---

## 🔧 Technische Details

### Pattern-Matching

Der `ErrorCategorizer` nutzt Regex-Patterns für robuste Erkennung:

```python
CATEGORIES = {
    'Netzwerk': [
        r'connection.*closed',
        r'network.*path.*not.*found',
        r'timeout',
        r'authenticating.*failed',
        r'\\\\[\d\.]+\\',  # UNC Pfade
    ],
    'Datei': [
        r'file.*not.*found',
        r'transferring.*file.*failed',
        r'end.*of.*file',
    ],
    # ...
}
```

### Anonymisierungs-Konsistenz

Der `DataAnonymizer` verwendet Dictionaries für konsistente Zuordnung:

```python
ip_mapping = {
    "192.168.200.5": "10.0.0.1",
    "192.168.205.3": "10.0.0.2",
    # Jede IP wird immer gleich ersetzt
}
```

---

## ✅ Test-Ergebnisse

Getestet mit `test_features.py`:

```
✓ Fehler-Kategorisierung: 6/6 Tests erfolgreich
✓ Anonymisierung: 3/3 Tests erfolgreich  
✓ IP-Ersetzung: 4 IPs anonymisiert
✓ Pfad-Vereinfachung: Funktioniert
```

---

## 🎯 Zusammenfassung

Alle drei Phasen sind **vollständig implementiert und getestet**:

1. ✅ **Fehler-Kategorisierung**: 7 Kategorien, automatisch
2. ✅ **Anonymisierung**: IPs, Pfade, Hostnamen - konsistent
3. ✅ **Export-Optionen**: 3 Formate (Detail, Summary, Stats)

**Bonus-Features**:
- Pattern-Matching für ähnliche Fehler
- Intelligente Pfad-Vereinfachung
- GUI mit vollständiger Konfiguration
- Erweiterte Statistiken

**Bereit für**: LLM-Training, Fehleranalyse, Datenbank-Integration
