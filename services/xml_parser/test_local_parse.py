#!/usr/bin/env python3
"""
Simple standalone script to test XML parser locally.
Usage: python test_local_parse.py <xml_file_path>
"""
import sys
import json
from parser_app import parse_ubl_invoice


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_local_parse.py <xml_file_path>")
        print("\nExample:")
        print("  python test_local_parse.py tests/sample_invoice.xml")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    try:
        with open(xml_file, 'rb') as f:
            xml_content = f.read()
        
        print(f"Parsing {xml_file}...")
        print(f"File size: {len(xml_content)} bytes\n")
        
        result = parse_ubl_invoice(xml_content)
        
        print("=" * 60)
        print("PARSED RESULT (JSON):")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        print("\n" + "=" * 60)
        
        # Summary
        metadata = result.get('invoice_metadata', {})
        items = result.get('line_items', [])
        
        print(f"\nSummary:")
        print(f"  Invoice: {metadata.get('invoice_number', 'N/A')}")
        print(f"  Date: {metadata.get('invoice_date', 'N/A')}")
        print(f"  Supplier: {metadata.get('supplier', 'N/A')}")
        print(f"  Total Amount: {metadata.get('total_amount', 'N/A')}")
        print(f"  Line Items: {len(items)}")
        
        for i, item in enumerate(items, 1):
            print(f"\n  Item {i}:")
            print(f"    Description: {item.get('description', 'N/A')}")
            print(f"    SKU: {item.get('sku_raw', 'N/A')}")
            print(f"    Quantity: {item.get('quantity', 'N/A')} {item.get('unit_code', '')}")
            print(f"    Unit Price: {item.get('unit_price', 'N/A')}")
            print(f"    Total: {item.get('total_price', 'N/A')}")
        
        print("\n✓ Parsing successful!")
        
    except FileNotFoundError:
        print(f"Error: File not found: {xml_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error parsing XML: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
