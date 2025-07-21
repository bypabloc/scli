import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Add the src directory to path to import scli modules  
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
from scli.menu_utils import interactive_menu, text_input, confirm

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
    
    # Get .cpy file path
    cpy_path = text_input("Enter path to .cpy file:")
    if cpy_path and cpy_path.strip():
        cpy_path = cpy_path.strip()
        if validate_file_path(cpy_path, '.cpy'):
            cpy_file = cpy_path
            print(f"✅ CPY file selected: {cpy_file}")
        else:
            print(f"❌ Invalid .cpy file: {cpy_path}")
            return
    else:
        print("❌ CPY file path is required")
        return
    
    # Get .txt file path
    txt_path = text_input("Enter path to .txt file:")
    if txt_path and txt_path.strip():
        txt_path = txt_path.strip()
        if validate_file_path(txt_path, '.txt'):
            txt_file = txt_path
            print(f"✅ TXT file selected: {txt_file}")
        else:
            print(f"❌ Invalid .txt file: {txt_path}")
            return
    else:
        print("❌ TXT file path is required")
        return
    
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
                parse_data_file(txt_file, fields)
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
    """Parse COBOL copybook and extract field definitions"""
    fields = []
    current_position = 1
    
    try:
        with open(cpy_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('*') or line.startswith('      *'):
                continue
            
            # Look for field definitions (level number + name + PIC)
            field_match = re.match(r'\s*(\d{2})\s+([A-Z0-9-]+)(?:\s+PIC\s+([X9V()0-9]+))?\s*\.?', line, re.IGNORECASE)
            
            if field_match:
                level = int(field_match.group(1))
                name = field_match.group(2)
                picture = field_match.group(3)
                
                # Calculate field length and type from PIC clause
                if picture:
                    field_length, field_type = parse_picture_clause(picture)
                    field = CobolField(
                        level=level,
                        name=name,
                        picture=picture,
                        start_pos=current_position,
                        length=field_length,
                        field_type=field_type
                    )
                    fields.append(field)
                    current_position += field_length
                else:
                    # Group field (no PIC clause)
                    field = CobolField(
                        level=level,
                        name=name,
                        picture=None,
                        start_pos=current_position,
                        length=0,  # Will be calculated based on children
                        field_type='group'
                    )
                    fields.append(field)
    
    except Exception as e:
        print(f"❌ Error parsing COBOL copybook: {e}")
        return []
    
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
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        if not lines:
            print("❌ Data file is empty")
            return
        
        print(f"\n📊 Parsing {len(lines)} data records:")
        print("-" * 60)
        
        # Parse only elementary fields (those with PIC clauses)
        elementary_fields = [f for f in fields if f.picture is not None]
        
        for i, line in enumerate(lines[:5], 1):  # Show first 5 records
            line = line.rstrip('\n\r')
            print(f"\n📄 Record {i}:")
            
            current_pos = 0
            for field in elementary_fields:
                if current_pos < len(line):
                    field_value = line[current_pos:current_pos + field.length].strip()
                    
                    # Format value based on field type
                    if field.field_type == 'numeric' and 'V' in (field.picture or ''):
                        # Handle decimal implied by V
                        try:
                            v_pos = field.picture.find('V')
                            decimal_places = field.picture[v_pos+1:].count('9')
                            if decimal_places > 0:
                                numeric_val = float(field_value) / (10 ** decimal_places)
                                field_value = f"{numeric_val:.{decimal_places}f}"
                        except:
                            pass
                    
                    print(f"  {field.name}: {field_value}")
                    current_pos += field.length
        
        if len(lines) > 5:
            print(f"\n... and {len(lines) - 5} more records")
        
        print(f"\n✅ Successfully parsed {len(lines)} records!")
        
    except Exception as e:
        print(f"❌ Error parsing data file: {e}")


if __name__ == "__main__":
    main()