"""
LogfileParser - Main Entry Point
Analysiert Logfiles und extrahiert Fehler in CSV-Format
"""

from gui.main_window import LogParserApp

if __name__ == "__main__":
    app = LogParserApp()
    app.run()
