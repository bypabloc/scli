#!/usr/bin/env python3
"""
COBOL Utilities - COBOL file processing functionality
"""

import csv
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from utils.menu_utils import confirm, interactive_menu, text_input
    from output_manager import OutputManager
except ImportError:
    # Fallback for standalone usage
    pass


@dataclass
class CobolField:
    """Represents a COBOL field definition"""

    level: int
    name: str
    picture: Optional[str]
    start_pos: int
    length: int
    field_type: str  # 'numeric', 'alphanumeric', 'group'
    children: List["CobolField"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


def select_and_process_files():
    """Allow user to manually select .cpy and .txt files"""
    print("📂 File Selection Mode")
    print("-" * 30)

    cpy_file = None
    txt_file = None

    # Get .cpy file path with browser
    print("\n📄 Select .cpy file:")
    cpy_file = browse_for_file(".cpy", "Select COBOL copybook file (.cpy)")
    if not cpy_file:
        print("❌ CPY file selection cancelled")
        return
    print(f"✅ CPY file selected: {cpy_file}")

    # Get .txt file path with browser
    print("\n📄 Select .txt file:")
    # Start browsing from the same directory as the .cpy file
    start_dir = os.path.dirname(cpy_file) if cpy_file else None
    txt_file = browse_for_file(".txt", "Select data file (.txt)", start_dir)
    if not txt_file:
        print("❌ TXT file selection cancelled")
        return
    print(f"✅ TXT file selected: {txt_file}")

    # Process the selected files
    if cpy_file and txt_file:
        process_files(cpy_file, txt_file)


def browse_directory_files():
    """Browse directory and let user select files"""
    print("📁 Directory Browse Mode")
    print("-" * 30)

    directory = text_input("Enter directory path to scan:")
    if not directory or not directory.strip():
        print("❌ Directory path is required")
        return

    directory = directory.strip()

    # Validate directory
    if not os.path.exists(directory):
        print(f"❌ Directory does not exist: {directory}")
        return

    if not os.path.isdir(directory):
        print(f"❌ Path is not a directory: {directory}")
        return

    # Scan for files
    cpy_files, txt_files = scan_directory_for_files(directory)

    if not cpy_files and not txt_files:
        print(f"❌ No .cpy or .txt files found in: {directory}")
        return

    print(f"\n📊 Files found in {directory}:")
    if cpy_files:
        print(f"   📄 .cpy files: {len(cpy_files)}")
        for file in cpy_files:
            size_str = format_file_size(os.path.getsize(file))
            print(f"     • {os.path.basename(file)} ({size_str})")

    if txt_files:
        print(f"   📄 .txt files: {len(txt_files)}")
        for file in txt_files:
            size_str = format_file_size(os.path.getsize(file))
            print(f"     • {os.path.basename(file)} ({size_str})")

    if not cpy_files:
        print("❌ No .cpy files found. Cannot process without copybook.")
        return

    if not txt_files:
        print("❌ No .txt files found. Cannot process without data file.")
        return

    # Let user select files
    if len(cpy_files) == 1 and len(txt_files) == 1:
        # Only one of each, auto-select
        cpy_file = cpy_files[0]
        txt_file = txt_files[0]
        print(f"\n🎯 Auto-selecting:")
        print(f"   CPY: {os.path.basename(cpy_file)}")
        print(f"   TXT: {os.path.basename(txt_file)}")
        process_files(cpy_file, txt_file)
    else:
        # Multiple files, let user choose
        cpy_file = select_file_from_list(cpy_files, ".cpy")
        if not cpy_file:
            return

        txt_file = select_file_from_list(txt_files, ".txt")
        if not txt_file:
            return

        process_files(cpy_file, txt_file)


def scan_directory_for_files(directory: str) -> Tuple[List[str], List[str]]:
    """Scan directory for .cpy and .txt files"""
    cpy_files = []
    txt_files = []

    try:
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path):
                if entry.lower().endswith(".cpy"):
                    cpy_files.append(full_path)
                elif entry.lower().endswith(".txt"):
                    txt_files.append(full_path)
    except PermissionError:
        print(f"❌ Permission denied accessing directory: {directory}")
    except Exception as e:
        print(f"❌ Error scanning directory: {e}")

    return sorted(cpy_files), sorted(txt_files)


def validate_file_path(file_path: str, expected_extension: str) -> bool:
    """Validate that file exists and has expected extension"""
    if not os.path.exists(file_path):
        print(f"❌ File does not exist: {file_path}")
        return False

    if not os.path.isfile(file_path):
        print(f"❌ Path is not a file: {file_path}")
        return False

    if not file_path.lower().endswith(expected_extension.lower()):
        print(f"❌ Expected {expected_extension} file, got: {file_path}")
        return False

    return True


