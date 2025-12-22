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
        
        # Export-Optionen
        self.export_detailed = tk.BooleanVar(value=True)
        self.export_summary = tk.BooleanVar(value=True)
        self.export_statistics = tk.BooleanVar(value=True)
        self.anonymize_data = tk.BooleanVar(value=False)
        self.add_error_category = tk.BooleanVar(value=True)
        
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
        
        # 
        ttk.Button(
            btn_frame,
            text="Liste leeren",
            command=self._clear_directories
        ).pack(side=tk.LEFT, padx=2)
        
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
                    temp_dir = tempfile.mkdtemp(prefix="logparser_zip_")
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
            temp_dir = tempfile.mkdtemp(prefix="logparser_zip_")
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
                f"Das Verzeichnis existiert nicht:\n{output_dir}"
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
                f"Keine Schreibberechtigung für:\n{output_dir}\n\n"
                f"Bitte wählen Sie einen anderen Speicherort (z.B. Desktop oder Dokumente).\n\n"
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
    
    def _cleanup_temp_dirs(self):
        """Löscht alle temporären Verzeichnisse"""
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
        """Wird beim Schließen des Fensters aufgerufen"""
        self._cleanup_temp_dirs()
        self.root.destroy()
