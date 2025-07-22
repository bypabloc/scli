import os
import sys
import re
import csv
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Add the src directory to path to import scli modules  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from scli.menu_utils import interactive_menu, text_input, confirm
from scli.output_manager import OutputManager

DESCRIPTION = "COBOL file processor - Process .cpy and .txt files to interpret data"


@dataclass
class CobolField:
    """Represents a COBOL field definition"""
    level: int
    name: str
    picture: Optional[str]
    start_pos: int
    length: int
    field_type: str  # 'numeric', 'alphanumeric', 'group'
    children: List['CobolField'] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


def main():
    print("🏢 COBOL File Processor")
    print("=" * 50)
    
    # Define menu options
    menu_options = [
        {
            'name': '📂 Select files to process',
            'value': 'select_files',
            'description': 'Choose .cpy and .txt files for processing',
            'action': select_and_process_files
        },
        {
            'name': '📁 Browse directory for COBOL files',
            'value': 'browse_directory', 
            'description': 'Scan directory for .cpy and .txt files',
            'action': browse_directory_files
        },
        {
            'name': '👋 Exit',
            'value': 'exit',
            'description': 'Quit the COBOL processor',
            'action': None
        }
    ]
    
    while True:
        try:
            print("\n" + "=" * 50)
            selected = interactive_menu("Select an option:", menu_options)
            
            if not selected or selected['value'] == 'exit':
                print("👋 Goodbye!")
                break
                
            # Execute the selected action
            if selected['action']:
                print(f"\n🔧 Running: {selected['name']}")
                print("-" * 40)
                selected['action']()
                
                # Ask if user wants to continue
                if not confirm("\nWould you like to perform another action?", default=True):
                    print("👋 Goodbye!")
                    break
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            if not confirm("Would you like to continue?", default=True):
                break


def select_and_process_files():
    """Allow user to manually select .cpy and .txt files"""
    print("📂 File Selection Mode")
    print("-" * 30)
    
    cpy_file = None
    txt_file = None
    
    # Get .cpy file path with browser
    print("\n📄 Select .cpy file:")
    cpy_file = browse_for_file('.cpy', "Select COBOL copybook file (.cpy)")
    if not cpy_file:
        print("❌ CPY file selection cancelled")
        return
    print(f"✅ CPY file selected: {cpy_file}")
    
    # Get .txt file path with browser
    print("\n📄 Select .txt file:")
    # Start browsing from the same directory as the .cpy file
    start_dir = os.path.dirname(cpy_file) if cpy_file else None
    txt_file = browse_for_file('.txt', "Select data file (.txt)", start_dir)
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
        print(f"  📄 .cpy files: {len(cpy_files)}")
    if txt_files:
        print(f"  📄 .txt files: {len(txt_files)}")
    
    # Select .cpy file
    cpy_file = None
    if cpy_files:
        if len(cpy_files) == 1:
            cpy_file = cpy_files[0]
            print(f"✅ Auto-selected CPY file: {os.path.basename(cpy_file)}")
        else:
            cpy_choices = [{'name': os.path.basename(f), 'value': f, 'description': f} for f in cpy_files]
            selected_cpy = interactive_menu("Select a .cpy file:", cpy_choices)
            if selected_cpy:
                cpy_file = selected_cpy['value']
                print(f"✅ Selected CPY file: {os.path.basename(cpy_file)}")
    
    # Select .txt file  
    txt_file = None
    if txt_files:
        if len(txt_files) == 1:
            txt_file = txt_files[0]
            print(f"✅ Auto-selected TXT file: {os.path.basename(txt_file)}")
        else:
            txt_choices = [{'name': os.path.basename(f), 'value': f, 'description': f} for f in txt_files]
            selected_txt = interactive_menu("Select a .txt file:", txt_choices)
            if selected_txt:
                txt_file = selected_txt['value']
                print(f"✅ Selected TXT file: {os.path.basename(txt_file)}")
    
    # Process files if both are selected
    if cpy_file and txt_file:
        process_files(cpy_file, txt_file)
    elif cpy_file and not txt_files:
        print("⚠️  Only .cpy file available, .txt file needed for processing")
    elif txt_file and not cpy_files:
        print("⚠️  Only .txt file available, .cpy file needed for processing")
    else:
        print("❌ Both .cpy and .txt files are required for processing")


