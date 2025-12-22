# LogfileParser

Ein Tool zum automatischen Parsen und Analysieren von Logdateien. Durchsucht rekursiv Verzeichnisse nach .txt Logfiles und extrahiert Fehlereinträge (Error, Fatal, Critical, Warning) in eine CSV-Datei.

## Features

- ✅ Rekursives Durchsuchen von Verzeichnissen und Unterverzeichnissen
- ✅ Unterstützung für .txt Logfiles
- ✅ Unterstützung für gezippte Archive (.zip)
- ✅ Erkennung von Fehlertypen: Error, Fatal, Critical, Warning
- ✅ Export in CSV-Format (Logfilename, Severity, Eintragstext)
- ✅ GUI mit Echtzeit-Fortschrittsanzeige
- ✅ Multi-Directory Support

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

1. **Verzeichnisse hinzufügen**: Klicke auf "Verzeichnis hinzufügen" und wähle die Ordner aus, die durchsucht werden sollen
2. **Ausgabedatei wählen**: Optional - ändere den Pfad der CSV-Ausgabedatei
3. **Parsing starten**: Klicke auf "Parsing starten"
4. **Fortschritt beobachten**: Verfolge den Fortschritt im Log-Bereich
5. **Ergebnisse öffnen**: Nach Abschluss wird die CSV-Datei am angegebenen Speicherort gespeichert

### CSV-Format

Die generierte CSV-Datei enthält folgende Spalten:

| Logfilename | Severity | Eintragstext |
|------------|----------|--------------|
| path/to/log.txt | error | Vollständiger Fehlertext aus dem Log |
| path/to/log.txt | critical | Vollständiger Fehlertext aus dem Log |

## Projektstruktur

```
LogfileParser/
├── main.py                 # Einstiegspunkt
├── requirements.txt        # Python-Abhängigkeiten
├── core/
│   ├── __init__.py
│   ├── log_parser.py      # Log-Parsing-Logik
│   └── csv_exporter.py    # CSV-Export
└── gui/
    ├── __init__.py
    └── main_window.py     # GUI-Interface
```

## Entwicklung

### Erweitern der Severity-Level

In `core/log_parser.py` können weitere Severity-Level hinzugefügt werden:

```python
SEVERITY_LEVELS = ['error', 'fatal', 'critical', 'warning', 'debug']
```

### Weitere Dateiformate

Die Klasse `LogParser` kann erweitert werden um weitere Dateiformate zu unterstützen.
