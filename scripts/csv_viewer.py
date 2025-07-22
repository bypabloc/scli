#!/usr/bin/env python3
"""
CSV Viewer - Interactive CSV file viewer with filtering and column management
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import pandas as pd

# Add the src directory to path to import scli modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from scli.menu_utils import interactive_menu, text_input

try:
    from textual import on, events
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.widgets import Header, Footer, DataTable, Input, Button, Label, Static, Checkbox, LoadingIndicator
    from textual.screen import Screen
    from textual.reactive import reactive
    from textual.binding import Binding
    from textual.worker import Worker, get_current_worker
except ImportError:
    print("❌ Error: textual library is required for CSV viewer")
    print("Please install it with: pip install textual pandas")
    sys.exit(1)

DESCRIPTION = "Interactive CSV viewer with filtering and column management"


@dataclass
class CSVData:
    """Container for CSV data and metadata"""
    file_path: str
    separator: str
    total_rows: int
    columns: List[str]
    visible_columns: Set[str]
    page_size: int = 1000
    current_page: int = 0
    filtered_indices: Optional[List[int]] = None


class CSVViewerApp(App):
    """Main CSV Viewer Application"""
    
    CSS = """
    HeaderTitle:hover {
        background: $boost;
        text-style: underline;
    }
    
    Screen {
        background: $surface;
    }
    
    #sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
        padding: 1;
    }
    
    #main-content {
        padding: 1;
    }
    
    #filter-container {
        height: 3;
        margin-bottom: 1;
    }
    
    DataTable {
        height: 100%;
    }
    
    Input {
        margin-right: 1;
    }
    
    Label {
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .column-item {
        height: 1;
        margin-bottom: 1;
    }
    
    #loading-container {
        align: center middle;
        width: 100%;
        height: 100%;
    }
    
    #loading-label {
        text-align: center;
        margin-top: 2;
    }
    
    #pagination-container {
        height: 3;
        margin-top: 1;
        align: center middle;
    }
    
    #page-size-input {
        width: 8;
        margin-right: 1;
    }
    
    .hidden {
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+f", "focus_filter", "Filter"),
        Binding("ctrl+r", "reset_filter", "Reset Filter"),
        Binding("ctrl+h", "toggle_sidebar", "Toggle Sidebar"),
        Binding("f1", "show_help", "Help"),
    ]
    
    def __init__(self, csv_data: CSVData):
        super().__init__()
        self.csv_data = csv_data
        self.show_sidebar = True
        self.filter_text = ""
        self.loading = False
        self.encoding = 'utf-8'  # Store detected encoding
        
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        with Horizontal():
            # Sidebar for column management
            with Vertical(id="sidebar"):
                yield Label("📊 Columns")
                yield ScrollableContainer(id="column-list")
                yield Button("Show All", id="show-all-btn", variant="primary")
                yield Button("Hide All", id="hide-all-btn", variant="warning")
                
            # Main content area
            with Vertical(id="main-content"):
                # Filter input
                with Horizontal(id="filter-container"):
                    yield Input(
                        placeholder="Filter data (searches all visible columns)...",
                        id="filter-input"
                    )
                    yield Button("Filter", id="filter-btn", variant="primary")
                    yield Button("Clear", id="clear-btn")
                
                # Loading indicator (initially hidden)
                with Container(id="loading-container", classes="hidden"):
                    yield LoadingIndicator()
                    yield Label("Loading data...", id="loading-label")
                
                # Data table
                yield DataTable(id="data-table", zebra_stripes=True)
                
                # Pagination controls
                with Horizontal(id="pagination-container"):
                    yield Button("◀ Previous", id="prev-btn", disabled=True)
                    yield Label("Page 1 of 1", id="page-info")
                    yield Button("Next ▶", id="next-btn")
                    yield Label(" | ")
                    yield Label("Page size: ")
                    yield Input(value="1000", id="page-size-input", placeholder="Page size")
                    yield Button("Apply", id="apply-page-size-btn", variant="primary")
                
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize the app when mounted"""
        self.title = f"CSV Viewer - {Path(self.csv_data.file_path).name}"
        self.sub_title = f"Separator: '{self.csv_data.separator}' | Total Rows: {self.csv_data.total_rows:,}"
        
        # Show loading initially
        self._show_loading(True)
        
        # Load data asynchronously
        self.run_worker(self._initialize_data, thread=True)
        
    def _populate_column_list(self) -> None:
        """Populate the sidebar with column checkboxes"""
        column_container = self.query_one("#column-list")
        column_container.remove_children()
        
        for i, col in enumerate(self.csv_data.columns):
            # Use index to ensure unique IDs
            checkbox = Checkbox(
                col,
                value=col in self.csv_data.visible_columns,
                id=f"col-checkbox-{i}",
                classes="column-item"
            )
            column_container.mount(checkbox)
            
    def _refresh_table(self) -> None:
        """Refresh the data table with current data and visible columns"""
        self._show_loading(True)
        self.run_worker(self._refresh_table_worker, thread=True)
    
    def _refresh_table_worker(self) -> None:
        """Worker to refresh table data"""
        worker = get_current_worker()
        if not worker.is_cancelled:
            self.call_from_thread(self._update_table_content)
    
    def _update_table_content(self) -> None:
        """Update table content in main thread"""
        table = self.query_one("#data-table", DataTable)
        table.clear(columns=True)
        
        # Add only visible columns
        visible_cols = [col for col in self.csv_data.columns if col in self.csv_data.visible_columns]
        
        if not visible_cols:
            table.add_column("No columns selected")
            self._show_loading(False)
            return
            
        # Add columns
        for col in visible_cols:
            table.add_column(col, key=col)
            
        # Load page data from file
        page_data = self._load_page_data()
        
        if page_data:
            for row_data in page_data:
                table.add_row(*row_data)
        else:
            table.add_row(*["No data" for _ in visible_cols])
            
        # Update pagination info
        self._update_pagination_info()
        
        # Update subtitle with filtered count
        filter_info = ""
        if self.csv_data.filtered_indices is not None:
            filter_info = f" | Filtered: {len(self.csv_data.filtered_indices):,}"
        self.sub_title = f"Separator: '{self.csv_data.separator}' | Total Rows: {self.csv_data.total_rows:,}{filter_info}"
        
        self._show_loading(False)
    
    def _show_loading(self, show: bool) -> None:
        """Show or hide loading indicator"""
        loading_container = self.query_one("#loading-container")
        data_table = self.query_one("#data-table")
        
        if show:
            loading_container.remove_class("hidden")
            data_table.add_class("hidden")
        else:
            loading_container.add_class("hidden")
            data_table.remove_class("hidden")
    
    def _initialize_data(self) -> None:
        """Initialize data in background"""
        worker = get_current_worker()
        if not worker.is_cancelled:
            # Populate column list
            self.call_from_thread(self._populate_column_list)
            # Load data into table
            self.call_from_thread(self._update_table_content)
        
    @on(Checkbox.Changed)
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle column visibility toggle"""
        checkbox = event.checkbox
        col_name = checkbox.label
        
        if event.value:
            self.csv_data.visible_columns.add(col_name)
        else:
            self.csv_data.visible_columns.discard(col_name)
            
        self._refresh_table()
        
    @on(Button.Pressed, "#filter-btn")
    def on_filter_pressed(self) -> None:
        """Apply filter to data"""
        self._show_loading(True)
        self.run_worker(self._apply_filter_worker, thread=True)
    
    def _apply_filter_worker(self) -> None:
        """Worker to apply filter"""
        filter_input = self.query_one("#filter-input", Input)
        filter_text = filter_input.value.strip()
        
        if not filter_text:
            self.csv_data.filtered_indices = None
        else:
            # Filter by reading file in chunks
            filtered_indices = []
            visible_cols = [col for col in self.csv_data.columns if col in self.csv_data.visible_columns]
            
            if visible_cols:
                # Read file in chunks to find matching rows
                chunk_size = 10000
                for chunk_df in pd.read_csv(
                    self.csv_data.file_path, 
                    sep=self.csv_data.separator,
                    encoding=self.encoding,
                    chunksize=chunk_size
                ):
                    # Get the starting index for this chunk
                    start_idx = len(filtered_indices)
                    
                    # Apply filter to visible columns
                    mask = chunk_df[visible_cols].astype(str).apply(
                        lambda x: x.str.contains(filter_text, case=False, na=False)
                    ).any(axis=1)
                    
                    # Add matching indices
                    matching_indices = chunk_df.index[mask].tolist()
                    filtered_indices.extend([idx + start_idx for idx in matching_indices])
                
                self.csv_data.filtered_indices = filtered_indices if filtered_indices else []
            else:
                self.csv_data.filtered_indices = []
        
        # Reset to first page after filtering
        self.csv_data.current_page = 0
        self.call_from_thread(self._update_table_content)
        
    @on(Button.Pressed, "#clear-btn")
    def on_clear_pressed(self) -> None:
        """Clear the filter"""
        filter_input = self.query_one("#filter-input", Input)
        filter_input.value = ""
        self.csv_data.filtered_indices = None
        self.csv_data.current_page = 0
        self._refresh_table()
        
    @on(Button.Pressed, "#show-all-btn")
    def on_show_all_pressed(self) -> None:
        """Show all columns"""
        self.csv_data.visible_columns = set(self.csv_data.columns)
        self._populate_column_list()
        self._refresh_table()
        
    @on(Button.Pressed, "#hide-all-btn")
    def on_hide_all_pressed(self) -> None:
        """Hide all columns"""
        self.csv_data.visible_columns = set()
        self._populate_column_list()
        self._refresh_table()
        
    @on(Input.Submitted, "#filter-input")
    def on_filter_submitted(self) -> None:
        """Apply filter when Enter is pressed in filter input"""
        self.on_filter_pressed()
        
    def action_focus_filter(self) -> None:
        """Focus the filter input"""
        self.query_one("#filter-input", Input).focus()
        
    def action_reset_filter(self) -> None:
        """Reset all filters"""
        self.on_clear_pressed()
        
    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        sidebar = self.query_one("#sidebar")
        sidebar.display = not sidebar.display
        
    def action_show_help(self) -> None:
        """Show help message"""
        self.notify(
            "Keyboard Shortcuts:\n"
            "Ctrl+Q: Quit | Ctrl+F: Focus Filter | Ctrl+R: Reset Filter\n"
            "Ctrl+H: Toggle Sidebar | F1: This Help",
            title="CSV Viewer Help",
            timeout=5
        )
    
    def _load_page_data(self) -> List[List[str]]:
        """Load data for current page from file"""
        visible_cols = [col for col in self.csv_data.columns if col in self.csv_data.visible_columns]
        if not visible_cols:
            return []
        
        # Calculate skip rows and nrows
        if self.csv_data.filtered_indices is not None:
            # For filtered data, we need to read specific rows
            total_filtered = len(self.csv_data.filtered_indices)
            if total_filtered == 0:
                return []
            
            start_idx = self.csv_data.current_page * self.csv_data.page_size
            end_idx = min(start_idx + self.csv_data.page_size, total_filtered)
            
            if start_idx >= total_filtered:
                return []
            
            # Get the actual row indices to read
            rows_to_read = self.csv_data.filtered_indices[start_idx:end_idx]
            
            # Read specific rows using skiprows
            all_rows = set(range(self.csv_data.total_rows))
            skip_rows = all_rows - set(rows_to_read) - {0}  # Don't skip header
            
            try:
                df = pd.read_csv(
                    self.csv_data.file_path,
                    sep=self.csv_data.separator,
                    encoding=self.encoding,
                    skiprows=skip_rows,
                    usecols=visible_cols
                )
                
                # Convert to list of lists
                return df.astype(str).values.tolist()
            except Exception as e:
                print(f"Error loading filtered page: {e}")
                return []
        else:
            # For unfiltered data, use simple skip and nrows
            skip_rows = 1 + (self.csv_data.current_page * self.csv_data.page_size)  # +1 for header
            
            try:
                df = pd.read_csv(
                    self.csv_data.file_path,
                    sep=self.csv_data.separator,
                    encoding=self.encoding,
                    skiprows=skip_rows,
                    nrows=self.csv_data.page_size,
                    usecols=visible_cols,
                    header=None,
                    names=visible_cols
                )
                
                # Convert to list of lists
                return df.astype(str).values.tolist()
            except Exception as e:
                print(f"Error loading page: {e}")
                return []
    
    def _update_pagination_info(self) -> None:
        """Update pagination controls and info"""
        # Calculate total pages
        if self.csv_data.filtered_indices is not None:
            total_rows = len(self.csv_data.filtered_indices)
        else:
            total_rows = self.csv_data.total_rows
        
        total_pages = max(1, (total_rows + self.csv_data.page_size - 1) // self.csv_data.page_size)
        current_page = self.csv_data.current_page + 1
        
        # Update page info label
        page_info = self.query_one("#page-info", Label)
        page_info.update(f"Page {current_page} of {total_pages}")
        
        # Update button states
        prev_btn = self.query_one("#prev-btn", Button)
        next_btn = self.query_one("#next-btn", Button)
        
        prev_btn.disabled = self.csv_data.current_page == 0
        next_btn.disabled = current_page >= total_pages
    
    @on(Button.Pressed, "#prev-btn")
    def on_prev_page(self) -> None:
        """Go to previous page"""
        if self.csv_data.current_page > 0:
            self.csv_data.current_page -= 1
            self._refresh_table()
    
    @on(Button.Pressed, "#next-btn")
    def on_next_page(self) -> None:
        """Go to next page"""
        # Calculate total pages
        if self.csv_data.filtered_indices is not None:
            total_rows = len(self.csv_data.filtered_indices)
        else:
            total_rows = self.csv_data.total_rows
        
        total_pages = max(1, (total_rows + self.csv_data.page_size - 1) // self.csv_data.page_size)
        
        if self.csv_data.current_page < total_pages - 1:
            self.csv_data.current_page += 1
            self._refresh_table()
    
    @on(Button.Pressed, "#apply-page-size-btn")
    def on_apply_page_size(self) -> None:
        """Apply new page size"""
        page_size_input = self.query_one("#page-size-input", Input)
        try:
            new_size = int(page_size_input.value)
            if new_size > 0 and new_size <= 10000:
                self.csv_data.page_size = new_size
                self.csv_data.current_page = 0
                self._refresh_table()
            else:
                self.notify("Page size must be between 1 and 10000", severity="warning")
        except ValueError:
            self.notify("Invalid page size", severity="error")
    
    def on_click(self, event: events.Click) -> None:
        """Handle clicks on the header title"""
        # Check if click is on header area
        if event.y <= 2:  # Header is typically 2 rows high
            self.notify(
                f"Full path:\n{self.csv_data.file_path}",
                title="File Location",
                timeout=10
            )


def select_csv_file() -> Optional[str]:
    """Interactive file browser to select CSV file"""
    current_dir = os.getcwd()
    
    while True:
        items = []
        
        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):
            items.append({
                'name': '📁 ..',
                'value': '..',
                'description': 'Parent directory',
                'type': 'parent'
            })
        
        # List directories and CSV files
        try:
            entries = sorted(os.listdir(current_dir))
            
            # Add directories first
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    items.append({
                        'name': f'📁 {entry}',
                        'value': entry,
                        'description': 'Directory',
                        'type': 'dir'
                    })
            
            # Add CSV files
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith('.csv'):
                    try:
                        file_size = os.path.getsize(full_path)
                        size_str = format_file_size(file_size)
                        items.append({
                            'name': f'📄 {entry}',
                            'value': entry,
                            'description': f'CSV File ({size_str})',
                            'type': 'file'
                        })
                    except:
                        pass
            
            # Add options
            items.extend([
                {
                    'name': '✏️  Enter path manually',
                    'value': 'manual',
                    'description': 'Type the full file path',
                    'type': 'manual'
                },
                {
                    'name': '❌ Cancel',
                    'value': 'cancel',
                    'description': 'Cancel file selection',
                    'type': 'cancel'
                }
            ])
            
            # Show current directory
            print(f"\n📂 Current directory: {current_dir}")
            
            # Show menu
            selected = interactive_menu("Select CSV file:", items)
            
            if not selected or selected['type'] == 'cancel':
                return None
            
            if selected['type'] == 'manual':
                manual_path = text_input("Enter full path to CSV file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if os.path.exists(manual_path) and manual_path.lower().endswith('.csv'):
                        return os.path.abspath(manual_path)
                    else:
                        print("❌ Invalid CSV file path")
                        continue
            
            elif selected['type'] == 'parent':
                current_dir = os.path.dirname(current_dir)
            
            elif selected['type'] == 'dir':
                current_dir = os.path.join(current_dir, selected['value'])
            
            elif selected['type'] == 'file':
                return os.path.abspath(os.path.join(current_dir, selected['value']))
                
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def detect_separator(file_path: str, sample_size: int = 5) -> str:
    """Try to detect CSV separator automatically"""
    common_separators = [',', ';', '\t', '|']
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sample_lines = [f.readline() for _ in range(sample_size)]
        
        # Count occurrences of each separator
        separator_counts = {}
        for sep in common_separators:
            counts = [line.count(sep) for line in sample_lines if line]
            if counts and all(c == counts[0] for c in counts) and counts[0] > 0:
                separator_counts[sep] = counts[0]
        
        if separator_counts:
            # Return separator with most consistent count
            return max(separator_counts.items(), key=lambda x: x[1])[0]
    except:
        pass
    
    return ','  # Default to comma


def load_csv_file(file_path: str, separator: str) -> Optional[CSVData]:
    """Load CSV file metadata and return CSVData object"""
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        encoding_used = None
        columns = None
        total_rows = 0
        
        for encoding in encodings:
            try:
                # Just read the header and count rows
                with open(file_path, 'r', encoding=encoding) as f:
                    # Read header
                    header_line = f.readline().strip()
                    columns = header_line.split(separator)
                    
                    # Count remaining rows
                    total_rows = sum(1 for _ in f)
                
                encoding_used = encoding
                print(f"✅ File loaded with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if encoding_used is None or columns is None:
            print("❌ Could not decode file with any supported encoding")
            return None
        
        # Create CSVData without loading all data
        csv_data = CSVData(
            file_path=file_path,
            separator=separator,
            total_rows=total_rows,
            columns=columns,
            visible_columns=set(columns)
        )
        
        # Store encoding for later use
        return csv_data, encoding_used
        
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return None


def main():
    """Main entry point for CSV viewer"""
    print("📊 CSV Viewer")
    print("=" * 50)
    
    # Select CSV file
    csv_file = select_csv_file()
    if not csv_file:
        print("❌ No file selected")
        return
    
    print(f"\n✅ Selected file: {csv_file}")
    
    # Detect separator
    detected_sep = detect_separator(csv_file)
    print(f"🔍 Detected separator: '{detected_sep}'")
    
    # Ask user to confirm or change separator
    separator = text_input(
        f"Enter CSV separator (detected: '{detected_sep}'):",
        default=detected_sep
    )
    if not separator:
        separator = detected_sep
    
    # Load CSV file
    print(f"\n📂 Loading CSV file...")
    result = load_csv_file(csv_file, separator)
    
    if not result:
        return
    
    csv_data, encoding = result
    
    print(f"✅ Loaded {csv_data.total_rows:,} rows and {len(csv_data.columns)} columns")
    print(f"\n🚀 Starting interactive viewer...")
    print("💡 Press Ctrl+Q to quit, F1 for help, click title for full path")
    
    # Run the app
    app = CSVViewerApp(csv_data)
    app.encoding = encoding  # Store encoding
    app.run()


if __name__ == "__main__":
    main()