def scan_directory_for_files(directory: str) -> Tuple[List[str], List[str]]:
    """Scan directory for .cpy and .txt files"""
    cpy_files = []
    txt_files = []
    
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.cpy'):
                    cpy_files.append(file_path)
                elif file.lower().endswith('.txt'):
                    txt_files.append(file_path)
    except Exception as e:
        print(f"❌ Error scanning directory: {e}")
    
    # Sort files for consistent ordering
    cpy_files.sort()
    txt_files.sort()
    
    return cpy_files, txt_files


def validate_file_path(file_path: str, expected_extension: str) -> bool:
    """Validate file path exists and has correct extension"""
    if not os.path.exists(file_path):
        print(f"❌ File does not exist: {file_path}")
        return False
        
    if not os.path.isfile(file_path):
        print(f"❌ Path is not a file: {file_path}")
        return False
        
    if not file_path.lower().endswith(expected_extension.lower()):
        print(f"❌ File does not have {expected_extension} extension: {file_path}")
        return False
        
    return True


def process_files(cpy_file: str, txt_file: str):
    """Process the selected .cpy and .txt files"""
    print(f"\n🔄 Processing Files")
    print("=" * 30)
    
    print(f"📄 CPY File: {cpy_file}")
    print(f"📄 TXT File: {txt_file}")
    
    # For now, just print the paths as requested
    print(f"\n📋 Selected Files:")
    print(f"  • CPY File Path: {os.path.abspath(cpy_file)}")
    print(f"  • TXT File Path: {os.path.abspath(txt_file)}")
    
    # Get file sizes
    try:
        cpy_size = os.path.getsize(cpy_file)
        txt_size = os.path.getsize(txt_file)
        
        print(f"\n📊 File Information:")
        print(f"  • CPY File Size: {format_file_size(cpy_size)}")
        print(f"  • TXT File Size: {format_file_size(txt_size)}")
        
        print(f"\n✅ Files ready for processing!")
        
        # Parse COBOL copybook structure
        print(f"\n🔍 Parsing COBOL copybook structure...")
        fields = parse_cobol_copybook(cpy_file)
        
        if fields:
            print(f"📋 Found {len(fields)} field definitions:")
            display_cobol_structure(fields)
            
            # Parse data file using the structure
            if confirm("\nWould you like to parse the data file using this structure?", default=True):
                print(f"\n🔄 Parsing data file...")
                parsed_records = parse_data_file(txt_file, fields)
                
                # Offer CSV export
                if parsed_records and confirm("\nWould you like to export the data to CSV?", default=True):
                    export_to_csv(parsed_records, fields, txt_file)
        else:
            print("❌ Could not parse COBOL copybook structure")
        
    except Exception as e:
        print(f"❌ Error processing files: {e}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(size_units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {size_units[unit_index]}"
    else:
        return f"{size:.1f} {size_units[unit_index]}"


def parse_cobol_copybook(cpy_file: str) -> List[CobolField]:
    """Parse COBOL copybook and extract field definitions with REDEFINES support"""
    fields = []
    current_position = 1
    current_group_start = 1  # Track where current level 02 group starts
    redefines_groups = {}  # Track REDEFINES relationships
    
    try:
        with open(cpy_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('*') or line.startswith('      *'):
                continue
            
            # Look for field definitions with optional REDEFINES clause
            field_match = re.match(r'\s*(\d{2})\s+([A-Z0-9-]+)(?:\s+REDEFINES\s+([A-Z0-9-]+))?(?:\s+PIC\s+([X9V()0-9]+))?\s*\.?', line, re.IGNORECASE)
            
            if field_match:
                level = int(field_match.group(1))
                name = field_match.group(2)
                redefines_target = field_match.group(3)
                picture = field_match.group(4)
                
                # Determine starting position for this field
                field_start_pos = current_position
                
                # Handle different level types
                if level == 2:  # Level 02 - main record structures
                    if redefines_target:
                        # REDEFINES: Start at position 1 (redefining the first structure)
                        field_start_pos = 1
                        current_group_start = 1
                        current_position = 1
                        redefines_groups[name] = redefines_target
                        print(f"🔄 REDEFINES detected: {name} redefines {redefines_target} at position 1")
                    else:
                        # First/main structure: starts at position 1
                        field_start_pos = 1
                        current_group_start = 1
                        current_position = 1
                elif level >= 5:  # Child fields (05, 10, etc.)
                    # Child fields continue from current position within the group
                    field_start_pos = current_position
                
                # Create the field object
                if picture:
                    # Elementary field with PIC clause
                    field_length, field_type = parse_picture_clause(picture)
                    field = CobolField(
                        level=level,
                        name=name,
                        picture=picture,
                        start_pos=field_start_pos,
                        length=field_length,
                        field_type=field_type
                    )
                    fields.append(field)
                    
                    # Advance position only for elementary fields
                    if level >= 5:
                        current_position += field_length
                else:
                    # Group field (no PIC clause)
                    field = CobolField(
                        level=level,
                        name=name,
                        picture=None,
                        start_pos=field_start_pos,
                        length=0,  # Will be calculated based on children
                        field_type='group'
                    )
                    fields.append(field)
    
    except Exception as e:
        print(f"❌ Error parsing COBOL copybook: {e}")
        return []
    
    # Post-process: Calculate group lengths and show REDEFINES relationships
    if redefines_groups:
        print(f"\n📋 REDEFINES relationships found:")
        for redefining, redefined in redefines_groups.items():
            print(f"  • {redefining} REDEFINES {redefined}")
    
    # Calculate total lengths for each group
    print(f"\n📏 Structure lengths:")
    current_group = None
    group_max_pos = 0
    
    for field in fields:
        if field.level == 2:
            if current_group:
                print(f"  • {current_group}: {group_max_pos} bytes")
            current_group = field.name
            group_max_pos = 0
        elif field.picture and field.length > 0:
            field_end = field.start_pos + field.length - 1
            group_max_pos = max(group_max_pos, field_end)
    
    if current_group:
        print(f"  • {current_group}: {group_max_pos} bytes")
    
    return fields


def parse_picture_clause(picture: str) -> Tuple[int, str]:
    """Parse PIC clause to determine field length and type"""
    if not picture:
        return 0, 'group'
    
    # Remove common COBOL keywords
    pic = picture.upper().replace('PIC', '').replace('PICTURE', '').strip()
    
    length = 0
    field_type = 'alphanumeric'
    
    # Handle different PIC formats
    if 'X' in pic:
        # Alphanumeric field
        field_type = 'alphanumeric'
        # Extract length: X(30) or XXX
        x_match = re.search(r'X\((\d+)\)', pic)
        if x_match:
            length = int(x_match.group(1))
        else:
            length = pic.count('X')
    
    elif '9' in pic:
        # Numeric field
        field_type = 'numeric'
        # Extract length: 9(10) or 999V99
        nine_match = re.search(r'9\((\d+)\)', pic)
        if nine_match:
            length = int(nine_match.group(1))
        else:
            length = pic.count('9')
        
        # Add decimal places if V is present
        if 'V' in pic:
            v_pos = pic.find('V')
            decimal_part = pic[v_pos+1:]
            if '(' in decimal_part:
                decimal_match = re.search(r'\((\d+)\)', decimal_part)
                if decimal_match:
                    length += int(decimal_match.group(1))
            else:
                length += decimal_part.count('9')
    
    return length, field_type


def display_cobol_structure(fields: List[CobolField]):
    """Display parsed COBOL structure in a readable format"""
    print("\n📋 COBOL Record Structure:")
    print("-" * 50)
    
    for field in fields:
        indent = "  " * (field.level // 5)  # Simple indentation
        pic_info = f" PIC {field.picture}" if field.picture else ""
        length_info = f" (Length: {field.length})" if field.length > 0 else ""
        pos_info = f" [Pos: {field.start_pos}]" if field.start_pos > 0 else ""
        
        print(f"{indent}{field.level:02d} {field.name}{pic_info}{length_info}{pos_info}")


def parse_data_file(txt_file: str, fields: List[CobolField]):
    """Parse fixed-width data file using COBOL field definitions"""
    try:
        # Try different encodings commonly used in COBOL systems
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        lines = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(txt_file, 'r', encoding=encoding) as f:
                    lines = f.readlines()
                    used_encoding = encoding
                    break
            except UnicodeDecodeError:
                continue
        
        if lines is None:
            print("❌ Could not decode file with any supported encoding")
            return
            
        print(f"📖 File decoded using: {used_encoding}")
        
        if not lines:
            print("❌ Data file is empty")
            return
        
        print(f"\n📊 Analyzing {len(lines)} data records...")
        print("-" * 60)
        
        # Group fields by record type (level 01/02 groups or single structure)
        record_types = {}
        current_group = None
        
        # Look for level 01 or 02 groups
        for field in fields:
            if field.level in [1, 2]:  # New record type (level 01 or 02)
                current_group = field.name
                record_types[current_group] = []
            elif current_group and field.picture is not None:
                record_types[current_group].append(field)
        
        # If no groups found, create a single default group
        if not record_types:
            elementary_fields = [f for f in fields if f.picture is not None]
            if elementary_fields:
                record_types['DEFAULT_RECORD'] = elementary_fields
        
        print(f"📋 Found {len(record_types)} record types:")
        for record_type in record_types.keys():
            print(f"  • {record_type}")
        
        # Parse records and detect type by first character or pattern
        records_by_type = {}
        
        for i, line in enumerate(lines[:10]):  # Analyze first 10 records
            line = line.rstrip('\n\r')
            if not line:
                continue
                
            # Try to determine record type
            record_type = detect_record_type(line, record_types)
            
            if record_type not in records_by_type:
                records_by_type[record_type] = []
            records_by_type[record_type].append((i+1, line))
        
        # Show samples of each record type
        for record_type, records in records_by_type.items():
            if not records:
                continue
                
            print(f"\n🔍 {record_type} Records (showing first 2):")
            print("-" * 50)
            
            field_list = record_types.get(record_type, [])
            
            for record_num, line in records[:2]:
                print(f"\n📄 Record #{record_num}:")
                
                for field in field_list[:10]:  # Show first 10 fields
                    if field.start_pos <= len(line):
                        start_pos = field.start_pos - 1  # Convert to 0-based
                        end_pos = start_pos + field.length
                        field_value = line[start_pos:end_pos].strip()
                        
                        # Format numeric fields with decimals
                        if field.field_type == 'numeric' and 'V' in (field.picture or ''):
                            field_value = format_numeric_field(field_value, field.picture)
                        
                        print(f"  {field.name}: '{field_value}'")
                
                if len(field_list) > 10:
                    print(f"  ... and {len(field_list) - 10} more fields")
        
        total_records = len([line for line in lines if line.strip()])
        print(f"\n✅ Successfully analyzed {total_records} records!")
        
        # Return parsed data for CSV export
        return {
            'records_by_type': records_by_type,
            'record_types': record_types,
            'all_lines': lines,
            'encoding': used_encoding
        }
        
    except Exception as e:
        print(f"❌ Error parsing data file: {e}")
        return None


def detect_record_type(line: str, record_types: Dict[str, Any]) -> str:
    """Detect the type of record based on the first character or pattern"""
    if not line:
        return "UNKNOWN"
    
    # If only one record type exists, return it (simple copybook case)
    if len(record_types) == 1:
        return list(record_types.keys())[0]
    
    # Common COBOL pattern: first character indicates record type
    first_char = line[0] if line else ""
    
    # Map common patterns to record types
    type_patterns = {
        '1': 'UGEC-CAB-RECAUDAC',  # Header record
        '2': 'UGEC-DET-RECAUDAC',  # Detail record  
        '9': 'UGEC-TOT-RECAUDAC'   # Total record
    }
    
    detected_type = type_patterns.get(first_char)
    
    # If pattern matches a known record type, return it
    if detected_type and detected_type in record_types:
        return detected_type
    
    # Otherwise, try to find the best match by length
    line_length = len(line.rstrip())
    best_match = "UNKNOWN"
    best_score = 0
    
    for record_type, fields in record_types.items():
        if fields:
            # Calculate expected length for this record type
            max_pos = max((f.start_pos + f.length - 1) for f in fields)
            length_diff = abs(line_length - max_pos)
            score = 1000 - length_diff  # Closer length = higher score
            
            if score > best_score:
                best_score = score
                best_match = record_type
    
    return best_match if best_match != "UNKNOWN" else list(record_types.keys())[0]


def format_numeric_field(value: str, picture: str) -> str:
    """Format a numeric field value according to its PICTURE clause"""
    if not value or not picture:
        return value
    
    try:
        # Remove non-numeric characters for processing
        clean_value = ''.join(c for c in value if c.isdigit())
        if not clean_value:
            return value
        
        # Check if field has decimal places
        if 'V' in picture:
            v_pos = picture.find('V')
            decimal_part = picture[v_pos+1:]
            decimal_places = decimal_part.count('9')
            
            if decimal_places > 0:
                # Convert to float with proper decimal places
                numeric_val = float(clean_value) / (10 ** decimal_places)
                return f"{numeric_val:.{decimal_places}f}"
        
        return clean_value
    except:
        return value


def export_to_csv(parsed_data: Dict[str, Any], fields: List[CobolField], original_file: str):
    """Export parsed COBOL data to CSV format"""
    try:
        print(f"\n📤 CSV Export")
        print("=" * 30)
        
        # Ask for separator
        separator = text_input("Enter CSV separator (default: ';'):", default=";")
        if not separator:
            separator = ";"
        
        # Generate default filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        default_filename = f"{timestamp}.csv"
        
        # Ask if user wants to change output filename
        custom_name = text_input(f"Output filename (default: {default_filename}):", default=default_filename)
        if custom_name and custom_name.strip():
            output_filename = custom_name.strip()
        else:
            output_filename = default_filename
        
        # Ensure .csv extension
        if not output_filename.lower().endswith('.csv'):
            output_filename += '.csv'
        
        # Use OutputManager to get the full path (no subfolder)
        output_manager = OutputManager()
        output_file = output_manager.get_output_path('cobol_processor', output_filename, subfolder="")
        
        # Get data
        records_by_type = parsed_data['records_by_type']
        record_types = parsed_data['record_types']
        all_lines = parsed_data['all_lines']
        encoding = parsed_data['encoding']
        
        print(f"\n🔄 Processing all {len(all_lines)} records...")
        
        # Create CSV with all records
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            
            # Collect all unique fields from all record types
            all_fields = {}
            for record_type, field_list in record_types.items():
                for field in field_list:
                    if field.picture:  # Only elementary fields
                        all_fields[field.name] = field
            
            # Create header row
            header = ['RECORD_TYPE', 'RECORD_NUMBER'] + list(all_fields.keys())
            
            writer = csv.writer(csvfile, delimiter=separator, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(header)
            
            # Process all lines
            records_written = 0
            for line_num, line in enumerate(all_lines, 1):
                line = line.rstrip('\n\r')
                if not line.strip():
                    continue
                
                # Detect record type
                record_type = detect_record_type(line, record_types)
                
                # Create row data
                row_data = [record_type, line_num]
                
                # Extract field values
                field_list = record_types.get(record_type, [])
                field_values = {}
                
                # Parse fields for this record type
                for field in field_list:
                    if field.picture and field.start_pos <= len(line):
                        start_pos = field.start_pos - 1  # Convert to 0-based
                        end_pos = start_pos + field.length
                        field_value = line[start_pos:end_pos].strip()
                        
                        # Format numeric fields
                        if field.field_type == 'numeric' and 'V' in (field.picture or ''):
                            field_value = format_numeric_field(field_value, field.picture)
                        
                        field_values[field.name] = field_value
                
                # Add values for all possible fields (fill missing with empty)
                for field_name in all_fields.keys():
                    row_data.append(field_values.get(field_name, ''))
                
                writer.writerow(row_data)
                records_written += 1
                
                # Show progress for large files
                if records_written % 5000 == 0:
                    print(f"  📝 Processed {records_written} records...")
        
        # Show statistics
        print(f"\n✅ CSV Export Complete!")
        print(f"📁 Output file: {output_file}")
        print(f"📊 Records exported: {records_written}")
        print(f"📋 Fields included: {len(all_fields)}")
        print(f"🔢 Separator used: '{separator}'")
        
        # Show file size
        file_size = os.path.getsize(output_file)
        print(f"📏 Output file size: {format_file_size(file_size)}")
        print(f"\n📂 Full path: {output_file.absolute()}")
        
        # Calculate actual record type breakdown from all processed records
        print(f"\n📋 Analyzing record type distribution...")
        type_counts = {}
        for line in all_lines:
            if line.strip():
                record_type = detect_record_type(line, record_types)
                type_counts[record_type] = type_counts.get(record_type, 0) + 1
        
        if type_counts:
            print(f"\n📋 Record types exported:")
            for record_type, count in sorted(type_counts.items()):
                percentage = (count / records_written) * 100 if records_written > 0 else 0
                print(f"  • {record_type}: {count:,} records ({percentage:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")


def browse_for_file(extension: str, title: str, start_dir: Optional[str] = None) -> Optional[str]:
    """Interactive file browser to select a file with specific extension"""
    current_dir = start_dir if start_dir and os.path.exists(start_dir) else os.getcwd()
    
    while True:
        # Get directory contents
        items = []
        
        # Add parent directory option
        if current_dir != os.path.dirname(current_dir):  # Not at root
            items.append({
                'name': '📁 ..',
                'value': '..',
                'description': 'Parent directory',
                'type': 'parent'
            })
        
        # List directories and files
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
            
            # Add files with matching extension
            for entry in entries:
                full_path = os.path.join(current_dir, entry)
                if os.path.isfile(full_path) and entry.lower().endswith(extension.lower()):
                    file_size = format_file_size(os.path.getsize(full_path))
                    items.append({
                        'name': f'📄 {entry}',
                        'value': entry,
                        'description': f'File ({file_size})',
                        'type': 'file'
                    })
            
            # Add manual entry option
            items.append({
                'name': '✏️  Enter path manually',
                'value': 'manual',
                'description': 'Type the full file path',
                'type': 'manual'
            })
            
            # Add cancel option
            items.append({
                'name': '❌ Cancel',
                'value': 'cancel',
                'description': 'Cancel file selection',
                'type': 'cancel'
            })
            
            # Show current directory
            print(f"\n📂 Current directory: {current_dir}")
            
            # Show menu
            selected = interactive_menu(title, items)
            
            if not selected or selected['type'] == 'cancel':
                return None
            
            if selected['type'] == 'manual':
                # Manual path entry
                manual_path = text_input(f"Enter full path to {extension} file:")
                if manual_path and manual_path.strip():
                    manual_path = manual_path.strip()
                    if validate_file_path(manual_path, extension):
                        return os.path.abspath(manual_path)
                    else:
                        print(f"❌ Invalid {extension} file: {manual_path}")
                        if not confirm("Try again?", default=True):
                            return None
                        continue
                else:
                    if not confirm("Try again?", default=True):
                        return None
                    continue
            
            elif selected['type'] == 'parent':
                # Go to parent directory
                current_dir = os.path.dirname(current_dir)
            
            elif selected['type'] == 'dir':
                # Enter directory
                current_dir = os.path.join(current_dir, selected['value'])
            
            elif selected['type'] == 'file':
                # File selected
                file_path = os.path.join(current_dir, selected['value'])
                return os.path.abspath(file_path)
                
        except PermissionError:
            print(f"❌ Permission denied: {current_dir}")
            current_dir = os.path.dirname(current_dir)
        except Exception as e:
            print(f"❌ Error browsing directory: {e}")
            return None


if __name__ == "__main__":
    main()