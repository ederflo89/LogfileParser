# LogfileParser

Ein Tool zum automatischen Parsen und Analysieren von Logdateien. Durchsucht rekursiv Verzeichnisse nach Logfiles und extrahiert Fehlereinträge in eine CSV-Datei.

## Features

- ✅ **Zwei Parser-Modi:**
  - **AV Stumpfl Format**: Strukturiertes Parsing mit Datum, Zeit, Severity, Type/Source und Description
  - **Generischer Modus**: Einfache Keyword-Suche (error, warning, fatal, critical)
- ✅ Rekursives Durchsuchen von Verzeichnissen und Unterverzeichnissen
- ✅ Unterstützung für .txt und .log Dateien
- ✅ Unterstützung für gezippte Archive (.zip)
- ✅ Intelligente Duplikatserkennung
- ✅ Export in CSV-Format
- ✅ GUI mit Echtzeit-Fortschrittsanzeige
- ✅ Multi-Directory Support

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
2. **Verzeichnisse hinzufügen**: Klicke auf "Verzeichnis hinzufügen" und wähle die Ordner aus
3. **Ausgabedatei wählen**: Optional - ändere den Pfad der CSV-Ausgabedatei
4. **Parsing starten**: Klicke auf "Parsing starten"
5. **Fortschritt beobachten**: Verfolge den Fortschritt im Log-Bereich
6. **Ergebnisse öffnen**: Nach Abschluss wird die CSV-Datei gespeichert

### CSV-Format

**AV Stumpfl Modus:**

| Logfilename | Datum | Zeit | Severity | Type/Source | Description |
|------------|-------|------|----------|-------------|-------------|
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