def process_files(cpy_file: str, txt_file: str):
    """Process COBOL copybook and data files"""
    print("\n🔄 Processing Files")
    print("=" * 50)

    # Validate files
    if not validate_file_path(cpy_file, ".cpy"):
        return
    if not validate_file_path(txt_file, ".txt"):
        return

    # Parse copybook
    print(f"📖 Parsing copybook: {os.path.basename(cpy_file)}")
    try:
        cobol_fields = parse_cobol_copybook(cpy_file)
        if not cobol_fields:
            print("❌ No fields found in copybook")
            return
        print(f"✅ Parsed {len(cobol_fields)} fields from copybook")
    except Exception as e:
        print(f"❌ Error parsing copybook: {e}")
        return

    # Display structure
    print("\n📋 COBOL Structure:")
    display_cobol_structure(cobol_fields)

    # Ask user if they want to proceed
    if not confirm("\nProceed with data processing?", default=True):
        print("❌ Processing cancelled")
        return

    # Parse data file
    print(f"\n📄 Processing data file: {os.path.basename(txt_file)}")
    try:
        parse_data_file(txt_file, cobol_fields)
        print("✅ Data processing completed!")
    except Exception as e:
        print(f"❌ Error processing data file: {e}")
        return


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def parse_cobol_copybook(cpy_file: str) -> List[CobolField]:
    """Parse COBOL copybook (.cpy) file and extract field definitions"""
    fields = []
    current_pos = 1

    try:
        with open(cpy_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # Try with latin-1 encoding
        with open(cpy_file, "r", encoding="latin-1") as file:
            lines = file.readlines()

    for line_num, line in enumerate(lines, 1):
        # Remove comments (anything after asterisk in column 7)
        if len(line) > 6 and line[6] == "*":
            continue

        # Skip empty lines
        if not line.strip():
            continue

        # Parse field definition
        field = parse_cobol_line(line, current_pos)
        if field:
            fields.append(field)
            if field.field_type != "group":
                current_pos += field.length

    return fields


def parse_cobol_line(line: str, current_pos: int) -> Optional[CobolField]:
    """Parse a single line from COBOL copybook"""
    # COBOL line format: columns 1-6 are sequence numbers, 7 is indicator, 8-72 is content

    # Extract content area (columns 8-72)
    if len(line) < 8:
        return None

    content = line[7:72] if len(line) >= 72 else line[7:]
    content = content.rstrip()

    if not content.strip():
        return None

    # Match field definition pattern
    # Format: level-number field-name [PIC picture] [other-clauses].
    pattern = r"^\s*(\d{2})\s+([A-Z0-9\-_]+)(?:\s+PIC\s+([X9VS\(\)]+))?.*$"
    match = re.match(pattern, content, re.IGNORECASE)

    if not match:
        return None

    level = int(match.group(1))
    name = match.group(2).strip()
    picture = match.group(3).strip() if match.group(3) else None

    if picture:
        length, field_type = parse_picture_clause(picture)
    else:
        # Group item (no PIC clause)
        length = 0
        field_type = "group"

    return CobolField(
        level=level,
        name=name,
        picture=picture,
        start_pos=current_pos,
        length=length,
        field_type=field_type,
    )


def parse_picture_clause(picture: str) -> Tuple[int, str]:
    """Parse COBOL PIC clause to determine field length and type"""
    picture = picture.upper().strip()
    length = 0
    field_type = "alphanumeric"

    # Remove parentheses and extract repeat count
    # Handle formats like X(10), 9(5), S9(7)V99
    if "(" in picture and ")" in picture:
        # Extract content within parentheses
        pattern = r"([X9VS]+)\((\d+)\)([X9VS]*)"
        match = re.match(pattern, picture)
        if match:
            prefix = match.group(1)
            count = int(match.group(2))
            suffix = match.group(3) if match.group(3) else ""

            # Calculate length based on prefix and count
            length = count

            # Add suffix length
            for char in suffix:
                if char in "X9":
                    length += 1

            # Determine type
            if any(c in picture for c in "9SV"):
                field_type = "numeric"
            else:
                field_type = "alphanumeric"
        else:
            # Handle simple patterns without parentheses
            for char in picture:
                if char in "X9SV":
                    length += 1
    else:
        # Handle simple patterns like XXX, 999, etc.
        for char in picture:
            if char in "X9":
                length += 1

        # Determine type
        if any(c in picture for c in "9SV"):
            field_type = "numeric"

    # Handle special cases
    if "V" in picture:
        # V indicates decimal position but doesn't add to length
        field_type = "numeric"

    if "S" in picture:
        # S indicates signed but doesn't add to length in display format
        field_type = "numeric"

    return length, field_type


def display_cobol_structure(fields: List[CobolField]):
    """Display the parsed COBOL structure"""
    print("Level | Name                     | Picture    | Position | Length | Type")
    print("-" * 75)

    for field in fields:
        pic_str = field.picture if field.picture else "-"
        pos_str = f"{field.start_pos}-{field.start_pos + field.length - 1}" if field.length > 0 else "-"
        print(
            f"{field.level:5d} | {field.name:24s} | {pic_str:10s} | {pos_str:8s} | {field.length:6d} | {field.field_type:12s}"
        )


def parse_data_file(txt_file: str, fields: List[CobolField]):
    """Parse data file using COBOL field definitions"""
    record_count = 0
    error_count = 0
    sample_records = []

    # Determine record types (if any level 88 items exist)
    record_types = {}

    try:
        # Try UTF-8 first
        with open(txt_file, "r", encoding="utf-8") as file:
            lines = file.readlines()
    except UnicodeDecodeError:
        # Fall back to latin-1
        with open(txt_file, "r", encoding="latin-1") as file:
            lines = file.readlines()

    print(f"📊 Total lines to process: {len(lines)}")

    # Show processing progress
    show_progress = len(lines) > 1000

    for line_num, line in enumerate(lines, 1):
        if show_progress and line_num % 1000 == 0:
            print(f"   Processing line {line_num:,}...")

        line = line.rstrip("\n\r")  # Remove line endings but keep spaces
        record_count += 1

        try:
            # Parse record according to COBOL structure
            record = parse_record(line, fields)
            
            # Store first 5 records as samples
            if len(sample_records) < 5:
                sample_records.append(record)

            # Detect record type if applicable
            if record_types:
                record_type = detect_record_type(line, record_types)
                record["_RECORD_TYPE"] = record_type

        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Only show first 10 errors
                print(f"❌ Error processing line {line_num}: {e}")

    # Show summary
    print(f"\n📊 Processing Summary:")
    print(f"   Total records: {record_count:,}")
    print(f"   Errors: {error_count:,}")
    print(f"   Success rate: {((record_count - error_count) / record_count * 100):.1f}%")

    if sample_records:
        print(f"\n📋 Sample Records (first {len(sample_records)}):")
        for i, record in enumerate(sample_records, 1):
            print(f"\n--- Record {i} ---")
            for field_name, value in record.items():
                print(f"  {field_name}: {value}")

    # Ask if user wants to export to CSV
    if record_count > 0 and confirm("\nExport all records to CSV?", default=True):
        export_to_csv(txt_file, fields, lines)


def parse_record(line: str, fields: List[CobolField]) -> Dict[str, Any]:
    """Parse a single record according to COBOL field definitions"""
    record = {}

    for field in fields:
        if field.field_type == "group":
            continue  # Skip group items

        start_pos = field.start_pos - 1  # Convert to 0-based index
        end_pos = start_pos + field.length

        if start_pos >= len(line):
            value = ""  # Field is beyond line length
        elif end_pos > len(line):
            value = line[start_pos:].ljust(field.length)  # Pad with spaces
        else:
            value = line[start_pos:end_pos]

        # Format based on field type
        if field.field_type == "numeric":
            formatted_value = format_numeric_field(value, field.picture or "")
            record[field.name] = formatted_value
        else:
            record[field.name] = value.rstrip()  # Remove trailing spaces for alphanumeric

    return record


def detect_record_type(line: str, record_types: Dict[str, Any]) -> str:
    """Detect record type based on indicator fields"""
    # This would be implemented based on specific level 88 items in the copybook
    # For now, return a default type
    return "DEFAULT"


def format_numeric_field(value: str, picture: str) -> str:
    """Format numeric field according to COBOL picture"""
    value = value.strip()

    if not value or value.isspace():
        return "0"

    # Handle signed fields
    if "S" in picture.upper():
        # Check for trailing sign (COBOL display format)
        if value and value[-1] in "ABCDEFGHI}":
            # Positive overpunch
            last_char = value[-1]
            digit_map = {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5",
                        "F": "6", "G": "7", "H": "8", "I": "9", "}": "0"}
            value = value[:-1] + digit_map.get(last_char, "0")
        elif value and value[-1] in "JKLMNOPQR{":
            # Negative overpunch
            last_char = value[-1]
            digit_map = {"J": "1", "K": "2", "L": "3", "M": "4", "N": "5",
                        "O": "6", "P": "7", "Q": "8", "R": "9", "{": "0"}
            value = "-" + value[:-1] + digit_map.get(last_char, "0")

    # Handle decimal point
    if "V" in picture.upper():
        # Find decimal position
        v_pos = picture.upper().find("V")
        decimal_places = len([c for c in picture[v_pos+1:] if c in "9"])
        if decimal_places > 0:
            if len(value) > decimal_places:
                integer_part = value[:-decimal_places]
                decimal_part = value[-decimal_places:]
                value = f"{integer_part}.{decimal_part}"

    return value


def export_to_csv(txt_file: str, fields: List[CobolField], lines: List[str]):
    """Export parsed records to CSV file"""
    # Generate output filename
    output_manager = OutputManager()
    base_name = os.path.splitext(os.path.basename(txt_file))[0]
    csv_filename = f"{base_name}_parsed.csv"
    csv_file = output_manager.get_output_path("cobol_processor", csv_filename)

    # Get field names (excluding group items)
    field_names = [field.name for field in fields if field.field_type != "group"]

    try:
        with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()

            processed_count = 0
            error_count = 0

            for line_num, line in enumerate(lines, 1):
                try:
                    line = line.rstrip("\n\r")
                    record = parse_record(line, fields)

                    # Filter to only include non-group fields
                    csv_record = {name: record.get(name, "") for name in field_names}
                    writer.writerow(csv_record)
                    processed_count += 1

                    # Show progress for large files
                    if processed_count % 10000 == 0:
                        print(f"   Exported {processed_count:,} records...")

                except Exception as e:
                    error_count += 1
                    if error_count <= 5:  # Only show first 5 errors
                        print(f"❌ Export error on line {line_num}: {e}")

        print(f"✅ Export completed!")
        print(f"   Records exported: {processed_count:,}")
        print(f"   Export errors: {error_count:,}")
        print(f"   Output file: {csv_file}")

        # Show file size
        file_size = format_file_size(os.path.getsize(csv_file))
        print(f"   File size: {file_size}")

    except Exception as e:
        print(f"❌ CSV export failed: {e}")


def browse_for_file(
    extension: str, title: str, start_dir: Optional[str] = None
) -> Optional[str]:
    """Browse for file with specific extension using interactive menu"""
    current_dir = start_dir if start_dir else os.getcwd()

    while True:
        items = []

        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):
            items.append(
                {
                    "name": "📁 ..",
                    "value": "..",
                    "description": "Parent directory",
                    "type": "parent",
                }
            )

        try:
            entries = sorted(os.listdir(current_dir))

            # Add directories first
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isdir(full_path):
                    items.append(
                        {
                            "name": f"📁 {entry}",
                            "value": entry,
                            "description": "Directory",
                            "type": "dir",
                        }
                    )

            # Add files with target extension
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith(
                    extension.lower()
                ):
                    file_size = format_file_size(os.path.getsize(full_path))
                    items.append(
                        {
                            "name": f"📄 {entry}",
                            "value": entry,
                            "description": f"{extension.upper()} File ({file_size})",
                            "type": "file",
                        }
                    )

            # Add manual entry and cancel options
            items.extend(
                [
                    {
                        "name": "✏️  Enter path manually",
                        "value": "manual",
                        "description": f"Type full path to {extension} file",
                        "type": "manual",
                    },
                    {
                        "name": "❌ Cancel",
                        "value": "cancel",
                        "description": "Cancel file selection",
                        "type": "cancel",
                    },
                ]
            )

            # Show current directory and menu
            print(f"\n📂 Current directory: {current_dir}")
            selected = interactive_menu(title, items)

            if not selected or selected["type"] == "cancel":
                return None

            if selected["type"] == "manual":
                manual_path = text_input(f"Enter full path to {extension} file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if os.path.exists(manual_path) and manual_path.lower().endswith(
                        extension.lower()
                    ):
                        return os.path.abspath(manual_path)
                    else:
                        print(f"❌ Invalid {extension} file: {manual_path}")
                        continue

            elif selected["type"] == "parent":
                current_dir = os.path.dirname(current_dir)

            elif selected["type"] == "dir":
                current_dir = os.path.join(current_dir, selected["value"])

            elif selected["type"] == "file":
                file_path = os.path.join(current_dir, selected["value"])
                return os.path.abspath(file_path)

        except PermissionError:
            print(f"❌ Permission denied: {current_dir}")
            current_dir = os.path.dirname(current_dir)
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


def select_file_from_list(files: List[str], extension: str) -> Optional[str]:
    """Let user select from a list of files"""
    items = []

    for file in files:
        file_size = format_file_size(os.path.getsize(file))
        items.append(
            {
                "name": f"📄 {os.path.basename(file)}",
                "value": file,
                "description": f"{extension.upper()} File ({file_size})",
            }
        )

    items.append(
        {"name": "❌ Cancel", "value": None, "description": "Cancel selection"}
    )

    selected = interactive_menu(f"Select {extension} file:", items)
    return selected["value"] if selected else None