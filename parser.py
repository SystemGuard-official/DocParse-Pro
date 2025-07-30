data = "user\n         \n            FORM IMAGE TO JSON - Extract ALL information from this form image and return ONLY a valid JSON object.\n            - Do NOT return any commentary, description, example, or explanation—ONLY the JSON object.\n            - The output MUST be a single, complete JSON object, only the assistance response no user prompt.\n            - Include every field or element you can identify, preserving structure, grouping, and relationships.\n            - Represent checkboxes/radios/dropdowns/tables/signatures/printed/handwritten/special elements/sections/empty/incomplete fields/validation/fine print as appropriate JSON keys/values.\n            - Mark unclear or questionable values as \"[UNCLEAR]\".\n            - If a field is empty, use null.\n            - For lists, use JSON arrays.\n            - For tables, use JSON arrays of objects (each object is a row).\n            - For booleans (checkboxes, radios), use true/false.\n            - For dates, use ISO format if possible.\n            - For confidence, use a separate key per section: \"confidence\": 0.0 to 1.0.\n            \n            \n            \n            assistant\n             ```json\n             {\n               \"BENEFICIARY DESIGNATION\": {\n                 \"Security Life of Denver Insurance Company, Denver, CO\": \"\",\n                 \"Midwestern United Life Insurance Company, Indianapolis, IN\": \"\",\n                 \"ReliaStar Life Insurance Company, Minneapolis, MN\": \"\",\n                 \"ReliaStar Life Insurance Company of New York, Woodbury, NY\": \"\",\n                 \"Voya Retirement Insurance and Annuity Company, Windsor, CT\": \"\",\n                 \"Venerable Insurance and Annuity Company, Des Moines, IA\": \"\"\n               },\n               \"The companies listed above may provide administrative services to each other, but may not be affiliated. All contractual obligations are the sole responsibility of the issuing insurance company.\": \"\",\n               \"Return Instructions\": \"Email completed forms to liferequest@resolutionlife.us or Fax to 877-788-6305 or Mail to Customer Service, PO Box 981331, Boston, MA 02298-1331; Overnight mail: 10 Dan Road, Dock 2, Canton, MA 02021 Website: https://customer.resolutionlife.us\",\n               \"A. OWNER(S) & INSURED/ANNUITANT(S) INFORMATION\": {\n                 \"Owner(s) Name(s) (Required)\": \"Brad Pitt\",\n                 \"Policy/Contract/File Code Number (Required)\": \"AB 56-1089\",\n                 \"Insured/Annuitant(s) Name(s)\": \"Simone Aswely\",\n                 \"Owner Phone (234)\": \"5609-1384\",\n                 \"Owner Email\": \"Bradpit@gmail.com\"\n               },\n               \"B. PRIMARY BENEFICIARIES\": {\n                 \"Irrevocable Beneficiary\": \"A beneficiary whose rights cannot be canceled without consent. If you designate an irrevocable beneficiary, any future change in the beneficiary designation or other contract change requires the signed consent of the irrevocable beneficiary. All irrevocable beneficiaries must sign their request on Page 3. If you wish to designate a beneficiary as irrevocable, check the \\\"Yes\\\" box below in association with that beneficiary's entry. If neither box is checked for Irrevocable Beneficiary, the Company will not make the beneficiary irrevocable.\",\n                 \"Trust Beneficiary\": \"If any of the below beneficiaries are a trust, include the full name and date of the trust in the Name field and write \\\"Trust\\\" in the Relationship field. The Company is not required to know or research the terms of the trust. Payment to the named trust will fully discharge all liability of the Company to the extent of such payment.\",\n                 \"Grandchildren's Clause\": \"If an insured/annuitant's child is a beneficiary, and he or she dies before the insured/annuitant, the deceased child's share will be divided among the child's surviving children, if any. (Check box to apply.)\"\n               },\n               \"Name (First, MI, Last)\": {\n                 \"1\": \"Simone Aswely\",\n                 \"DOB\": \"\",\n                 \"Gender\": \"M\",\n                 \"SSN/TIN\": \"2346-12\",\n                 \"Relationship\": \"Wife\",\n                 \"%\": \"25%\",\n                 \"Is this Beneficiary Irrevocable?\": \"No\"\n               },\n               \"Address\": {\n                 \"1\": \"Kowy Kondou, Sheet 2, AB, 2402\",\n                 \"Phone\": \"(234) 1111-4568\"\n               },\n               \"Names of all trustees (if a trust)\": {\n                 \"2\": \"Lewis Pitt\",\n                 \"DOB\": \"\",\n                 \"Gender\": \"M\",\n                 \"SSN/TIN\": \"\",\n                 \"Relationship\": \"Son\",\n                 \"%\": \"25%\",\n                 \"Is this Beneficiary Irrevocable?\": \"No\"\n               },\n               \"Address\": {\n                 \"2\": \"Kowy Kondou, Sheet 2 AB, 2402\",\n                 \"Phone\": \"(234) 234-567\"\n               },\n               \"3\": \"Callie Pitt\",\n               \"4\": \"Sarah Niles\",\n               \"Address\": {\n                 \"3\": \"Kowy Kondou Sheet 2, AB, 2402\",\n                 \"Phone\": \"(234) 345-689\"\n               },\n               \"Address\": {\n                 \"4\": \"Buxton hily Lane 4, LN 5608\",\n                 \"Phone\": \"(101) 4567-8910\"\n               },\n               \"TOTAL (MUST EQUAL 100%)\": \"100%\"\n             }\n             ```"
import json
import re

def extract_and_parse_json(data_string):
    """
    Extract JSON from the data string and parse it
    """
    try:
        # Find the JSON content between ```json and ```
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, data_string, re.DOTALL)
        if not match:
            return None
        json_content = match.group(1)

        def clean_json_string(text):
            # 1. Basic cleanup - handle escaped characters
            text = text.replace('\\n', '\n').replace('\\"', '"')
            
            def is_related_field(entity_id, field_key, original_text):
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
            
            def normalize_field_name(field_name):
                """Normalize field names without domain knowledge"""
                # Remove special characters and normalize
                normalized = re.sub(r'[^\w\s]', '', field_name.lower())
                normalized = re.sub(r'\s+', '_', normalized.strip())
                normalized = re.sub(r'_+', '_', normalized)
                return normalized.strip('_')
            
            # 2. Generic JSON repair without document knowledge
            def generic_json_repair(text):
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

def main():
    # Your input data
    
    # Extract and parse JSON
    parsed_data = extract_and_parse_json(data)
 
if __name__ == "__main__":
    main()