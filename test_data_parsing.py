#!/usr/bin/env python3
"""
Test data parsing with the corrected COBOL parser
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Import the parsing functions from our test script
sys.path.append('.')
from test_cobol_parser import parse_cobol_copybook, CobolField, display_cobol_structure

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
        
        # Group fields by record type (level 02 groups)
        record_types = {}
        current_group = None
        
        # Look for level 02 groups
        for field in fields:
            if field.level == 2:  # New record type (level 02)
                current_group = field.name
                record_types[current_group] = []
            elif current_group and field.picture is not None:
                record_types[current_group].append(field)
        
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
                
            print(f"\n🔍 {record_type} Records:")
            print("-" * 50)
            
            field_list = record_types.get(record_type, [])
            
            for record_num, line in records[:2]:  # Show first 2 records
                print(f"\n📄 Record #{record_num} (Length: {len(line)} chars):")
                print(f"   Raw: {line}")
                
                print(f"   Parsed fields:")
                for field in field_list[:8]:  # Show first 8 fields
                    if field.start_pos <= len(line):
                        start_pos = field.start_pos - 1  # Convert to 0-based
                        end_pos = start_pos + field.length
                        field_value = line[start_pos:end_pos] if end_pos <= len(line) else line[start_pos:]
                        
                        print(f"     {field.name} (pos {field.start_pos}-{field.start_pos + field.length - 1}): '{field_value.strip()}'")
                    else:
                        print(f"     {field.name} (pos {field.start_pos}-{field.start_pos + field.length - 1}): <beyond record length>")
                
                if len(field_list) > 8:
                    print(f"     ... and {len(field_list) - 8} more fields")
                
                # Check if record length matches expected structure
                expected_length = max((f.start_pos + f.length - 1) for f in field_list) if field_list else 0
                actual_length = len(line)
                if actual_length != expected_length:
                    print(f"   ⚠️  Length mismatch: expected {expected_length}, got {actual_length}")
                else:
                    print(f"   ✅ Length matches expected {expected_length} chars")
        
        total_records = len([line for line in lines if line.strip()])
        print(f"\n✅ Successfully analyzed {total_records} records!")
        
    except Exception as e:
        print(f"❌ Error parsing data file: {e}")
        return None

def main():
    print("🔍 COBOL Data Parsing Test")
    print("=" * 50)
    
    # Test with the COBOL copybook and data file
    cpy_file = "test_cobol_files/UGECCUOT.CPY"
    txt_file = "test_cobol_files/HALQ.UG.BAT1SBAS.REG00777.NUEVOR1.D250711.txt"
    
    if not os.path.exists(cpy_file):
        print(f"❌ Copybook file not found: {cpy_file}")
        return
        
    if not os.path.exists(txt_file):
        print(f"❌ Data file not found: {txt_file}")
        return
    
    print(f"📄 Parsing copybook: {cpy_file}")
    fields = parse_cobol_copybook(cpy_file)
    
    if fields:
        print(f"\n📄 Analyzing data file: {txt_file}")
        parse_data_file(txt_file, fields)
    else:
        print("❌ Failed to parse COBOL copybook")

if __name__ == "__main__":
    main()