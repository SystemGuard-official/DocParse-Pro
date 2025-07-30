"""
JSON parsing utilities for extracting and cleaning JSON from text responses.
"""
import re
import json
from typing import Optional, Dict, Any


def extract_and_parse_json(data_string: str) -> Optional[Dict[Any, Any]]:
    """
    Extract JSON from the data string and parse it.
    
    This function is designed to extract JSON content that is wrapped in 
    markdown code blocks (```json ... ```) and parse it into a Python dictionary.
    It includes robust JSON cleaning and repair functionality.
    
    Args:
        data_string (str): The string containing JSON data, possibly wrapped in markdown
        
    Returns:
        Optional[Dict[Any, Any]]: Parsed JSON data as a dictionary, or None if parsing fails
    """
    try:
        # Find the JSON content between ```json and ```
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, data_string, re.DOTALL)
        if not match:
            return None
        json_content = match.group(1)

        def clean_json_string(text: str) -> str:
            """Clean and repair JSON string with intelligent structure recovery."""
            # 1. Basic cleanup - handle escaped characters
            text = text.replace('\\n', '\n').replace('\\"', '"')
            
            def is_related_field(entity_id: str, field_key: str, original_text: str) -> bool:
                """Determine if a field is related to an entity without domain knowledge"""
                # Look for proximity in original text
                entity_pattern = f'"{entity_id}"'
                field_pattern = f'"{field_key}"'
                
                entity_pos = original_text.find(entity_pattern)
                field_pos = original_text.find(field_pattern)
                
                if entity_pos == -1 or field_pos == -1:
                    return False
                
                # If they're within 500 characters, consider them related
                return abs(entity_pos - field_pos) < 500
            
            def normalize_field_name(field_name: str) -> str:
                """Normalize field names without domain knowledge"""
                # Remove special characters and normalize
                normalized = re.sub(r'[^\w\s]', '', field_name.lower())
                normalized = re.sub(r'\s+', '_', normalized.strip())
                normalized = re.sub(r'_+', '_', normalized)
                return normalized.strip('_')
            
            def generic_json_repair(text: str) -> Dict[Any, Any]:
                """Generic JSON repair without document knowledge"""
                # Step 1: Extract all key-value pairs and nested objects
                all_data = {}
                
                # Find all simple key-value pairs first
                simple_kv_pattern = r'"([^"]+)":\s*"([^"]*)"'
                simple_matches = re.findall(simple_kv_pattern, text)
                
                # Store simple key-value pairs
                for key, value in simple_matches:
                    clean_key = key.strip()
                    clean_value = value.strip()
                    all_data[clean_key] = clean_value
                
                # Step 2: Find nested objects (structures like "key": { ... })
                nested_pattern = r'"([^"]+)":\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
                nested_matches = re.findall(nested_pattern, text, re.DOTALL)
                
                for key, content in nested_matches:
                    clean_key = key.strip()
                    nested_obj = {}
                    
                    # Extract key-value pairs from nested content
                    nested_kv_matches = re.findall(simple_kv_pattern, content)
                    for nkey, nvalue in nested_kv_matches:
                        nested_obj[nkey.strip()] = nvalue.strip()
                    
                    all_data[clean_key] = nested_obj
                
                # Step 3: Handle duplicate keys by converting to arrays
                organized_data = {}
                key_counts = {}
                
                # Count occurrences of each key
                for key in all_data.keys():
                    key_counts[key] = key_counts.get(key, 0) + 1
                
                # Organize data, handling duplicates
                for key, value in all_data.items():
                    if key_counts[key] > 1:
                        # Multiple values for same key - convert to array
                        if key not in organized_data:
                            organized_data[key] = []
                        organized_data[key].append(value)
                    else:
                        organized_data[key] = value
                
                # Step 4: Intelligently group related data
                final_data = {}
                
                # Look for numbered items (potential list items)
                numbered_items = {}
                regular_items = {}
                
                for key, value in organized_data.items():
                    if key.isdigit():
                        numbered_items[key] = value
                    else:
                        regular_items[key] = value
                
                # Group numbered items as potential entities
                if numbered_items:
                    entities = []
                    for num in sorted(numbered_items.keys()):
                        entity = {"id": num}
                        
                        # Try to find the primary value (usually name)
                        if isinstance(numbered_items[num], str):
                            entity["primary_value"] = numbered_items[num]
                        
                        # Look for related fields that might belong to this entity
                        for field_key, field_value in regular_items.items():
                            # Simple heuristic: if field appears near this number in original text
                            # or contains common field indicators
                            if is_related_field(num, field_key, text):
                                entity[normalize_field_name(field_key)] = field_value
                        
                        entities.append(entity)
                    
                    final_data["entities"] = entities
                
                # Add remaining regular items
                for key, value in regular_items.items():
                    # Skip items that were already grouped
                    if not any(is_related_field(num, key, text) for num in numbered_items.keys()):
                        final_data[normalize_field_name(key)] = value
                
                return final_data
            
            # Apply generic repair
            try:
                repaired_data = generic_json_repair(text)
                return json.dumps(repaired_data, indent=2)
            except Exception as e:
                # Fallback: try to extract whatever we can
                # Simple extraction as last resort
                simple_data = {}
                simple_matches = re.findall(r'"([^"]+)":\s*"([^"]*)"', text)
                for key, value in simple_matches:
                    simple_data[key.strip()] = value.strip()
                return json.dumps(simple_data, indent=2)

        fixed_json = clean_json_string(json_content)
        try:
            parsed_data = json.loads(fixed_json)
            return parsed_data
        except json.JSONDecodeError as e:
            return None
    except Exception as e:
        return None
