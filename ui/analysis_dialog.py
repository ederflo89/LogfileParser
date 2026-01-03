"""
Analysis Dialog - Display error details with database-matched causes and solutions

Provides a dialog window for analyzing individual errors with:
- Error details (severity, type, description)
- Database-matched cause and solution (if available)
- Match type indicator (exact, normalized, fuzzy)
- Similarity score for fuzzy matches
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Dict, Any
from core.database_matcher import DatabaseMatcher
from database.turso_client import TursoClient


class AnalysisDialog:
    """
    Dialog for displaying detailed error analysis
    
    Shows:
    - Error metadata (date, time, severity, source)
    - Full error description
    - Database-matched cause and solution
    - Match confidence and type
    """
    
    def __init__(self, parent, error_data: Dict[str, Any], database_client: Optional[TursoClient] = None):
        """
        Initialize the Analysis Dialog
        
        Args:
            parent: Parent Tkinter window
            error_data: Dictionary containing error details
                Required keys: 'error_text', 'description'
                Optional keys: 'severity', 'date', 'time', 'filename', 'category'
            database_client: Optional TursoClient for database matching
        """
        self.parent = parent
        self.error_data = error_data
        self.database_client = database_client
        self.matcher = DatabaseMatcher(database_client) if database_client else None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Error Analysis")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Create UI
        self._create_ui()
        
        # Perform database matching
        self._perform_matching()
        
        # Center the dialog
        self._center_dialog()
    
    def _create_ui(self):
        """Create the dialog UI"""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="🔍 Error Analysis",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Error Details Section
        details_frame = ttk.LabelFrame(main_frame, text="Error Details", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # Metadata grid
        metadata_frame = ttk.Frame(details_frame)
        metadata_frame.pack(fill=tk.X)
        
        row = 0
        # Severity
        if 'severity' in self.error_data:
            ttk.Label(metadata_frame, text="Severity:", font=("Arial", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
            )
            severity_color = self._get_severity_color(self.error_data.get('severity', ''))
            severity_label = ttk.Label(
                metadata_frame,
                text=self.error_data.get('severity', '').upper(),
                foreground=severity_color,
                font=("Arial", 9, "bold")
            )
            severity_label.grid(row=row, column=1, sticky=tk.W, pady=2)
            row += 1
        
        # Category
        if 'category' in self.error_data and self.error_data['category']:
            ttk.Label(metadata_frame, text="Category:", font=("Arial", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
            )
            ttk.Label(metadata_frame, text=self.error_data['category']).grid(
                row=row, column=1, sticky=tk.W, pady=2
            )
            row += 1
        
        # Date/Time
        if 'date' in self.error_data or 'time' in self.error_data:
            datetime_str = f"{self.error_data.get('date', '')} {self.error_data.get('time', '')}".strip()
            if datetime_str:
                ttk.Label(metadata_frame, text="Date/Time:", font=("Arial", 9, "bold")).grid(
                    row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
                )
                ttk.Label(metadata_frame, text=datetime_str).grid(
                    row=row, column=1, sticky=tk.W, pady=2
                )
                row += 1
        
        # Filename
        if 'filename' in self.error_data and self.error_data['filename']:
            ttk.Label(metadata_frame, text="File:", font=("Arial", 9, "bold")).grid(
                row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2
            )
            ttk.Label(metadata_frame, text=self.error_data['filename']).grid(
                row=row, column=1, sticky=tk.W, pady=2
            )
            row += 1
        
        # Error Text
        ttk.Label(details_frame, text="Error:", font=("Arial", 9, "bold")).pack(
            anchor=tk.W, pady=(10, 2)
        )
        error_text_widget = scrolledtext.ScrolledText(
            details_frame,
            height=3,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        error_text_widget.pack(fill=tk.X, pady=(0, 5))
        error_text_widget.insert(tk.END, self.error_data.get('error_text', 'N/A'))
        error_text_widget.config(state=tk.DISABLED)
        
        # Description (if different from error_text)
        if 'description' in self.error_data and self.error_data['description']:
            if self.error_data['description'] != self.error_data.get('error_text', ''):
                ttk.Label(details_frame, text="Description:", font=("Arial", 9, "bold")).pack(
                    anchor=tk.W, pady=(10, 2)
                )
                desc_widget = scrolledtext.ScrolledText(
                    details_frame,
                    height=3,
                    wrap=tk.WORD,
                    font=("Courier", 9)
                )
                desc_widget.pack(fill=tk.X, pady=(0, 5))
                desc_widget.insert(tk.END, self.error_data['description'])
                desc_widget.config(state=tk.DISABLED)
        
        # Database Match Section
        self.match_frame = ttk.LabelFrame(main_frame, text="Database Match", padding="10")
        self.match_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Match status (will be updated after matching)
        self.match_status_label = ttk.Label(
            self.match_frame,
            text="🔄 Searching database...",
            font=("Arial", 9, "italic")
        )
        self.match_status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Cause section (hidden initially)
        self.cause_label = ttk.Label(self.match_frame, text="Cause:", font=("Arial", 9, "bold"))
        self.cause_text = scrolledtext.ScrolledText(
            self.match_frame,
            height=4,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        
        # Solution section (hidden initially)
        self.solution_label = ttk.Label(self.match_frame, text="Solution:", font=("Arial", 9, "bold"))
        self.solution_text = scrolledtext.ScrolledText(
            self.match_frame,
            height=4,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        
        # Close button
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        close_button = ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy
        )
        close_button.pack(side=tk.RIGHT)
    
    def _perform_matching(self):
        """Perform database matching and update UI"""
        if not self.matcher:
            self._show_no_database()
            return
        
        error_text = self.error_data.get('error_text', '')
        error_type = self.error_data.get('type', '')
        
        # Perform matching
        match_result = self.matcher.match_error(error_text, error_type)
        
        if match_result:
            self._show_match(match_result)
        else:
            self._show_no_match()
    
    def _show_match(self, match_result: Dict[str, Any]):
        """Display matched database entry"""
        # Update status
        match_type = match_result.get('match_type', 'unknown')
        similarity = match_result.get('similarity', 0.0)
        
        status_text = f"✅ Match found ({match_type}"
        if match_type == 'fuzzy':
            status_text += f", {similarity:.1%} similarity"
        status_text += ")"
        
        self.match_status_label.config(
            text=status_text,
            foreground="green",
            font=("Arial", 9, "bold")
        )
        
        # Show cause
        cause = match_result.get('cause', '')
        if cause:
            self.cause_label.pack(anchor=tk.W, pady=(0, 2))
            self.cause_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self.cause_text.insert(tk.END, cause)
            self.cause_text.config(state=tk.DISABLED)
        
        # Show solution
        solution = match_result.get('solution', '')
        if solution:
            self.solution_label.pack(anchor=tk.W, pady=(0, 2))
            self.solution_text.pack(fill=tk.BOTH, expand=True)
            self.solution_text.insert(tk.END, solution)
            self.solution_text.config(state=tk.DISABLED)
        
        # If no cause or solution, show message
        if not cause and not solution:
            no_info_label = ttk.Label(
                self.match_frame,
                text="Match found, but no cause/solution information available.",
                font=("Arial", 9, "italic"),
                foreground="gray"
            )
            no_info_label.pack(anchor=tk.W, pady=(0, 10))
    
    def _show_no_match(self):
        """Display no match message"""
        self.match_status_label.config(
            text="❌ No match found in database",
            foreground="orange",
            font=("Arial", 9, "bold")
        )
        
        info_label = ttk.Label(
            self.match_frame,
            text="This error has not been documented in the database yet.",
            font=("Arial", 9, "italic"),
            foreground="gray"
        )
        info_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _show_no_database(self):
        """Display no database message"""
        self.match_status_label.config(
            text="⚠️ No database connection",
            foreground="gray",
            font=("Arial", 9, "bold")
        )
        
        info_label = ttk.Label(
            self.match_frame,
            text="Database matching is not available. Please configure a database connection.",
            font=("Arial", 9, "italic"),
            foreground="gray"
        )
        info_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level"""
        severity_lower = severity.lower()
        if severity_lower in ['fatal', 'critical', 'f', 'c']:
            return 'red'
        elif severity_lower in ['error', 'e']:
            return 'dark red'
        elif severity_lower in ['warning', 'warn', 'w']:
            return 'orange'
        else:
            return 'black'
    
    def _center_dialog(self):
        """Center the dialog on the screen"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
