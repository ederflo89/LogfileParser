"""
Main Window - GUI für den LogfileParser
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from datetime import datetime
import zipfile
import tempfile
import shutil
from core import LogParser, CSVExporter
from core.avstumpfl_parser import AVStumpflLogParser
from core.avstumpfl_exporter import AVStumpflCSVExporter
from core.anonymizer import DataAnonymizer
from core.summary_exporter import SummaryExporter


class LogParserApp:
    """Hauptfenster der LogfileParser-Anwendung"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LogfileParser")
        self.root.geometry("950x850")  # Erhöht damit alle Buttons sichtbar sind
        self.root.minsize(950, 850)  # Minimum-Größe festlegen
        
        self.directories = []
        self.is_parsing = False
        self.parser = None
        self.parser_mode = tk.StringVar(value="avstumpfl")  # Default: AV Stumpfl Format
        self.temp_dirs = []  # Temporäre Verzeichnisse für extrahierte ZIP-Dateien
        self.custom_temp_dir = None  # Benutzerdefinierter Temp-Ordner für ZIP-Extraktion
        
        # Cleanup alter temp-Verzeichnisse beim Start
        self._cleanup_old_temp_dirs()
        
        # Export-Optionen
        self.export_detailed = tk.BooleanVar(value=True)
        self.export_summary = tk.BooleanVar(value=True)
        self.export_statistics = tk.BooleanVar(value=True)
        self.anonymize_data = tk.BooleanVar(value=False)
        self.add_error_category = tk.BooleanVar(value=True)
        
        # Datenbank-Modus für persistente Fehlersammlung
        self.use_database_mode = tk.BooleanVar(value=False)
        self.database_file = None  # Pfad zur Datenbank-CSV
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="LogfileParser",
            font=('Arial', 16, 'bold')
        ).pack(side=tk.LEFT)
        
        # Parser-Modus Auswahl
        mode_frame = ttk.LabelFrame(self.root, text="Parser-Modus", padding="10")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="AV Stumpfl Format (Strukturiertes Log mit Datum/Zeit/Severity/Type/Description)",
            variable=self.parser_mode,
            value="avstumpfl"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="Generischer Modus (Einfache Keyword-Suche: error, warning, fatal, critical)",
            variable=self.parser_mode,
            value="generic"
        ).pack(anchor=tk.W, pady=2)
        
        # Verzeichnis-Auswahl Bereich
        dir_frame = ttk.LabelFrame(self.root, text="Verzeichnisse", padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Listbox für Verzeichnisse
        list_frame = ttk.Frame(dir_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.dir_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=4
        )
        self.dir_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.dir_listbox.yview)
        
        # Buttons für Verzeichnisverwaltung
        btn_frame = ttk.Frame(dir_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            btn_frame,
            text="Verzeichnis hinzufügen",
            command=self._add_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Datei hinzufügen",
            command=self._add_file
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Entfernen",
            command=self._remove_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Liste leeren",
            command=self._clear_directories
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Cache leeren",
            command=self._manual_cache_cleanup
        ).pack(side=tk.LEFT, padx=2)
        
        # Export-Optionen Bereich
        export_options_frame = ttk.LabelFrame(self.root, text="Export-Optionen", padding="10")
        export_options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Linke Spalte - Export-Typen
        left_col = ttk.Frame(export_options_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_col, text="Export-Formate:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Checkbutton(
            left_col,
            text="Detailliert (alle Einzelheiten)",
            variable=self.export_detailed
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            left_col,
            text="Zusammengefasst (gruppiert nach Fehlertyp)",
            variable=self.export_summary
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            left_col,
            text="Statistik (Übersicht als TXT)",
            variable=self.export_statistics
        ).pack(anchor=tk.W, pady=2)
        
        # Rechte Spalte - Verarbeitungsoptionen
        right_col = ttk.Frame(export_options_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_col, text="Datenverarbeitung:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Checkbutton(
            right_col,
            text="Fehler-Kategorisierung (Netzwerk/Datei/System/...)",
            variable=self.add_error_category
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            right_col,
            text="Daten anonymisieren (IPs, Pfade, Hostnamen)",
            variable=self.anonymize_data
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Label(
            right_col,
            text="💡 Tipp: Anonymisierung für LLM-Training empfohlen",
            font=('Arial', 8),
            foreground='gray'
        ).pack(anchor=tk.W, padx=20)
        
        # Datenbank-Modus
        db_mode_frame = ttk.LabelFrame(self.root, text="Persistente Fehler-Datenbank", padding="10")
        db_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(
            db_mode_frame,
            text="📊 Datenbank-Modus: An bestehende CSV anhängen statt neue zu erstellen",
            variable=self.use_database_mode,
            command=self._toggle_database_mode
        ).pack(anchor=tk.W, pady=2)
        
        # Datenbank-Datei Anzeige
        db_file_frame = ttk.Frame(db_mode_frame)
        db_file_frame.pack(fill=tk.X, pady=5)
        
        self.db_file_var = tk.StringVar(value="Keine Datenbank geladen")
        db_entry = ttk.Entry(
            db_file_frame,
            textvariable=self.db_file_var,
            state='readonly'
        )
        db_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.db_load_btn = ttk.Button(
            db_file_frame,
            text="Datenbank laden",
            command=self._load_database,
            state='disabled'
        )
        self.db_load_btn.pack(side=tk.LEFT, padx=2)
        
        self.db_new_btn = ttk.Button(
            db_file_frame,
            text="Neue erstellen",
            command=self._create_new_database,
            state='disabled'
        )
        self.db_new_btn.pack(side=tk.LEFT, padx=2)
        
        # Info-Label für Datenbank-Statistik
        self.db_stats_label = ttk.Label(
            db_mode_frame,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.db_stats_label.pack(anchor=tk.W, padx=5)
        
        ttk.Label(
            db_mode_frame,
            text="💡 Datenbank-Modus: Sammelt Fehler über mehrere Sessions hinweg. Neue Scans erweitern die bestehende Datenbank.",
            font=('Arial', 8),
            foreground='gray',
            wraplength=900
        ).pack(anchor=tk.W, padx=20, pady=(5, 0))
        
        # Temp-Ordner Konfiguration
        temp_config_frame = ttk.LabelFrame(self.root, text="ZIP-Extraktion Temp-Ordner", padding="10")
        temp_config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Info-Label
        ttk.Label(
            temp_config_frame,
            text="Wähle ein Laufwerk mit ausreichend Speicherplatz für temporäre ZIP-Extraktion:",
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Temp-Pfad Anzeige und Auswahl
        temp_path_frame = ttk.Frame(temp_config_frame)
        temp_path_frame.pack(fill=tk.X, pady=2)
        
        self.temp_dir_var = tk.StringVar(value="Standard (System-Temp)")
        temp_entry = ttk.Entry(
            temp_path_frame,
            textvariable=self.temp_dir_var,
            state='readonly'
        )
        temp_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Button(
            temp_path_frame,
            text="Durchsuchen...",
            command=self._select_temp_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            temp_path_frame,
            text="Zurücksetzen",
            command=self._reset_temp_directory
        ).pack(side=tk.LEFT, padx=2)
        
        # Info über verfügbaren Speicherplatz
        self.temp_space_label = ttk.Label(
            temp_config_frame,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.temp_space_label.pack(anchor=tk.W, padx=5)
        self._update_temp_space_info()
        
        # Ausgabe-Datei Bereich
        output_frame = ttk.LabelFrame(self.root, text="Ausgabe-Datei", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        output_inner = ttk.Frame(output_frame)
        output_inner.pack(fill=tk.X)
        
        self.output_path_var = tk.StringVar()
        # Verwende sicheres Verzeichnis: Desktop oder Dokumente, nicht System32
        safe_dir = Path.home() / "Desktop"
        if not safe_dir.exists():
            safe_dir = Path.home() / "Documents"
        if not safe_dir.exists():
            safe_dir = Path(__file__).parent.parent  # Programmverzeichnis als Fallback
        
        default_output = str(safe_dir / f"logparser_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        self.output_path_var.set(default_output)
        
        ttk.Entry(
            output_inner,
            textvariable=self.output_path_var,
            state='readonly'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            output_inner,
            text="Durchsuchen...",
            command=self._select_output_file
        ).pack(side=tk.RIGHT)
        
        # Fortschritts-Bereich
        progress_frame = ttk.LabelFrame(self.root, text="Fortschritt", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Aktueller Status
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Bereit")
        ttk.Label(
            status_frame,
            textvariable=self.status_var,
            font=('Arial', 9, 'bold')
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Fortschrittsbalken
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, pady=(0, 5))
        
        # Log-Ausgabe
        log_frame = ttk.Frame(progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_frame,
            height=15,
            yscrollcommand=log_scroll.set,
            state='disabled',
            wrap=tk.WORD
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Statistik-Bereich
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.stats_var = tk.StringVar(value="Eindeutige Fehler: 0 | Duplikate übersprungen: 0")
        ttk.Label(
            stats_frame,
            textvariable=self.stats_var,
            font=('Arial', 10, 'bold')
        ).pack(side=tk.LEFT)
        
        # Control Buttons
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="Parsing starten",
            command=self._start_parsing,
            style='Accent.TButton'
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="Abbrechen",
            command=self._stop_parsing,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Log leeren",
            command=self._clear_log
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Beenden",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=2)
    
    def _add_directory(self):
        """Fügt ein Verzeichnis zur Liste hinzu und findet automatisch alle ZIP-Dateien darin"""
        directory = filedialog.askdirectory(title="Verzeichnis auswählen")
        if not directory:
            return
            
        directory_path = Path(directory)
        
        # Füge Hauptverzeichnis hinzu
        if directory not in self.directories:
            self.directories.append(directory)
            self.dir_listbox.insert(tk.END, directory)
            self._log(f"Verzeichnis hinzugefügt: {directory}")
        
        # Suche rekursiv nach ZIP-Dateien
        zip_files = list(directory_path.rglob("*.zip"))
        if zip_files:
            self._log(f"Gefundene ZIP-Dateien: {len(zip_files)}")
            # Zeige Progress-Dialog und extrahiere ZIPs
            self._extract_zip_files_with_progress(zip_files)
        else:
            self._log("Keine ZIP-Dateien im Verzeichnis gefunden")
    
    def _add_file(self):
        """Fügt eine einzelne Datei hinzu (automatische Erkennung ob ZIP)"""
        file_path = filedialog.askopenfilename(
            title="Datei auswählen",
            filetypes=[
                ("Alle unterstützten Dateien", "*.zip;*.log;*.txt"),
                ("ZIP-Archive", "*.zip"),
                ("Log-Dateien", "*.log;*.txt"),
                ("Alle Dateien", "*.*")
            ]
        )
        if not file_path:
            return
        
        file_path_obj = Path(file_path)
        
        # Prüfe ob ZIP-Datei (robuste Erkennung)
        is_zip = file_path_obj.suffix.lower() == '.zip' or zipfile.is_zipfile(file_path)
        
        if is_zip:
            self._log(f"ZIP-Datei erkannt: {file_path_obj.name}")
            # Zeige Progress-Dialog für einzelne ZIP
            self._extract_zip_files_with_progress([Path(file_path)])
        else:
            self._log(f"Log-Datei erkannt: {file_path_obj.name}")
            # Füge Verzeichnis der Datei hinzu (damit die Datei geparst wird)
            parent_dir = str(file_path_obj.parent)
            if parent_dir not in self.directories:
                self.directories.append(parent_dir)
                self.dir_listbox.insert(tk.END, f"📄 {file_path_obj.name} → {parent_dir}")
                self._log(f"Datei hinzugefügt: {file_path_obj.name}")
    
    def _extract_zip_files_with_progress(self, zip_files: list):
        """Extrahiert mehrere ZIP-Dateien mit Fortschrittsanzeige"""
        # Erstelle Progress-Dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("ZIP-Dateien extrahieren")
        progress_dialog.geometry("600x200")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # Verhindere Schließen während Extrahierung
        extraction_complete = threading.Event()
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Status-Label
        status_label = ttk.Label(
            progress_dialog,
            text=f"Extrahiere 0 von {len(zip_files)} ZIP-Dateien...",
            font=('Arial', 10, 'bold')
        )
        status_label.pack(pady=(20, 10))
        
        # Aktueller Dateiname
        file_label = ttk.Label(
            progress_dialog,
            text="Vorbereitung...",
            font=('Arial', 9),
            wraplength=550
        )
        file_label.pack(pady=5)
        
        # Fortschrittsbalken
        progress_bar = ttk.Progressbar(
            progress_dialog,
            mode='determinate',
            length=550,
            maximum=len(zip_files)
        )
        progress_bar.pack(pady=10)
        
        # Detail-Label
        detail_label = ttk.Label(
            progress_dialog,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        detail_label.pack(pady=5)
        
        # Extrahiere ZIPs in Thread
        def extract_worker():
            for idx, zip_file in enumerate(zip_files, 1):
                try:
                    zip_path_obj = Path(zip_file)
                    
                    # Update UI
                    self.root.after(0, lambda i=idx, name=zip_path_obj.name: (
                        status_label.config(text=f"Extrahiere {i} von {len(zip_files)} ZIP-Dateien..."),
                        file_label.config(text=f"📦 {name}"),
                        progress_bar.config(value=i-1)
                    ))
                    
                    # Erstelle temporäres Verzeichnis
                    temp_dir = self._create_temp_dir()
                    self.temp_dirs.append(temp_dir)
                    
                    # Extrahiere ZIP
                    self.root.after(0, lambda: self._log(f"Extrahiere ZIP: {zip_path_obj.name}"))
                    with zipfile.ZipFile(str(zip_file), 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Zähle extrahierte Dateien
                    all_files = list(Path(temp_dir).rglob('*'))
                    log_files = [f for f in all_files if f.suffix.lower() in ['.log', '.txt']]
                    
                    # Füge zur Liste hinzu
                    self.directories.append(temp_dir)
                    display_name = f"📦 {zip_path_obj.name} ({len(log_files)} Logs)"
                    self.root.after(0, lambda dn=display_name: self.dir_listbox.insert(tk.END, dn))
                    self.root.after(0, lambda lf=len(log_files), af=len(all_files): 
                                  self._log(f"  └─ Extrahiert: {lf} Log-Dateien, {af} Dateien gesamt"))
                    
                    # Update Details
                    self.root.after(0, lambda lf=len(log_files): 
                                  detail_label.config(text=f"✓ {lf} Log-Dateien gefunden"))
                    
                except Exception as e:
                    error_msg = f"FEHLER beim Extrahieren von {Path(zip_file).name}: {str(e)}"
                    self.root.after(0, lambda msg=error_msg: self._log(msg))
                    self.root.after(0, lambda: detail_label.config(text="✗ Fehler beim Extrahieren", foreground='red'))
            
            # Markiere Extrahierung als abgeschlossen
            extraction_complete.set()
            
            # Schließe Dialog nach Abschluss
            self.root.after(0, progress_dialog.destroy)
            self.root.after(100, lambda: self._log(f"✓ {len(zip_files)} ZIP-Dateien erfolgreich extrahiert"))
        
        # Starte Thread (NICHT als daemon, damit er zu Ende läuft)
        thread = threading.Thread(target=extract_worker, daemon=False)
        thread.start()
        
        # Warte auf Abschluss der Extrahierung (mit Timeout)
        def wait_for_extraction():
            if extraction_complete.wait(timeout=0.1):
                # Extrahierung abgeschlossen
                return
            else:
                # Noch nicht fertig, prüfe erneut
                self.root.after(100, wait_for_extraction)
        
        wait_for_extraction()
    
    def _add_zip_file(self, zip_path: str):
        """Extrahiert ZIP-Datei in temporäres Verzeichnis"""
        try:
            zip_path_obj = Path(zip_path)
            
            # Erstelle temporäres Verzeichnis
            temp_dir = self._create_temp_dir()
            self.temp_dirs.append(temp_dir)
            
            # Extrahiere ZIP
            self._log(f"Extrahiere ZIP: {zip_path_obj.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Zähle extrahierte Dateien
            all_files = list(Path(temp_dir).rglob('*'))
            log_files = [f for f in all_files if f.suffix.lower() in ['.log', '.txt']]
            
            # Füge temporäres Verzeichnis zur Liste hinzu
            self.directories.append(temp_dir)
            display_name = f"📦 {zip_path_obj.name} ({len(log_files)} Logs)"
            self.dir_listbox.insert(tk.END, display_name)
            self._log(f"  └─ Extrahiert: {len(log_files)} Log-Dateien, {len(all_files)} Dateien gesamt")
            
        except Exception as e:
            messagebox.showerror("Fehler", f"ZIP-Datei konnte nicht extrahiert werden:\n{str(e)}")
            self._log(f"FEHLER beim Extrahieren von {Path(zip_path).name}: {str(e)}")
    
    def _remove_directory(self):
        """Entfernt das ausgewählte Verzeichnis"""
        selection = self.dir_listbox.curselection()
        if selection:
            index = selection[0]
            directory = self.directories[index]
            self.directories.pop(index)
            self.dir_listbox.delete(index)
            
            # Wenn es ein temp-Verzeichnis ist, cleanup durchführen
            if directory in self.temp_dirs:
                self.temp_dirs.remove(directory)
                try:
                    if Path(directory).exists():
                        shutil.rmtree(directory)
                        self._log(f"Temporäres Verzeichnis gelöscht: {directory}")
                except Exception as e:
                    self._log(f"Warnung: Konnte temporäres Verzeichnis nicht löschen: {e}")
            
            self._log(f"Verzeichnis entfernt: {directory}")
    
    def _clear_directories(self):
        """Leert die Verzeichnisliste"""
        self._cleanup_temp_dirs()
        self.directories.clear()
        self.dir_listbox.delete(0, tk.END)
        self._log("Verzeichnisliste geleert")
    
    def _select_output_file(self):
        """Wählt die Ausgabe-CSV-Datei"""
        filename = filedialog.asksaveasfilename(
            title="Ausgabedatei wählen",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_path_var.set(filename)
    
    def _log(self, message: str):
        """Fügt eine Nachricht zum Log hinzu"""
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def _clear_log(self):
        """Leert das Log"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
    
    def _update_progress(self, message: str):
        """Callback für Fortschrittsmeldungen vom Parser"""
        self.root.after(0, lambda: self._log(message))
    
    def _start_parsing(self):
        """Startet den Parsing-Prozess"""
        if not self.directories:
            messagebox.showwarning(
                "Keine Verzeichnisse",
                "Bitte fügen Sie mindestens ein Verzeichnis hinzu."
            )
            return
        
        # DATENBANK-MODUS: Validierung
        if self.use_database_mode.get():
            if not self.database_file:
                messagebox.showwarning(
                    "Keine Datenbank",
                    "Bitte laden Sie eine bestehende Datenbank oder erstellen Sie eine neue."
                )
                return
            
            if not Path(self.database_file).exists():
                result = messagebox.askyesno(
                    "Datenbank nicht gefunden",
                    f"Die Datenbank-Datei wurde nicht gefunden:\\n{self.database_file}\\n\\n"
                    f"Möchten Sie eine neue Datenbank erstellen?"
                )
                if result:
                    self._create_new_database()
                    if not self.database_file:
                        return
                else:
                    return
        
        # NORMALER MODUS: Output-Pfad Validierung
        else:
            output_path = self.output_path_var.get()
            if not output_path:
                messagebox.showwarning(
                    "Keine Ausgabedatei",
                    "Bitte wählen Sie eine Ausgabedatei."
                )
                return
            
            # Validiere Ausgabeverzeichnis
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                messagebox.showerror(
                    "Ungültiger Pfad",
                    f"Das Verzeichnis existiert nicht:\\n{output_dir}"
                )
                return
            
            # Prüfe ob Verzeichnis beschreibbar ist
            try:
                test_file = output_dir / ".logparser_write_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                messagebox.showerror(
                    "Keine Schreibberechtigung",
                    f"Keine Schreibberechtigung für:\\n{output_dir}\\n\\n"
                    f"Bitte wählen Sie einen anderen Speicherort (z.B. Desktop oder Dokumente).\\n\\n"
                    f"Fehler: {str(e)}"
                )
                return
        
        self.is_parsing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("Parsing läuft...")
        self.progress.start()
        
        self._log("=" * 50)
        self._log("Parsing gestartet")
        self._log(f"Verzeichnisse: {len(self.directories)}")
        
        # Starte Parsing in separatem Thread
        thread = threading.Thread(target=self._parse_thread, args=(output_path,))
        thread.daemon = True
        thread.start()
    
    def _parse_thread(self, output_path: str):
        """Thread-Funktion für das Parsing"""
        try:
            all_results = []
            mode = self.parser_mode.get()
            
            # Erstelle Anonymizer wenn aktiviert
            anonymizer = DataAnonymizer() if self.anonymize_data.get() else None
            
            self._log(f"Parser-Modus: {'AV Stumpfl Format' if mode == 'avstumpfl' else 'Generischer Modus'}")
            if anonymizer:
                self._log("Anonymisierung aktiviert (für LLM-Training)")
            
            # Erstelle EINEN Parser für alle Verzeichnisse
            # Damit funktioniert die globale Duplikaterkennung über alle Logfiles hinweg
            if mode == "avstumpfl":
                parser = AVStumpflLogParser(progress_callback=self._update_progress)
            else:
                parser = LogParser(progress_callback=self._update_progress)
            
            for directory in self.directories:
                if not self.is_parsing:
                    break
                
                self._log(f"Durchsuche Verzeichnis: {directory}")
                
                # Verwende denselben Parser für alle Verzeichnisse
                # So werden identische Fehler über alle Logfiles nur einmal erfasst
                results = parser.parse_directory(directory)
                all_results.extend(results)
                
                # Zeige Statistik inkl. übersprungener Duplikate
                unique_count = len(all_results)
                skipped_count = parser.skipped_duplicates
                self.root.after(0, lambda u=unique_count, s=skipped_count: 
                    self.stats_var.set(f"Eindeutige Fehler: {u} | Duplikate übersprungen: {s}")
                )
            
            if self.is_parsing and all_results:
                # Berechne Basispfad für Ausgabedateien
                output_base = Path(output_path).stem
                output_dir = Path(output_path).parent
                
                # Export Detailliert
                if self.export_detailed.get():
                    # DATENBANK-MODUS: Erweitere bestehende Datenbank
                    if self.use_database_mode.get() and self.database_file and mode == "avstumpfl":
                        self._log(f"Erweitere Datenbank mit {len(all_results)} neuen Einträgen...")
                        
                        db_file, new_entries, total_entries = AVStumpflCSVExporter.export_to_database(
                            all_results,
                            self.database_file,
                            anonymizer=anonymizer,
                            add_category=self.add_error_category.get()
                        )
                        
                        self._log(f"✓ Datenbank aktualisiert: {Path(db_file).name}")
                        self._log(f"  • Neue Fehler: {new_entries}")
                        self._log(f"  • Gesamt: {total_entries} Einträge")
                        
                        # Aktualisiere Statistik-Label
                        self.db_stats_label.config(
                            text=f"📊 Datenbank: {total_entries} Einträge ({new_entries} neu hinzugefügt)",
                            foreground='green'
                        )
                        
                        messagebox.showinfo(
                            "Datenbank erweitert",
                            f"Datenbank erfolgreich aktualisiert:\\n\\n"
                            f"Neue Fehler: {new_entries}\\n"
                            f"Gesamt: {total_entries} Einträge\\n\\n"
                            f"Datei: {Path(db_file).name}"
                        )
                    
                    # NORMALER MODUS: Erstelle neue CSV
                    else:
                        self._log(f"Exportiere {len(all_results)} eindeutige Einträge (Detailliert)...")
                        detail_path = output_dir / f"{output_base}_detail.csv"
                        
                        if mode == "avstumpfl":
                            AVStumpflCSVExporter.export(
                                all_results, 
                                str(detail_path),
                                anonymizer=anonymizer,
                                add_category=self.add_error_category.get()
                            )
                        else:
                            CSVExporter.export(
                                all_results, 
                                str(detail_path),
                                anonymizer=anonymizer,
                                add_category=self.add_error_category.get()
                            )
                        
                        self._log(f"✓ Detailliert: {detail_path}")
                
                # Export Zusammengefasst
                if self.export_summary.get():
                    self._log("Erstelle zusammengefasste Ansicht...")
                    summary_path = output_dir / f"{output_base}_summary.csv"
                    SummaryExporter.export_grouped_csv(
                        all_results, 
                        str(summary_path),
                        anonymizer=anonymizer
                    )
                    self._log(f"✓ Zusammengefasst: {summary_path}")
                
                # Export Statistik
                if self.export_statistics.get():
                    self._log("Erstelle Statistik...")
                    stats_path = output_dir / f"{output_base}_statistics.txt"
                    SummaryExporter.export_statistics(
                        all_results,
                        str(stats_path),
                        anonymizer=anonymizer
                    )
                    self._log(f"✓ Statistik: {stats_path}")
                
                # Zeige Anonymisierungs-Statistik
                if anonymizer:
                    anon_stats = anonymizer.get_stats()
                    self._log("\nAnonymisierungs-Übersicht:")
                    self._log(f"  - IPs anonymisiert: {anon_stats['ips_anonymized']}")
                    self._log(f"  - Pfade anonymisiert: {anon_stats['paths_anonymized']}")
                    self._log(f"  - Hostnamen anonymisiert: {anon_stats['hostnames_anonymized']}")
                    self._log(f"  - Dateinamen anonymisiert: {anon_stats['filenames_anonymized']}")
                
                # Berechne Gesamtzahl übersprungener Duplikate
                total_skipped = sum(p.skipped_duplicates for p in [parser] if hasattr(parser, 'skipped_duplicates'))
                
                # Erstelle Zusammenfassung
                summary_msg = f"Parsing abgeschlossen!\n\n"
                summary_msg += f"Eindeutige Fehler gefunden: {len(all_results)}\n"
                summary_msg += f"Duplikate übersprungen: {total_skipped}\n\n"
                summary_msg += f"Exportierte Dateien:\n"
                if self.export_detailed.get():
                    summary_msg += f"  ✓ Detail-CSV\n"
                if self.export_summary.get():
                    summary_msg += f"  ✓ Zusammenfassung-CSV\n"
                if self.export_statistics.get():
                    summary_msg += f"  ✓ Statistik-TXT\n"
                if anonymizer:
                    summary_msg += f"\n🔒 Daten wurden anonymisiert (bereit für LLM-Training)"
                
                self.root.after(0, lambda: messagebox.showinfo("Fertig", summary_msg))
            elif not all_results:
                self._log("Keine Fehler gefunden.")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Fertig",
                    "Parsing abgeschlossen, aber keine Fehler gefunden."
                ))
        
        except Exception as e:
            import traceback
            self._log(f"FEHLER: {str(e)}")
            self._log(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror(
                "Fehler",
                f"Ein Fehler ist aufgetreten:\n{str(e)}"
            ))
        
        finally:
            self._parsing_finished()
    
    def _create_temp_dir(self):
        """Erstellt ein temporäres Verzeichnis im konfigurierten Temp-Ordner"""
        if self.custom_temp_dir:
            # Verwende benutzerdefinierten Temp-Ordner
            return tempfile.mkdtemp(prefix="logparser_zip_", dir=self.custom_temp_dir)
        else:
            # Verwende System-Temp
            return tempfile.mkdtemp(prefix="logparser_zip_")
    
    def _select_temp_directory(self):
        """Lässt User einen Temp-Ordner für ZIP-Extraktion auswählen"""
        directory = filedialog.askdirectory(
            title="Temp-Ordner für ZIP-Extraktion auswählen",
            initialdir=self.custom_temp_dir if self.custom_temp_dir else Path.home()
        )
        
        if directory:
            directory = Path(directory)
            
            # Prüfe ob Verzeichnis beschreibbar ist
            test_file = directory / ".logparser_write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                
                self.custom_temp_dir = str(directory)
                self.temp_dir_var.set(str(directory))
                self._update_temp_space_info()
                self._log(f"Temp-Ordner gesetzt: {directory}")
                
                messagebox.showinfo(
                    "Temp-Ordner gesetzt",
                    f"ZIP-Dateien werden nun extrahiert nach:\n{directory}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Fehler",
                    f"Verzeichnis ist nicht beschreibbar:\n{directory}\n\nFehler: {e}"
                )
    
    def _reset_temp_directory(self):
        """Setzt Temp-Ordner auf System-Standard zurück"""
        self.custom_temp_dir = None
        self.temp_dir_var.set("Standard (System-Temp)")
        self._update_temp_space_info()
        self._log("Temp-Ordner zurückgesetzt auf System-Standard")
    
    def _update_temp_space_info(self):
        """Aktualisiert die Anzeige des verfügbaren Speicherplatzes"""
        try:
            if self.custom_temp_dir:
                temp_path = Path(self.custom_temp_dir)
            else:
                temp_path = Path(tempfile.gettempdir())
            
            # Hole Laufwerk-Informationen
            import shutil
            usage = shutil.disk_usage(temp_path)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            percent_free = (usage.free / usage.total) * 100
            
            # Farbe basierend auf verfügbarem Speicher
            if free_gb < 5:
                color = 'red'
                warning = ' ⚠️ WENIG SPEICHER!'
            elif free_gb < 20:
                color = 'orange'
                warning = ' ⚠️'
            else:
                color = 'green'
                warning = ''
            
            info_text = f"Laufwerk {temp_path.drive if hasattr(temp_path, 'drive') else temp_path}: {free_gb:.1f} GB frei von {total_gb:.1f} GB ({percent_free:.1f}%){warning}"
            self.temp_space_label.config(text=info_text, foreground=color)
            
        except Exception as e:
            self.temp_space_label.config(text=f"Speicherplatz-Info nicht verfügbar: {e}", foreground='gray')
    
    def _toggle_database_mode(self):
        """Aktiviert/Deaktiviert den Datenbank-Modus"""
        if self.use_database_mode.get():
            self.db_load_btn.config(state='normal')
            self.db_new_btn.config(state='normal')
            self._log("Datenbank-Modus aktiviert")
        else:
            self.db_load_btn.config(state='disabled')
            self.db_new_btn.config(state='disabled')
            self.database_file = None
            self.db_file_var.set("Keine Datenbank geladen")
            self.db_stats_label.config(text="")
            self._log("Datenbank-Modus deaktiviert")
    
    def _load_database(self):
        """Lädt eine bestehende Datenbank-CSV"""
        file_path = filedialog.askopenfilename(
            title="Datenbank-CSV laden",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
            initialdir=Path.home() / "Desktop"
        )
        
        if file_path:
            try:
                # Prüfe ob Datei lesbar ist
                import csv
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    
                    # Validiere Header
                    required_cols = ['Type/Source', 'Description', 'Severity']
                    if not all(col in reader.fieldnames for col in required_cols):
                        messagebox.showerror(
                            "Ungültige Datenbank",
                            f"Die CSV-Datei enthält nicht alle erforderlichen Spalten.\\n\\n"
                            f"Erforderlich: {', '.join(required_cols)}"
                        )
                        return
                    
                    self.database_file = file_path
                    self.db_file_var.set(Path(file_path).name)
                    
                    # Zeige Statistik
                    unique_errors = len(set(f"{r.get('Severity', '')}|{r.get('Type/Source', '')}|{r.get('Description', '')}" for r in rows))
                    self.db_stats_label.config(
                        text=f"📊 Geladen: {len(rows)} Einträge, {unique_errors} unique Fehler",
                        foreground='green'
                    )
                    
                    self._log(f"Datenbank geladen: {Path(file_path).name} ({len(rows)} Einträge)")
                    
                    messagebox.showinfo(
                        "Datenbank geladen",
                        f"Datenbank erfolgreich geladen:\\n\\n"
                        f"Datei: {Path(file_path).name}\\n"
                        f"Einträge: {len(rows)}\\n"
                        f"Unique Fehler: {unique_errors}\\n\\n"
                        f"Neue Scans werden diese Datenbank erweitern."
                    )
            
            except Exception as e:
                messagebox.showerror(
                    "Fehler beim Laden",
                    f"Konnte Datenbank nicht laden:\\n{e}"
                )
    
    def _create_new_database(self):
        """Erstellt eine neue Datenbank-CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Neue Datenbank erstellen",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
            initialdir=Path.home() / "Desktop",
            initialfile="fehler_datenbank.csv"
        )
        
        if file_path:
            try:
                # Erstelle leere CSV mit Header
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    header = ['Log-Kategorie', 'Ordner', 'Logfile-Gruppe', 'Dateiname-Original', 'Anzahl']
                    if self.add_error_category.get():
                        header.append('Fehler-Kategorie')
                    header.extend(['Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
                    writer.writerow(header)
                
                self.database_file = file_path
                self.db_file_var.set(Path(file_path).name)
                self.db_stats_label.config(
                    text="📊 Neue Datenbank: 0 Einträge",
                    foreground='blue'
                )
                
                self._log(f"Neue Datenbank erstellt: {Path(file_path).name}")
                
                messagebox.showinfo(
                    "Datenbank erstellt",
                    f"Neue Datenbank erfolgreich erstellt:\\n\\n"
                    f"Datei: {Path(file_path).name}\\n\\n"
                    f"Die Datenbank ist bereit für den ersten Scan."
                )
            
            except Exception as e:
                messagebox.showerror(
                    "Fehler beim Erstellen",
                    f"Konnte Datenbank nicht erstellen:\\n{e}"
                )
    
    def _cleanup_old_temp_dirs(self):
        """Löscht alle alten logparser_zip_* Verzeichnisse beim Programmstart"""
        try:
            # Cleanup im System-Temp
            temp_base = Path(tempfile.gettempdir())
            old_dirs = list(temp_base.glob("logparser_zip_*"))
            
            total_size = 0
            total_cleaned = 0
            
            for old_dir in old_dirs:
                try:
                    # Berechne Größe vor dem Löschen
                    size = sum(f.stat().st_size for f in old_dir.rglob('*') if f.is_file())
                    total_size += size
                    shutil.rmtree(old_dir)
                    total_cleaned += 1
                except Exception as e:
                    # Fehler ignorieren - evtl. von anderer Instanz verwendet
                    pass
            
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                self._log(f"Startup: {total_cleaned} alte Cache-Verzeichnisse gelöscht ({size_mb:.1f} MB freigegeben)")
        except Exception as e:
            # Startup-Fehler nicht kritisch - einfach loggen
            print(f"Startup cleanup warning: {e}")
    
    def _manual_cache_cleanup(self):
        """Manuelles Leeren des Cache - alle logparser temp-Verzeichnisse"""
        try:
            # Sammle Verzeichnisse aus beiden Locations
            all_dirs = []
            
            # System-Temp
            temp_base = Path(tempfile.gettempdir())
            all_dirs.extend(list(temp_base.glob("logparser_zip_*")))
            
            # Benutzerdefinierter Temp-Ordner (falls gesetzt)
            if self.custom_temp_dir:
                custom_base = Path(self.custom_temp_dir)
                all_dirs.extend(list(custom_base.glob("logparser_zip_*")))
            
            # Duplikate entfernen
            all_dirs = list(set(all_dirs))
            
            if not all_dirs:
                messagebox.showinfo(
                    "Cache leeren",
                    "Kein Cache gefunden. Der Cache ist bereits leer."
                )
                return
            
            # Berechne Gesamtgröße
            total_size = 0
            for cache_dir in all_dirs:
                try:
                    size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                    total_size += size
                except:
                    pass
            
            size_mb = total_size / (1024 * 1024)
            
            # Zeige Locations
            locations_info = "System-Temp"
            if self.custom_temp_dir:
                locations_info += f" + {self.custom_temp_dir}"
            
            # Bestätigung vom User
            result = messagebox.askyesno(
                "Cache leeren",
                f"Gefunden: {len(all_dirs)} Cache-Verzeichnisse ({size_mb:.1f} MB)\n"
                f"Location(s): {locations_info}\n\n"
                f"Alle Cache-Verzeichnisse löschen?\n\n"
                f"Hinweis: Dies löscht auch extrahierte ZIP-Dateien aus der aktuellen Liste."
            )
            
            if result:
                deleted_count = 0
                freed_size = 0
                
                for cache_dir in all_dirs:
                    try:
                        size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
                        shutil.rmtree(cache_dir)
                        deleted_count += 1
                        freed_size += size
                    except Exception as e:
                        self._log(f"Warnung: Konnte {cache_dir.name} nicht löschen: {e}")
                
                # Eigene temp_dirs Liste leeren
                self.temp_dirs.clear()
                
                # Aktualisiere Liste - entferne gelöschte Verzeichnisse
                remaining_dirs = []
                for directory in self.directories:
                    if Path(directory).exists():
                        remaining_dirs.append(directory)
                    else:
                        self._log(f"Aus Liste entfernt (gelöscht): {directory}")
                
                self.directories = remaining_dirs
                self._update_directory_list()
                
                freed_mb = freed_size / (1024 * 1024)
                messagebox.showinfo(
                    "Cache geleert",
                    f"Erfolgreich gelöscht:\n"
                    f"• {deleted_count} Cache-Verzeichnisse\n"
                    f"• {freed_mb:.1f} MB Speicherplatz freigegeben"
                )
                self._log(f"Cache manuell geleert: {deleted_count} Verzeichnisse, {freed_mb:.1f} MB freigegeben")
        
        except Exception as e:
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Leeren des Cache:\n{str(e)}"
            )
    
    def _cleanup_temp_dirs(self):
        """Löscht alle temporären Verzeichnisse dieser Session"""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
                    self._log(f"Temporäres Verzeichnis gelöscht: {temp_dir}")
            except Exception as e:
                self._log(f"Warnung: Konnte temporäres Verzeichnis nicht löschen: {e}")
        self.temp_dirs.clear()
    
    def _stop_parsing(self):
        """Bricht den Parsing-Prozess ab"""
        self.is_parsing = False
        self._log("Parsing abgebrochen vom Benutzer")
    
    def _parsing_finished(self):
        """Wird aufgerufen wenn das Parsing beendet ist"""
        self.root.after(0, self._reset_ui)
        # KEIN Cleanup nach Parsing - temp_dirs werden weiter benötigt
        # für erneutes Parsing mit anderen Settings
        # Cleanup erfolgt nur beim Schließen oder manuellen Entfernen
    
    def _reset_ui(self):
        """Setzt die UI zurück"""
        self.is_parsing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Bereit")
        self.progress.stop()
    
    def run(self):
        """Startet die Anwendung"""
        # Cleanup beim Schließen
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen - Automatisches Cache-Cleanup"""
        try:
            # Sammle alle logparser_zip_* Verzeichnisse aus beiden Locations
            all_temp_dirs = []
            
            # System-Temp
            temp_base = Path(tempfile.gettempdir())
            all_temp_dirs.extend(list(temp_base.glob("logparser_zip_*")))
            
            # Benutzerdefinierter Temp-Ordner (falls gesetzt)
            if self.custom_temp_dir:
                custom_base = Path(self.custom_temp_dir)
                all_temp_dirs.extend(list(custom_base.glob("logparser_zip_*")))
            
            # Duplikate entfernen
            all_temp_dirs = list(set(all_temp_dirs))
            
            # Lösche alle gefundenen Verzeichnisse
            if all_temp_dirs:
                deleted_count = 0
                total_size = 0
                
                for temp_dir in all_temp_dirs:
                    try:
                        # Berechne Größe vor dem Löschen
                        size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                        total_size += size
                        shutil.rmtree(temp_dir)
                        deleted_count += 1
                    except Exception as e:
                        # Fehler ignorieren - evtl. von anderer Instanz verwendet
                        pass
                
                if deleted_count > 0:
                    size_mb = total_size / (1024 * 1024)
                    print(f"Exit cleanup: {deleted_count} Cache-Verzeichnisse gelöscht ({size_mb:.1f} MB freigegeben)")
        
        except Exception as e:
            # Cleanup-Fehler beim Beenden sind nicht kritisch
            print(f"Exit cleanup warning: {e}")
        
        finally:
            # Fenster schließen
            self.root.destroy()
