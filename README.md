# LogfileParser

Ein leistungsstarkes Tool zum automatischen Parsen, Analysieren und Anonymisieren von Logdateien. Optimiert für die Extraktion von Fehlerinformationen und Aufbereitung für LLM-Training.

## 🎯 Hauptzweck

Dieses Tool dient zur Vorbereitung großer Logfile-Bestände für:
- **LLM-Training**: Anonymisierte, strukturierte Fehlerdaten
- **Fehleranalyse**: Kategorisierte und gruppierte Fehler
- **Datenbank-Integration**: Bereitet Daten für weitere Analyse-Tools auf

## Features

### Parser-Modi
- ✅ **AV Stumpfl Format**: Strukturiertes Parsing mit Datum, Zeit, Severity, Type/Source und Description
  - Unterstützt 3 verschiedene Log-Formate (DD.MM.YYYY, YYYY-MM-DD, Day DD.Mon.)
  - Multi-Line Support für Stacktraces
- ✅ **Generischer Modus**: Einfache Keyword-Suche (error, warning, fatal, critical)

### Export-Formate
- 📄 **Detailliert**: Alle Einzelheiten mit optionaler Fehler-Kategorisierung
- 📊 **Zusammengefasst**: Gruppiert nach Fehlertyp mit Anzahl und Zeiträumen
- 📈 **Statistik**: Übersicht mit Top-Fehlern und Verteilungen

### Datenverarbeitung
- 🔍 **Fehler-Kategorisierung**: Automatische Einteilung in Netzwerk, Datei, System, Auth, Media, etc.
- 🔒 **Anonymisierung**: Ersetzt IPs, Pfade, Hostnamen für DSGVO-konforme LLM-Nutzung
- 🎯 **Intelligente Duplikatserkennung**: Verhindert redundante Einträge
- 📁 **Multi-Format Support**: .txt, .log, .zip Archive

### Benutzeroberfläche
- 🖥️ **Moderne GUI**: Tkinter-basiert mit Echtzeit-Fortschritt
- 📊 **Live-Statistiken**: Zeigt eindeutige Fehler und übersprungene Duplikate
- 🎛️ **Flexible Optionen**: Anpassbare Export- und Verarbeitungseinstellungen

## AV Stumpfl Log-Format

Das Tool erkennt automatisch das AV Stumpfl Logfile-Format:

```
DD.MM.YYYY HH:MM:SS [TAB] SEVERITY [TAB] Type/Source
[TAB] Description (kann mehrzeilig sein)
```

**Severity-Codes:**
- `V` = Verbose (wird übersprungen)
- `I` = Info (wird übersprungen)
- `E` = Error/Event
- `W` = Warning
- `F` = Fatal
- `C` = Critical

## Installation

### Voraussetzungen
- Python 3.8 oder höher

### Setup

1. Repository klonen oder herunterladen
2. Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

## Verwendung

### Programm starten

```bash
python main.py
```

### Workflow

1. **Parser-Modus wählen**: 
   - AV Stumpfl Format für strukturierte Logs
   - Generischer Modus für einfache Keyword-Suche

2. **Export-Optionen konfigurieren**:
   - **Export-Formate**: Detailliert, Zusammengefasst, Statistik
   - **Fehler-Kategorisierung**: Aktiviert automatische Klassifizierung
   - **Anonymisierung**: Empfohlen für LLM-Training

3. **Verzeichne

**Detail-CSV** (mit Fehler-Kategorisierung):

| Log-Kategorie | Ordner | Dateiname | Fehler-Kategorie | Datum | Zeit | Severity | Type/Source | Description |
|---------------|--------|-----------|------------------|-------|------|----------|-------------|-------------|
| rx_logs | | file_1.log | Netzwerk | 04.Oct. | 18:50:29 | error | | Connection closed |

**Summary-CSV** (Zusammengefasst):

| Fehler-Kategorie | Fehlertyp | Anzahl | Severity | Erste Occurrence | Letzte Occurrence | Betroffene Dateien | Beispiel-Beschreibung |
|------------------|-----------|--------|----------|------------------|-------------------|--------------------|----------------------|
| Netzwerk | Connection closed | 87 | error | Sat 04.Oct. | Sat 11.Oct. | file_1.log, file_2.log | Connection forcibly closed by remote host |

**Statistics-TXT**: 
```
=================================================================================
LOG ANALYSE STATISTIK
=================================================================================
Generiert: 2025-12-22 14:30:00

Gesamt Fehlereinträge: 119

ANONYMISIERUNG
---------------------------------------------------------------------------------
Anonymisierte IPs: 5
Anonymisierte Pfade: 23
Anonymisierte Hostnamen: 3
Anonymisierte Dateinamen: 12

FEHLER NACH KATEGORIE
---------------------------------------------------------------------------------
Datei               :    89 ( 74.8%)
Netzwerk            :    38 ( 31.9%) (3 Formate)
│   ├── avstumpfl_exporter.py   # AV Stumpfl CSV-Export
│   ├── error_categorizer.py    # Fehler-Kategorisierung (NEU)
│   ├── anonymizer.py           # Daten-Anonymisierung (NEU)
│   └── summary_exporter.py     # Zusammenfassung & Statistik (NEU)
└── gui/
    ├── __init__.py
    └── main_window.py          # GUI-Interface
```

## 🔒 Anonymisierung für LLM-Training

Das Tool anonymisiert automatisch:
- **IP-Adressen**: `192.168.200.5` → `10.0.0.1`
- **Netzwerkpfade**: `\\server\share\path` → `\\server_1\share_1\...`
- **Dateipfade**: `D:\Projects\Customer\...` → `Projects/.../*.ext`
- **Hostnamen**: `server.domain.com` → `server_1`

Die Anonymisierung ist **konsistent** - dieselbe IP wird immer gleich ersetzt.

## 📊 Fehler-Kategorien

Automatische Klassifizierung in:
- **Netzwerk**: Connection errors, timeouts, network paths
- **Datei**: File not found, file transfer, permissions
- **System**: I/O errors, memory errors, threads
- **Authentifizierung**: Login failed, access denied
- **Media**: Encoding/decoding errors, codec errors
- **Modul**: Module loading, linking errors
- **Zeitbezogen**: System time, timestamps
- **Sonstige**: Nicht kategorisierbare Fehler

## 💡 Best Practices für LLM-Training

1. ✅ **Anonymisierung aktivieren**: Schützt sensible Daten
2. ✅ **Fehler-Kategorisierung nutzen**: Strukturiert Trainingsdaten
3. ✅ **Summary-Export**: Reduziert Redundanz
4. ✅ **Mehrere Quellen**: Diverse Logfiles erhöhen Datenqualität

## Lizenz

Intern - AV Stumpfl GmbH----------|-------|------|----------|-------------|-------------|
| path/to/log.log | 08.06.2022 | 14:10:00 | warning | Module.Class | Fehlerbeschreibung |

**Generischer Modus:**

| Logfilename | Severity | Eintragstext |
|------------|----------|--------------|
| path/to/log.txt | error | Vollständiger Fehlertext aus dem Log |

## Projektstruktur

```
LogfileParser/
├── main.py                      # Einstiegspunkt
├── requirements.txt             # Python-Abhängigkeiten
├── core/
│   ├── __init__.py
│   ├── log_parser.py           # Generischer Parser
│   ├── csv_exporter.py         # Generischer CSV-Export
│   ├── avstumpfl_parser.py     # AV Stumpfl Parser
│   └── avstumpfl_exporter.py   # AV Stumpfl CSV-Export
└── gui/
    ├── __init__.py
    └── main_window.py          # GUI-Interface
```
