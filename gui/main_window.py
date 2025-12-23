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
from core.summary_exporter import SummaryExporter


class LogParserApp:
    """Main window for the LogfileParser application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LogfileParser")
        self.root.geometry("950x1050")  # Increased to show all elements including bottom buttons
        self.root.minsize(950, 1050)  # Minimum size to fit all UI elements
        
        self.directories = []
        self.is_parsing = False
        self.parser = None
        self.parser_mode = tk.StringVar(value="avstumpfl")  # Default: AV Stumpfl Format
        self.temp_dirs = []  # Temporary directories for extracted ZIP files
        self.custom_temp_dir = None  # User-defined temp folder for ZIP extraction
        
        # Cleanup old temp directories on startup
        self._cleanup_old_temp_dirs()
        
        # Export options
        self.export_detailed = tk.BooleanVar(value=True)
        self.export_summary = tk.BooleanVar(value=True)
        self.export_statistics = tk.BooleanVar(value=True)
        self.anonymize_data = tk.BooleanVar(value=False)
        self.add_error_category = tk.BooleanVar(value=True)
        
        # Database mode for persistent error collection
        self.use_database_mode = tk.BooleanVar(value=False)
        self.database_file = None  # Path to database CSV
        
        # Collapsible section states
        self.export_options_expanded = tk.BooleanVar(value=False)
        self.database_expanded = tk.BooleanVar(value=False)
        self.temp_dir_expanded = tk.BooleanVar(value=False)
        self.output_file_expanded = tk.BooleanVar(value=True)  # Output file visible by default
        
        # Load saved settings (e.g., last database)
        self._load_settings()
        
        self._setup_ui()
        
        # Update UI with loaded settings
        self._update_ui_from_settings()
    
    def _create_collapsible_frame(self, parent, title, var_expanded):
        """Creates a collapsible frame with expand/collapse functionality"""
        container = ttk.Frame(parent)
        container.pack(fill=tk.X, padx=10, pady=5)
        
        # Header with toggle button
        header = ttk.Frame(container)
        header.pack(fill=tk.X)
        
        # Toggle button
        toggle_btn = ttk.Button(
            header,
            text="▼ " + title if var_expanded.get() else "▶ " + title,
            command=lambda: self._toggle_section(container, content_frame, toggle_btn, title, var_expanded),
            width=80
        )
        toggle_btn.pack(fill=tk.X)
        
        # Content frame
        content_frame = ttk.Frame(container, padding="10")
        if var_expanded.get():
            content_frame.pack(fill=tk.BOTH, expand=True)
        
        return content_frame
    
    def _toggle_section(self, container, content_frame, button, title, var_expanded):
        """Toggles visibility of a collapsible section"""
        if var_expanded.get():
            # Collapse
            content_frame.pack_forget()
            button.config(text="▶ " + title)
            var_expanded.set(False)
        else:
            # Expand
            content_frame.pack(fill=tk.BOTH, expand=True)
            button.config(text="▼ " + title)
            var_expanded.set(True)
    
    def _setup_ui(self):
        """Creates the user interface"""
        
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="LogfileParser",
            font=('Arial', 16, 'bold')
        ).pack(side=tk.LEFT)
        
        # Parser Mode Selection
        mode_frame = ttk.LabelFrame(self.root, text="Parser Mode", padding="10")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Radiobutton(
            mode_frame,
            text="AV Stumpfl Format (Structured log with Date/Time/Severity/Type/Description)",
            variable=self.parser_mode,
            value="avstumpfl"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            mode_frame,
            text="Generic Mode (Simple keyword search: error, warning, fatal, critical)",
            variable=self.parser_mode,
            value="generic"
        ).pack(anchor=tk.W, pady=2)
        
        # Directory Selection Area
        dir_frame = ttk.LabelFrame(self.root, text="Directories", padding="10")
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Listbox for directories
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
        
        # Buttons for directory management
        btn_frame = ttk.Frame(dir_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            btn_frame,
            text="Add Directory",
            command=self._add_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Add File",
            command=self._add_file
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Remove",
            command=self._remove_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Clear List",
            command=self._clear_directories
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="Clear Cache",
            command=self._manual_cache_cleanup
        ).pack(side=tk.LEFT, padx=2)
        
        # Export Options - COLLAPSIBLE
        export_options_content = self._create_collapsible_frame(
            self.root,
            "Export Options",
            self.export_options_expanded
        )
        
        # Left column - Export types
        left_col = ttk.Frame(export_options_content)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        ttk.Label(left_col, text="Export Formats:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Checkbutton(
            left_col,
            text="Detailed (all details)",
            variable=self.export_detailed
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            left_col,
            text="Summary (grouped by error type)",
            variable=self.export_summary
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            left_col,
            text="Statistics (overview as TXT)",
            variable=self.export_statistics
        ).pack(anchor=tk.W, pady=2)
        
        # Right column - Processing options
        right_col = ttk.Frame(export_options_content)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(right_col, text="Data Processing:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Checkbutton(
            right_col,
            text="Error Categorization (Network/File/System/...)",
            variable=self.add_error_category
        ).pack(anchor=tk.W, pady=2)
        
        # Persistent Error Database - COLLAPSIBLE
        db_mode_content = self._create_collapsible_frame(
            self.root,
            "Persistent Error Database",
            self.database_expanded
        )
        
        ttk.Checkbutton(
            db_mode_content,
            text="📊 Database Mode: Append to existing CSV instead of creating new",
            variable=self.use_database_mode,
            command=self._toggle_database_mode
        ).pack(anchor=tk.W, pady=2)
        
        # Database file display
        db_file_frame = ttk.Frame(db_mode_content)
        db_file_frame.pack(fill=tk.X, pady=5)
        
        self.db_file_var = tk.StringVar(value="No database loaded")
        db_entry = ttk.Entry(
            db_file_frame,
            textvariable=self.db_file_var,
            state='readonly'
        )
        db_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.db_load_btn = ttk.Button(
            db_file_frame,
            text="Load Database",
            command=self._load_database,
            state='disabled'
        )
        self.db_load_btn.pack(side=tk.LEFT, padx=2)
        
        self.db_new_btn = ttk.Button(
            db_file_frame,
            text="Create New",
            command=self._create_new_database,
            state='disabled'
        )
        self.db_new_btn.pack(side=tk.LEFT, padx=2)
        
        # Database statistics label
        self.db_stats_label = ttk.Label(
            db_mode_content,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.db_stats_label.pack(anchor=tk.W, padx=5)
        
        ttk.Label(
            db_mode_content,
            text="💡 Database Mode: Collects errors across multiple sessions. New scans extend the existing database.",
            font=('Arial', 8),
            foreground='gray',
            wraplength=900
        ).pack(anchor=tk.W, padx=20, pady=(5, 0))
        
        # ZIP Extraction Temp Folder - COLLAPSIBLE
        temp_config_content = self._create_collapsible_frame(
            self.root,
            "ZIP Extraction Temp Folder",
            self.temp_dir_expanded
        )
        
        # Info label
        ttk.Label(
            temp_config_content,
            text="Choose a drive with sufficient storage space for temporary ZIP extraction:",
            font=('Arial', 9)
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Temp path display and selection
        temp_path_frame = ttk.Frame(temp_config_content)
        temp_path_frame.pack(fill=tk.X, pady=2)
        
        self.temp_dir_var = tk.StringVar(value="Standard (System Temp)")
        temp_entry = ttk.Entry(
            temp_path_frame,
            textvariable=self.temp_dir_var,
            state='readonly'
        )
        temp_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Button(
            temp_path_frame,
            text="Browse...",
            command=self._select_temp_directory
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            temp_path_frame,
            text="Reset",
            command=self._reset_temp_directory
        ).pack(side=tk.LEFT, padx=2)
        
        # Info about available storage space
        self.temp_space_label = ttk.Label(
            temp_config_content,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        self.temp_space_label.pack(anchor=tk.W, padx=5)
        self._update_temp_space_info()
        
        # Output File - COLLAPSIBLE
        output_content = self._create_collapsible_frame(
            self.root,
            "Output File",
            self.output_file_expanded
        )
        
        output_inner = ttk.Frame(output_content)
        output_inner.pack(fill=tk.X)
        
        self.output_path_var = tk.StringVar()
        # Use safe directory: Desktop or Documents, not System32
        safe_dir = Path.home() / "Desktop"
        if not safe_dir.exists():
            safe_dir = Path.home() / "Documents"
        if not safe_dir.exists():
            safe_dir = Path(__file__).parent.parent  # Program directory as fallback
        
        default_output = str(safe_dir / f"logparser_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        self.output_path_var.set(default_output)
        
        ttk.Entry(
            output_inner,
            textvariable=self.output_path_var,
            state='readonly'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            output_inner,
            text="Browse...",
            command=self._select_output_file
        ).pack(side=tk.RIGHT)
        
        # Fortschritts-Bereich
        progress_frame = ttk.LabelFrame(self.root, text="Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Aktueller Status
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ready")
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
        
        self.stats_var = tk.StringVar(value="Unique Errors: 0 | Duplicates Skipped: 0")
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
            text="Start Parsing",
            command=self._start_parsing,
            style='Accent.TButton'
        )
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="Cancel",
            command=self._stop_parsing,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Clear Log",
            command=self._clear_log
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            control_frame,
            text="Exit",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=2)
    
    def _add_directory(self):
        """Adds a directory to the list and automatically finds all ZIP files in it"""
        directory = filedialog.askdirectory(title="Select Directory")
        if not directory:
            return
            
        directory_path = Path(directory)
        
        # Add main directory
        if directory not in self.directories:
            self.directories.append(directory)
            self.dir_listbox.insert(tk.END, directory)
            self._log(f"Directory added: {directory}")
        
        # Search recursively for ZIP files
        zip_files = list(directory_path.rglob("*.zip"))
        if zip_files:
            self._log(f"Found ZIP files: {len(zip_files)}")
            # Show progress dialog and extract ZIPs
            self._extract_zip_files_with_progress(zip_files)
        else:
            self._log("No ZIP files found in directory")
    
    def _add_file(self):
        """Adds a single file (automatic detection if ZIP)"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("All Supported Files", "*.zip;*.log;*.txt"),
                ("ZIP Archives", "*.zip"),
                ("Log Files", "*.log;*.txt"),
                ("All Files", "*.*")
            ]
        )
        if not file_path:
            return
        
        file_path_obj = Path(file_path)
        
        # Check if ZIP file (robust detection)
        is_zip = file_path_obj.suffix.lower() == '.zip' or zipfile.is_zipfile(file_path)
        
        if is_zip:
            self._log(f"ZIP file detected: {file_path_obj.name}")
            # Show progress dialog for single ZIP
            self._extract_zip_files_with_progress([Path(file_path)])
        else:
            self._log(f"Log file detected: {file_path_obj.name}")
            # Add file's directory (so the file will be parsed)
            parent_dir = str(file_path_obj.parent)
            if parent_dir not in self.directories:
                self.directories.append(parent_dir)
                self.dir_listbox.insert(tk.END, f"📄 {file_path_obj.name} → {parent_dir}")
                self._log(f"File added: {file_path_obj.name}")
    
    def _extract_zip_files_with_progress(self, zip_files: list):
        """Extracts multiple ZIP files with progress display"""
        # Create progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("Extracting ZIP Files")
        progress_dialog.geometry("600x200")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()
        
        # Prevent closing during extraction
        extraction_complete = threading.Event()
        progress_dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Status label
        status_label = ttk.Label(
            progress_dialog,
            text=f"Extracting 0 of {len(zip_files)} ZIP files...",
            font=('Arial', 10, 'bold')
        )
        status_label.pack(pady=(20, 10))
        
        # Current filename
        file_label = ttk.Label(
            progress_dialog,
            text="Preparing...",
            font=('Arial', 9),
            wraplength=550
        )
        file_label.pack(pady=5)
        
        # Progress bar
        progress_bar = ttk.Progressbar(
            progress_dialog,
            mode='determinate',
            length=550,
            maximum=len(zip_files)
        )
        progress_bar.pack(pady=10)
        
        # Detail label
        detail_label = ttk.Label(
            progress_dialog,
            text="",
            font=('Arial', 8),
            foreground='gray'
        )
        detail_label.pack(pady=5)
        
        # Extract ZIPs in thread
        def extract_worker():
            for idx, zip_file in enumerate(zip_files, 1):
                try:
                    zip_path_obj = Path(zip_file)
                    
                    # Update UI
                    self.root.after(0, lambda i=idx, name=zip_path_obj.name: (
                        status_label.config(text=f"Extracting {i} of {len(zip_files)} ZIP files..."),
                        file_label.config(text=f"📦 {name}"),
                        progress_bar.config(value=i-1)
                    ))
                    
                    # Create temporary directory
                    temp_dir = self._create_temp_dir()
                    self.temp_dirs.append(temp_dir)
                    
                    # Extract ZIP
                    self.root.after(0, lambda: self._log(f"Extracting ZIP: {zip_path_obj.name}"))
                    with zipfile.ZipFile(str(zip_file), 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Count extracted files
                    all_files = list(Path(temp_dir).rglob('*'))
                    log_files = [f for f in all_files if f.suffix.lower() in ['.log', '.txt']]
                    
                    # Add to list
                    self.directories.append(temp_dir)
                    display_name = f"📦 {zip_path_obj.name} ({len(log_files)} Logs)"
                    self.root.after(0, lambda dn=display_name: self.dir_listbox.insert(tk.END, dn))
                    self.root.after(0, lambda lf=len(log_files), af=len(all_files): 
                                  self._log(f"  └─ Extracted: {lf} log files, {af} files total"))
                    
                    # Update details
                    self.root.after(0, lambda lf=len(log_files): 
                                  detail_label.config(text=f"✓ {lf} log files found"))
                    
                except Exception as e:
                    error_msg = f"ERROR extracting {Path(zip_file).name}: {str(e)}"
                    self.root.after(0, lambda msg=error_msg: self._log(msg))
                    self.root.after(0, lambda: detail_label.config(text="✗ Extraction error", foreground='red'))
            
            # Mark extraction as complete
            extraction_complete.set()
            
            # Close dialog after completion
            self.root.after(0, progress_dialog.destroy)
            self.root.after(100, lambda: self._log(f"✓ {len(zip_files)} ZIP files successfully extracted"))
        
        # Start thread (NICHT als daemon, damit er zu Ende läuft)
        thread = threading.Thread(target=extract_worker, daemon=False)
        thread.start()
        
        # Wait for extraction completion (mit Timeout)
        def wait_for_extraction():
            if extraction_complete.wait(timeout=0.1):
                # Extraction completed
                return
            else:
                # Not finished yet, check again
                self.root.after(100, wait_for_extraction)
        
        wait_for_extraction()
    
    def _add_zip_file(self, zip_path: str):
        """Extracts ZIP file to temporary directory"""
        try:
            zip_path_obj = Path(zip_path)
            
            # Create temporary directory
            temp_dir = self._create_temp_dir()
            self.temp_dirs.append(temp_dir)
            
            # Extracting ZIP
            self._log(f"Extracting ZIP: {zip_path_obj.name}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Count extracted files
            all_files = list(Path(temp_dir).rglob('*'))
            log_files = [f for f in all_files if f.suffix.lower() in ['.log', '.txt']]
            
            # Add temporary directory to list
            self.directories.append(temp_dir)
            display_name = f"📦 {zip_path_obj.name} ({len(log_files)} Logs)"
            self.dir_listbox.insert(tk.END, display_name)
            self._log(f"  └─ Extracted: {len(log_files)} log files, {len(all_files)} files total")
            
        except Exception as e:
            messagebox.showerror("Error", f"ZIP file could not be extracted:\n{str(e)}")
            self._log(f"ERROR extracting {Path(zip_path).name}: {str(e)}")
    
    def _remove_directory(self):
        """Removes the selected directory"""
        selection = self.dir_listbox.curselection()
        if selection:
            index = selection[0]
            directory = self.directories[index]
            self.directories.pop(index)
            self.dir_listbox.delete(index)
            
            # If it's a temp directory, perform cleanup
            if directory in self.temp_dirs:
                self.temp_dirs.remove(directory)
                try:
                    if Path(directory).exists():
                        shutil.rmtree(directory)
                        self._log(f"Temporary directory deleted: {directory}")
                except Exception as e:
                    self._log(f"Warning: Could not delete temporary directory: {e}")
            
            self._log(f"Directory removed: {directory}")
    
    def _clear_directories(self):
        """Clears the directory list"""
        self._cleanup_temp_dirs()
        self.directories.clear()
        self.dir_listbox.delete(0, tk.END)
        self._log("Directory list cleared")
    
    def _select_output_file(self):
        """Selects the output CSV file"""
        filename = filedialog.asksaveasfilename(
            title="Select Output File",
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
                "No Directories",
                "Please add at least one directory."
            )
            return
        
        # Initialize output_path (needed for both modes)
        output_path = None
        
        # DATENBANK-MODUS: Validierung
        if self.use_database_mode.get():
            if not self.database_file:
                messagebox.showwarning(
                    "No Database",
                    "Please load an existing database or create a new one."
                )
                return
            
            if not Path(self.database_file).exists():
                result = messagebox.askyesno(
                    "Database Not Found",
                    f"The database file was not found:\\n{self.database_file}\\n\\n"
                    f"Would you like to create a new database?"
                )
                if result:
                    self._create_new_database()
                    if not self.database_file:
                        return
                else:
                    return
            
            # In database mode we use the database file as base
            output_path = self.database_file
        
        # NORMALER MODUS: Output-Pfad Validierung
        else:
            output_path = self.output_path_var.get()
            if not output_path:
                messagebox.showwarning(
                    "No Output File",
                    "Please select an output file."
                )
                return
            
            # Validate output directory
            output_dir = Path(output_path).parent
            if not output_dir.exists():
                messagebox.showerror(
                    "Invalid Path",
                    f"The directory does not exist:\\n{output_dir}"
                )
                return
            
            # Check if directory is writable
            try:
                test_file = output_dir / ".logparser_write_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                messagebox.showerror(
                    "No Write Permission",
                    f"No write permission for:\\n{output_dir}\\n\\n"
                    f"Please choose a different location (e.g. Desktop or Documents).\\n\\n"
                    f"Error: {str(e)}"
                )
                return
        
        self.is_parsing = True
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_var.set("Parsing in progress...")
        self.progress.start()
        
        self._log("=" * 50)
        self._log("Parsing started")
        self._log(f"Directories: {len(self.directories)}")
        
        # Starte Parsing in separatem Thread
        thread = threading.Thread(target=self._parse_thread, args=(output_path,))
        thread.daemon = True
        thread.start()
    
    def _parse_thread(self, output_path: str):
        """Thread-Funktion für das Parsing"""
        try:
            all_results = []
            mode = self.parser_mode.get()
            
            self._log(f"Parser-Modus: {'AV Stumpfl Format' if mode == 'avstumpfl' else 'Generischer Modus'}")
            
            # Create ONE parser for all directories
            # This enables global duplicate detection across all logfiles
            if mode == "avstumpfl":
                parser = AVStumpflLogParser(progress_callback=self._update_progress)
            else:
                parser = LogParser(progress_callback=self._update_progress)
            
            for directory in self.directories:
                if not self.is_parsing:
                    break
                
                self._log(f"Durchsuche Verzeichnis: {directory}")
                
                # Use the same parser for all directories
                # This way identical errors are captured only once across all logfiles
                results = parser.parse_directory(directory)
                all_results.extend(results)
                
                # Zeige Statistik inkl. übersprungener Duplikate
                unique_count = len(all_results)
                skipped_count = parser.skipped_duplicates
                self.root.after(0, lambda u=unique_count, s=skipped_count: 
                    self.stats_var.set(f"Unique Errors: {u} | Duplicates Skipped: {s}")
                )
            
            if self.is_parsing and all_results:
                # Calculate base path for output files
                output_base = Path(output_path).stem
                output_dir = Path(output_path).parent
                
                # Export Detailliert
                if self.export_detailed.get():
                    # DATENBANK-MODUS: Erweitere bestehende Datenbank
                    if self.use_database_mode.get() and self.database_file and mode == "avstumpfl":
                        self._log(f"Erweitere Datenbank mit {len(all_results)} neuen entriesn...")
                        
                        db_file, new_entries, total_entries = AVStumpflCSVExporter.export_to_database(
                            all_results,
                            self.database_file,
                            add_category=self.add_error_category.get()
                        )
                        
                        self._log(f"✓ Datenbank aktualisiert: {Path(db_file).name}")
                        self._log(f"  • New Errors: {new_entries}")
                        self._log(f"  • Gesamt: {total_entries} entries")
                        
                        # Aktualisiere Statistik-Label
                        self.db_stats_label.config(
                            text=f"📊 Datenbank: {total_entries} entries ({new_entries} neu hinzugefügt)",
                            foreground='green'
                        )
                        
                        messagebox.showinfo(
                            "Datenbank erweitert",
                            f"Database successfully updated:\\n\\n"
                            f"New Errors: {new_entries}\\n"
                            f"Gesamt: {total_entries} entries\\n\\n"
                            f"File: {Path(db_file).name}"
                        )
                    
                    # NORMALER MODUS: Erstelle neue CSV
                    else:
                        self._log(f"Exportiere {len(all_results)} eindeutige entries (Detailliert)...")
                        detail_path = output_dir / f"{output_base}_detail.csv"
                        
                        if mode == "avstumpfl":
                            AVStumpflCSVExporter.export(
                                all_results, 
                                str(detail_path),
                                add_category=self.add_error_category.get()
                            )
                        else:
                            CSVExporter.export(
                                all_results, 
                                str(detail_path),
                                add_category=self.add_error_category.get()
                            )
                        
                        self._log(f"✓ Detailliert: {detail_path}")
                
                # Export Zusammengefasst
                if self.export_summary.get():
                    self._log("Erstelle zusammengefasste Ansicht...")
                    summary_path = output_dir / f"{output_base}_summary.csv"
                    SummaryExporter.export_grouped_csv(
                        all_results, 
                        str(summary_path)
                    )
                    self._log(f"✓ Zusammengefasst: {summary_path}")
                
                # Export Statistik
                if self.export_statistics.get():
                    self._log("Erstelle Statistik...")
                    stats_path = output_dir / f"{output_base}_statistics.txt"
                    SummaryExporter.export_statistics(
                        all_results,
                        str(stats_path)
                    )
                    self._log(f"✓ Statistik: {stats_path}")
                
                # Zeige Anonymisierungs-Statistik
                if anonymizer:
                    anon_stats = anonymizer.get_stats()
                    self._log("\nAnonymisierungs-Übersicht:")
                    self._log(f"  - IPs anonymisiert: {anon_stats['ips_anonymized']}")
                    self._log(f"  - Pfade anonymisiert: {anon_stats['paths_anonymized']}")
                    self._log(f"  - Hostnamen anonymisiert: {anon_stats['hostnames_anonymized']}")
                    self._log(f"  - Filenames anonymized: {anon_stats['filenames_anonymized']}")
                
                # Berechne Gesamtzahl übersprungener Duplikate
                total_skipped = sum(p.skipped_duplicates for p in [parser] if hasattr(parser, 'skipped_duplicates'))
                
                # Erstelle Zusammenfassung
                summary_msg = f"Parsing abgeschlossen!\n\n"
                summary_msg += f"Unique Errors gefunden: {len(all_results)}\n"
                summary_msg += f"Duplicates Skipped: {total_skipped}\n\n"
                summary_msg += f"Exportierte Dateien:\n"
                if self.export_detailed.get():
                    summary_msg += f"  ✓ Detail-CSV\n"
                if self.export_summary.get():
                    summary_msg += f"  ✓ Zusammenfassung-CSV\n"
                if self.export_statistics.get():
                    summary_msg += f"  ✓ Statistik-TXT\n"
                if anonymizer:
                    summary_msg += f"\n🔒 Data anonymized (ready for LLM training)"
                
                self.root.after(0, lambda: messagebox.showinfo("Finished", summary_msg))
            elif not all_results:
                self._log("Keine Error gefunden.")
                self.root.after(0, lambda: messagebox.showinfo(
                    "Finished",
                    "Parsing abgeschlossen, aber keine Error gefunden."
                ))
        
        except Exception as e:
            import traceback
            self._log(f"ERROR: {str(e)}")
            self._log(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror(
                "Error",
                f"Ein Error ist aufgetreten:\n{str(e)}"
            ))
        
        finally:
            self._parsing_finished()
    
    def _create_temp_dir(self):
        """Erstellt ein temporäres Verzeichnis im konfigurierten Temp-Folder"""
        if self.custom_temp_dir:
            # Use custom temp folder
            return tempfile.mkdtemp(prefix="logparser_zip_", dir=self.custom_temp_dir)
        else:
            # Verwende System-Temp
            return tempfile.mkdtemp(prefix="logparser_zip_")
    
    def _select_temp_directory(self):
        """Lets user select a temp folder for ZIP extraction"""
        directory = filedialog.askdirectory(
            title="Select Temp Folder for ZIP Extraction",
            initialdir=self.custom_temp_dir if self.custom_temp_dir else Path.home()
        )
        
        if directory:
            directory = Path(directory)
            
            # Check if directory is writable
            test_file = directory / ".logparser_write_test"
            try:
                test_file.write_text("test")
                test_file.unlink()
                
                self.custom_temp_dir = str(directory)
                self.temp_dir_var.set(str(directory))
                self._update_temp_space_info()
                self._log(f"Temp Folder Set: {directory}")
                
                messagebox.showinfo(
                    "Temp Folder Set",
                    f"ZIP-Dateien werden nun extrahiert nach:\n{directory}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Verzeichnis ist nicht beschreibbar:\n{directory}\n\nError: {e}"
                )
    
    def _reset_temp_directory(self):
        """Resets temp folder to system default"""
        self.custom_temp_dir = None
        self.temp_dir_var.set("Standard (System Temp)")
        self._update_temp_space_info()
        self._log("Temp folder reset to system default")
    
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
            self.db_file_var.set("No database loaded")
            self.db_stats_label.config(text="")
            self._log("Datenbank-Modus deaktiviert")
    
    def _load_database(self):
        """Loads an existing database CSV"""
        file_path = filedialog.askopenfilename(
            title="Load Database CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=Path.home() / "Desktop"
        )
        
        if file_path:
            try:
                # Check if file is readable
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
                        text=f"📊 Loaded: {len(rows)} entries, {unique_errors} unique Error",
                        foreground='green'
                    )
                    
                    self._log(f"Datenbank geladen: {Path(file_path).name} ({len(rows)} entries)")
                    
                    messagebox.showinfo(
                        "Datenbank geladen",
                        f"Database successfully loaded:\\n\\n"
                        f"File: {Path(file_path).name}\\n"
                        f"entries: {len(rows)}\\n"
                        f"Unique Error: {unique_errors}\\n\\n"
                        f"Neue Scans werden diese Datenbank erweitern."
                    )
            
            except Exception as e:
                messagebox.showerror(
                    "Error beim Laden",
                    f"Konnte Datenbank nicht laden:\\n{e}"
                )
    
    def _create_new_database(self):
        """Creates a new database CSV"""
        file_path = filedialog.asksaveasfilename(
            title="Create New Database",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialdir=Path.home() / "Desktop",
            initialfile="error_database.csv"
        )
        
        if file_path:
            try:
                # Create empty CSV with header
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    header = ['Log Category', 'Folder', 'Logfile Group', 'Filename-Original', 'Count']
                    if self.add_error_category.get():
                        header.append('Error-Kategorie')
                    header.extend(['Datum', 'Zeit', 'Severity', 'Type/Source', 'Description'])
                    writer.writerow(header)
                
                self.database_file = file_path
                self.db_file_var.set(Path(file_path).name)
                self.db_stats_label.config(
                    text="📊 Neue Datenbank: 0 entries",
                    foreground='blue'
                )
                
                self._log(f"Neue Datenbank erstellt: {Path(file_path).name}")
                
                messagebox.showinfo(
                    "Database Created",
                    f"Neue Datenbank erfolgreich erstellt:\\n\\n"
                    f"File: {Path(file_path).name}\\n\\n"
                    f"The database is ready for the first scan."
                )
            
            except Exception as e:
                messagebox.showerror(
                    "Error Creating",
                    f"Konnte Datenbank nicht erstellen:\\n{e}"
                )
    
    def _load_settings(self):
        """Lädt gespeicherte Einstellungen aus config.json"""
        try:
            config_file = Path(__file__).parent.parent / "config.json"
            if config_file.exists():
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Lade Datenbank-Einstellungen
                if 'database_file' in config and config['database_file']:
                    db_path = Path(config['database_file'])
                    if db_path.exists():
                        self.database_file = str(db_path)
                        self.use_database_mode.set(config.get('use_database_mode', False))
                        print(f"Einstellungen geladen: Datenbank {db_path.name}")
                
                # Lade Custom Temp Dir
                if 'custom_temp_dir' in config and config['custom_temp_dir']:
                    temp_path = Path(config['custom_temp_dir'])
                    if temp_path.exists():
                        self.custom_temp_dir = str(temp_path)
                
        except Exception as e:
            # Error beim Laden ignorieren - verwende Defaults
            print(f"Hinweis: Konnte Einstellungen nicht laden: {e}")
    
    def _save_settings(self):
        """Speichert aktuelle Einstellungen in config.json"""
        try:
            config_file = Path(__file__).parent.parent / "config.json"
            
            config = {
                'database_file': self.database_file,
                'use_database_mode': self.use_database_mode.get(),
                'custom_temp_dir': self.custom_temp_dir
            }
            
            import json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, indent=2, fp=f)
            
            print(f"Einstellungen gespeichert")
            
        except Exception as e:
            # Error beim Speichern nicht kritisch
            print(f"Hinweis: Konnte Einstellungen nicht speichern: {e}")
    
    def _update_ui_from_settings(self):
        """Aktualisiert UI-Elemente mit geladenen Einstellungen"""
        # Datenbank-Modus UI aktualisieren
        if self.database_file:
            db_path = Path(self.database_file)
            self.db_file_var.set(str(db_path))
            
            # Lade Statistik wenn Datei existiert
            if db_path.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(db_path, encoding='utf-8-sig')
                    entry_count = len(df)
                    self.db_stats_label.config(
                        text=f"✓ Datenbank geladen: {entry_count} entries"
                    )
                except:
                    self.db_stats_label.config(text="✓ Database loaded")
            
            # Aktiviere Datenbank-Buttons wenn Datenbank-Modus aktiv
            if self.use_database_mode.get():
                self.db_load_btn.config(state='normal')
                self.db_new_btn.config(state='normal')
        
        # Custom Temp Dir anzeigen
        if self.custom_temp_dir:
            self.temp_dir_var.set(self.custom_temp_dir)
            try:
                self._update_temp_space_info()
            except:
                pass
    
    def _cleanup_old_temp_dirs(self):
        """Deletes all old logparser_zip_* directories on program startup"""
        try:
            # Cleanup in system temp
            temp_base = Path(tempfile.gettempdir())
            old_dirs = list(temp_base.glob("logparser_zip_*"))
            
            total_size = 0
            total_cleaned = 0
            
            for old_dir in old_dirs:
                try:
                    # Calculate size before deletion
                    size = sum(f.stat().st_size for f in old_dir.rglob('*') if f.is_file())
                    total_size += size
                    shutil.rmtree(old_dir)
                    total_cleaned += 1
                except Exception as e:
                    # Error ignorieren - evtl. von anderer Instanz verwendet
                    pass
            
            if total_size > 0:
                size_mb = total_size / (1024 * 1024)
                # Log nur ausgeben wenn UI bereits existiert
                # Beim Startup ist self.log_text noch nicht initialisiert
                try:
                    if hasattr(self, 'log_text'):
                        self._log(f"Startup: {total_cleaned} old cache directories deleted ({size_mb:.1f} MB freed)")
                    else:
                        print(f"Startup: {total_cleaned} old cache directories deleted ({size_mb:.1f} MB freed)")
                except:
                    print(f"Startup: {total_cleaned} old cache directories deleted ({size_mb:.1f} MB freed)")
        except Exception as e:
            # Startup-Error nicht kritisch - einfach loggen
            print(f"Startup cleanup warning: {e}")
    
    def _manual_cache_cleanup(self):
        """Manual cache clearing - all logparser temp directories"""
        try:
            # Sammle Verzeichnisse aus beiden Locations
            all_dirs = []
            
            # System-Temp
            temp_base = Path(tempfile.gettempdir())
            all_dirs.extend(list(temp_base.glob("logparser_zip_*")))
            
            # Benutzerdefinierter Temp-Folder (falls gesetzt)
            if self.custom_temp_dir:
                custom_base = Path(self.custom_temp_dir)
                all_dirs.extend(list(custom_base.glob("logparser_zip_*")))
            
            # Duplikate entfernen
            all_dirs = list(set(all_dirs))
            
            if not all_dirs:
                messagebox.showinfo(
                    "Clear Cache",
                    "No cache found. The cache is already empty."
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
                "Clear Cache",
                f"Found: {len(all_dirs)} cache directories ({size_mb:.1f} MB)\n"
                f"Location(s): {locations_info}\n\n"
                f"Alle cache directories löschen?\n\n"
                f"Note: This will also delete extracted ZIP files from the current list."
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
                        self._log(f"Warning: Could not delete {cache_dir.name}  {e}")
                
                # Eigene temp_dirs Liste leeren
                self.temp_dirs.clear()
                
                # Update list - remove deleted directories
                remaining_dirs = []
                for directory in self.directories:
                    if Path(directory).exists():
                        remaining_dirs.append(directory)
                    else:
                        self._log(f"Removed from list (deleted): {directory}")
                
                self.directories = remaining_dirs
                self._update_directory_list()
                
                freed_mb = freed_size / (1024 * 1024)
                messagebox.showinfo(
                    "Cache Cleared",
                    f"Successfully deleted:\n"
                    f"• {deleted_count} cache directories\n"
                    f"• {freed_mb:.1f} MB Speicherplatz freigegeben"
                )
                self._log(f"Cache manuell geleert: {deleted_count} Verzeichnisse, {freed_mb:.1f} MB freed")
        
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error beim Leeren des Cache:\n{str(e)}"
            )
    
    def _cleanup_temp_dirs(self):
        """Deletes all temporary directories of this session"""
        for temp_dir in self.temp_dirs:
            try:
                if Path(temp_dir).exists():
                    shutil.rmtree(temp_dir)
                    self._log(f"Temporary directory deleted: {temp_dir}")
            except Exception as e:
                self._log(f"Warning: Could not delete temporary directory: {e}")
        self.temp_dirs.clear()
    
    def _stop_parsing(self):
        """Aborts the parsing process"""
        self.is_parsing = False
        self._log("Parsing aborted by user")
    
    def _parsing_finished(self):
        """Called when parsing is finished"""
        self.root.after(0, self._reset_ui)
        # NO cleanup after parsing - temp_dirs are still needed
        # for re-parsing with different settings
        # Cleanup only occurs on close or manual removal
    
    def _reset_ui(self):
        """Resets the UI"""
        self.is_parsing = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_var.set("Ready")
        self.progress.stop()
    
    def run(self):
        """Startet die Anwendung"""
        # Cleanup beim Schließen
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.mainloop()
    
    def _on_closing(self):
        """Wird beim Schließen des Fensters aufgerufen - Automatisches Cache-Cleanup"""
        # Speichere Einstellungen vor dem Schließen
        self._save_settings()
        
        try:
            # Sammle alle logparser_zip_* Verzeichnisse aus beiden Locations
            all_temp_dirs = []
            
            # System-Temp
            temp_base = Path(tempfile.gettempdir())
            all_temp_dirs.extend(list(temp_base.glob("logparser_zip_*")))
            
            # Benutzerdefinierter Temp-Folder (falls gesetzt)
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
                        # Calculate size before deletion
                        size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                        total_size += size
                        shutil.rmtree(temp_dir)
                        deleted_count += 1
                    except Exception as e:
                        # Error ignorieren - evtl. von anderer Instanz verwendet
                        pass
                
                if deleted_count > 0:
                    size_mb = total_size / (1024 * 1024)
                    print(f"Exit cleanup: {deleted_count} cache directories gelöscht ({size_mb:.1f} MB freed)")
        
        except Exception as e:
            # Cleanup-Error beim Beenden sind nicht kritisch
            print(f"Exit cleanup warning: {e}")
        
        finally:
            # Fenster schließen
            self.root.destroy()
