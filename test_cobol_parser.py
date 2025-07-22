#!/usr/bin/env python3
"""
Simple test script to validate COBOL parser without dependencies
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

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

def main():
    print("🔍 COBOL Parser Test")
    print("=" * 50)
    
    # Test with the COBOL copybook
    cpy_file = "test_cobol_files/UGECCUOT.CPY"
    
    if not os.path.exists(cpy_file):
        print(f"❌ File not found: {cpy_file}")
        return
    
    print(f"📄 Parsing: {cpy_file}")
    fields = parse_cobol_copybook(cpy_file)
    
    if fields:
        display_cobol_structure(fields)
        
        # Show position analysis
        print(f"\n🔍 Position Analysis:")
        print("-" * 50)
        
        groups = {}
        for field in fields:
            if field.level == 2:
                groups[field.name] = []
            elif field.picture and field.level >= 5:
                # Find the parent group
                parent_group = None
                for group_name in reversed(list(groups.keys())):
                    parent_group = group_name
                    break
                if parent_group:
                    groups[parent_group].append(field)
        
        for group_name, group_fields in groups.items():
            print(f"\n📂 {group_name}:")
            if group_fields:
                for field in group_fields[:5]:  # Show first 5 fields
                    end_pos = field.start_pos + field.length - 1
                    print(f"  {field.name}: pos {field.start_pos}-{end_pos} ({field.length} bytes)")
                if len(group_fields) > 5:
                    print(f"  ... and {len(group_fields) - 5} more fields")
            else:
                print("  (Group only - no elementary fields)")
    else:
        print("❌ Failed to parse COBOL copybook")

if __name__ == "__main__":
    main()