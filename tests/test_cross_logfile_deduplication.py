"""
Test: Cross-Logfile Deduplication
Testet, dass der gleiche Fehler in verschiedenen Logfiles separat erfasst wird
"""
import unittest
import tempfile
import shutil
import sys
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.avstumpfl_parser import AVStumpflLogParser


class TestCrossLogfileDeduplication(unittest.TestCase):
    def setUp(self):
        """Erstelle temporäre Test-Umgebung"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Räume temporäre Test-Umgebung auf"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_same_error_different_logfiles_creates_separate_entries(self):
        """
        Test: Gleicher Fehler in rx-log und pixera-log muss 2 separate Einträge erzeugen
        """
        # Erstelle rx-log mit Fehler (Format 2: YYYY-MM-DD HH:MM:SS.mmm [LEVEL] Message)
        rx_log = Path(self.test_dir) / "rx-log.txt"
        rx_log.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Erstelle pixera-log mit GLEICHEM Fehler
        pixera_log = Path(self.test_dir) / "pixera-log.txt"
        pixera_log.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Parse beide Logfiles
        parser = AVStumpflLogParser()
        entries = parser.parse_directory(self.test_dir)
        
        # Erwarte 2 separate Einträge (einer für rx-log, einer für pixera-log)
        self.assertEqual(len(entries), 2, 
                        "Gleicher Fehler in verschiedenen Logfiles muss 2 Einträge erzeugen")
        
        # Tuple-Format: (source_name, date, time, severity_name, log_type, description)
        # Index 0 = source_name, Index 4 = log_type, Index 5 = description
        
        # Prüfe dass beide Einträge unterschiedliche source_name haben
        sources = [entry[0] for entry in entries]
        self.assertIn(str(rx_log), sources)
        self.assertIn(str(pixera_log), sources)
        
        # Beide sollten denselben Type und Description haben
        self.assertEqual(entries[0][4], entries[1][4])  # log_type
        self.assertEqual(entries[0][5], entries[1][5])  # description
    
    def test_same_error_same_logfile_with_split_suffix_deduplicates(self):
        """
        Test: Gleicher Fehler in playback-27103-1.log und playback-27103-2.log muss zu 1 Eintrag führen
        (weil beide zu playback-27103.log normalisiert werden)
        """
        # Erstelle playback-27103-1.log mit Fehler
        log1 = Path(self.test_dir) / "playback-27103-1.log"
        log1.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Erstelle playback-27103-2.log mit GLEICHEM Fehler
        log2 = Path(self.test_dir) / "playback-27103-2.log"
        log2.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Parse beide Logfiles
        parser = AVStumpflLogParser()
        entries = parser.parse_directory(self.test_dir)
        
        # Erwarte NUR 1 Eintrag (weil beide zu playback-27103.log normalisiert werden)
        self.assertEqual(len(entries), 1, 
                        "Gleicher Fehler in Split-Logfiles (z.B. -1, -2) muss dedupliziert werden")
        
        # Tuple-Format: (source_name, date, time, severity_name, log_type, description)
        # Der Eintrag kann von einem der beiden Logfiles stammen
        source = entries[0][0]  # source_name ist Index 0
        self.assertTrue(source in [str(log1), str(log2)])
    
    def test_different_errors_different_logfiles_creates_separate_entries(self):
        """
        Test: Verschiedene Fehler in verschiedenen Logfiles müssen separate Einträge erzeugen
        """
        # Erstelle rx-log mit Fehler A
        rx_log = Path(self.test_dir) / "rx-log.txt"
        rx_log.write_text("""2024-01-15 10:23:45.123 [ERROR] Network timeout
Connection failed
""", encoding='utf-8')
        
        # Erstelle pixera-log mit Fehler B
        pixera_log = Path(self.test_dir) / "pixera-log.txt"
        pixera_log.write_text("""2024-01-15 10:23:45.123 [ERROR] File not found
Missing resource
""", encoding='utf-8')
        
        # Parse beide Logfiles
        parser = AVStumpflLogParser()
        entries = parser.parse_directory(self.test_dir)
        
        # Erwarte 2 separate Einträge (unterschiedliche Fehler)
        self.assertEqual(len(entries), 2, 
                        "Verschiedene Fehler in verschiedenen Logfiles müssen separate Einträge erzeugen")
        
        # Tuple-Format: (source_name, date, time, severity_name, log_type, description)
        # Index 4 = log_type
        types = [entry[4] for entry in entries]
        self.assertIn('Network timeout', types)
        self.assertIn('File not found', types)
    
    def test_normalization_removes_writeable_suffix(self):
        """
        Test: -WRITEABLE Suffix wird korrekt normalisiert
        """
        # Erstelle playback-27103-WRITEABLE.log
        log1 = Path(self.test_dir) / "playback-27103-WRITEABLE.log"
        log1.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Erstelle playback-27103.log mit GLEICHEM Fehler
        log2 = Path(self.test_dir) / "playback-27103.log"
        log2.write_text("""2024-01-15 10:23:45.123 [ERROR] End of file
Error reading data stream
""", encoding='utf-8')
        
        # Parse beide Logfiles
        parser = AVStumpflLogParser()
        entries = parser.parse_directory(self.test_dir)
        
        # Erwarte NUR 1 Eintrag (weil -WRITEABLE normalisiert wird)
        self.assertEqual(len(entries), 1, 
                        "-WRITEABLE Suffix muss normalisiert werden")


if __name__ == '__main__':
    unittest.main()
