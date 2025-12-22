"""
Main Window - GUI für den LogfileParser
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from pathlib import Path
from datetime import datetime
from core import LogParser, CSVExporter


class LogParserApp:
    """Hauptfenster der LogfileParser-Anwendung"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LogfileParser")
        self.root.geometry("900x700")
        
        self.directories = []
        self.is_parsing = False
        self.parser = None
        
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
            text="Entfernen",
            command=self._remove_directory
        ).pack(side=tk.LEFT, padx=2)
        
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
        default_output = str(Path.cwd() / f"logparser_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
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
        
        self.stats_var = tk.StringVar(value="Fehler gefunden: 0")
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
        """Fügt ein Verzeichnis zur Liste hinzu"""
        directory = filedialog.askdirectory(title="Verzeichnis auswählen")
        if directory and directory not in self.directories:
            self.directories.append(directory)
            self.dir_listbox.insert(tk.END, directory)
            self._log(f"Verzeichnis hinzugefügt: {directory}")
    
    def _remove_directory(self):
        """Entfernt das ausgewählte Verzeichnis"""
        selection = self.dir_listbox.curselection()
        if selection:
            index = selection[0]
            directory = self.directories[index]
            self.directories.pop(index)
            self.dir_listbox.delete(index)
            self._log(f"Verzeichnis entfernt: {directory}")
    
    def _clear_directories(self):
        """Leert die Verzeichnisliste"""
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
            
            for directory in self.directories:
                if not self.is_parsing:
                    break
                
                self._log(f"Durchsuche Verzeichnis: {directory}")
                
                parser = LogParser(progress_callback=self._update_progress)
                results = parser.parse_directory(directory)
                all_results.extend(results)
                
                self.root.after(0, lambda r=len(all_results): 
                    self.stats_var.set(f"Fehler gefunden: {r}")
                )
            
            if self.is_parsing and all_results:
                self._log(f"Exportiere {len(all_results)} Einträge nach CSV...")
                CSVExporter.export(all_results, output_path)
                self._log(f"Erfolgreich exportiert: {output_path}")
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Fertig",
                    f"Parsing abgeschlossen!\n\n"
                    f"Fehler gefunden: {len(all_results)}\n"
                    f"Ausgabedatei: {output_path}"
                ))
            elif not all_results:
                self._log("Keine Fehler gefunden.")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Fertig",
                    "Parsing abgeschlossen, aber keine Fehler gefunden."
                ))
        
        except Exception as e:
            self._log(f"FEHLER: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror(
                "Fehler",
                f"Ein Fehler ist aufgetreten:\n{str(e)}"
            ))
        
        finally:
            self._parsing_finished()
    
    def _stop_parsing(self):
        """Bricht den Parsing-Prozess ab"""
        self.is_parsing = False
        self._log("Parsing abgebrochen vom Benutzer")
    
    def _parsing_finished(self):
        """Wird aufgerufen wenn das Parsing beendet ist"""
        self.root.after(0, self._reset_ui)
    
    def _reset_ui(self):
        """Setzt die UI zurück"""
        self.is_parsing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Bereit")
        self.progress.stop()
    
    def run(self):
        """Startet die Anwendung"""
        self.root.mainloop()
