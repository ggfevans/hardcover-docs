import json
import os
from pathlib import Path

# Configuration
INPUT_FILE = "hardcover-schema-dump.json"  # Now using the direct JSON file
OUTPUT_DIR = "../src/content/docs/api/GraphQL/Schemas"

def parse_type_info(type_obj):
    """Convert GraphQL type object to a readable string"""
    if not type_obj:
        return "Unknown"
    
    kind = type_obj.get('kind', '')
    name = type_obj.get('name')
    of_type = type_obj.get('ofType')
    
    if kind == 'NON_NULL':
        return f"{parse_type_info(of_type)}!"
    elif kind == 'LIST':
        return f"[{parse_type_info(of_type)}]"
    elif name:
        return name
    elif of_type:
        return parse_type_info(of_type)
    else:
        return "Unknown"

def generate_markdown_for_type(type_info, type_map):
    """Generate markdown documentation for a specific type"""
    name = type_info['name']
    kind = type_info['kind']
    description = type_info.get('description', 'No description provided')
    
    # Create frontmatter
    content = f"""---
title: {name}
description: {description.replace('"', '\\"').replace('\n', ' ')}
---

# {name}

**Kind:** {kind}

## Description
{description}

"""
    
    # Add fields section if applicable
    fields = type_info.get('fields', [])
    if fields:
        content += "## Fields\n| Name | Type | Description |\n|------|------|-------------|\n"
        for field in fields:
            if not field:  # Skip empty fields
                continue
            field_name = field.get('name', '')
            field_type = parse_type_info(field.get('type', {}))
            field_desc = field.get('description', '') or 'No description'
            
            # Clean up description for markdown table
            field_desc = field_desc.replace('\n', ' ').replace('|', '\\|')
            
            # Add row to table
            content += f"| {field_name} | `{field_type}` | {field_desc} |\n"
    
    # Add input fields section if applicable
    input_fields = type_info.get('inputFields', [])
    if input_fields:
        content += "\n## Input Fields\n| Name | Type | Description | Default |\n|------|------|-------------|--------|\n"
        for field in input_fields:
            if not field:  # Skip empty fields
                continue
            field_name = field.get('name', '')
            field_type = parse_type_info(field.get('type', {}))
            field_desc = field.get('description', '') or 'No description'
            field_default = field.get('defaultValue', '') or 'null'
            
            # Clean up description for markdown table
            field_desc = field_desc.replace('\n', ' ').replace('|', '\\|')
            
            # Add row to table
            content += f"| {field_name} | `{field_type}` | {field_desc} | `{field_default}` |\n"
    
    # Add enum values section if applicable
    enum_values = type_info.get('enumValues', [])
    if enum_values:
        content += "\n## Enum Values\n| Value | Description |\n|-------|-------------|\n"
        for enum_val in enum_values:
            if not enum_val:  # Skip empty values
                continue
            enum_name = enum_val.get('name', '')
            enum_desc = enum_val.get('description', '') or 'No description'
            
            # Clean up description for markdown table
            enum_desc = enum_desc.replace('\n', ' ').replace('|', '\\|')
            
            # Add row to table
            content += f"| {enum_name} | {enum_desc} |\n"
    
    return content

def main():
    # Load the JSON directly - no need to extract it from Groovy
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as file:
            schema_data = json.load(file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return
    
    # Process the schema data
    types = schema_data['data']['__schema']['types']
    
    # Group types by kind
    types_by_kind = {}
    type_map = {}
    
    for t in types:
        if 'kind' in t and 'name' in t:
            kind = t['kind']
            type_map[t['name']] = t
            
            if kind not in types_by_kind:
                types_by_kind[kind] = []
            types_by_kind[kind].append(t)
    
    # Create output directory structure
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Create a directory for each kind
    for kind in types_by_kind:
        kind_dir = os.path.join(OUTPUT_DIR, kind)
        os.makedirs(kind_dir, exist_ok=True)
        
        # Create a markdown file for each type
        for type_info in types_by_kind[kind]:
            if type_info.get('name', '').startswith('__'):
                continue  # Skip GraphQL introspection types
            
            content = generate_markdown_for_type(type_info, type_map)
            
            file_path = os.path.join(kind_dir, f"{type_info['name']}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        # Create an index file for this kind
        index_content = f"""---
title: {kind} Types
description: GraphQL {kind} types in the Hardcover API
---

# {kind} Types

| Name | Description |
|------|-------------|
"""
        
        # Add entry for each type, sorted alphabetically
        sorted_types = sorted(types_by_kind[kind], key=lambda t: t.get('name', ''))
        for type_info in sorted_types:
            if type_info.get('name', '').startswith('__'):
                continue  # Skip GraphQL introspection types
            
            name = type_info.get('name', '')
            desc = (type_info.get('description', '') or 'No description').replace('\n', ' ')
            index_content += f"| [{name}](./{name}) | {desc} |\n"
        
        # Write the index file
        with open(os.path.join(kind_dir, "index.md"), 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    # Create a main index file
    main_index = """---
title: GraphQL Schema Reference
description: Complete reference of Hardcover's GraphQL schema types
---

# GraphQL Schema Reference

This section documents the complete GraphQL schema used by the Hardcover API.

## Type Categories

"""
    
    for kind in sorted(types_by_kind.keys()):
        count = len([t for t in types_by_kind[kind] if not t.get('name', '').startswith('__')])
        main_index += f"- [{kind}](./{kind}/) - {count} types\n"
    
    # Write the main index file
    with open(os.path.join(OUTPUT_DIR, "index.md"), 'w', encoding='utf-8') as f:
        f.write(main_index)
    
    print(f"Documentation generated successfully in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()