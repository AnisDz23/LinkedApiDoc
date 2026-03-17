#!/usr/bin/env python3
"""
Improved script to fix all LinkedApiDoc endpoints with empty parameters.
Better C# parsing, handles all controller directories.
"""

import json
import re
import os
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:3000/api"
AUTH_USER = "admin"
AUTH_PASS = "admin"
WORKSPACE_DIR = "/home/linked/.openclaw/workspaces/linked-dev/linked-api/API"
VERSIONS_FILE = "/home/linked/.openclaw/workspaces/linked-dev/LinkedApiDoc/VERSIONS.md"

def normalize_type(param_type):
    """Normalize C# type to JSON schema type."""
    type_map = {
        'string': 'string',
        'int': 'int',
        'Int32': 'int',
        'short': 'short',
        'Int16': 'short',
        'bool': 'bool',
        'Boolean': 'bool',
        'decimal': 'decimal',
        'double': 'decimal',
        'float': 'decimal',
        'List<string>': 'List<string>',
        'List<int>': 'List<int>',
        'List<short>': 'List<short>',
        'List<bool>': 'List<bool>',
        'string[]': 'List<string>',
        'int[]': 'List<int>',
        'XpertQueryDAL': 'XpertQueryDAL',
        'PrintInfos': 'PrintInfos',
        'View_TRS_TIERS': 'View_TRS_TIERS',
        'TRS_RECALCUL': 'TRS_RECALCUL',
        'ImportResult': 'ImportResult',
    }
    
    # Handle generic List<T>
    list_match = re.match(r'List<([^>]+)>', param_type)
    if list_match:
        inner_type = list_match.group(1)
        return f"List<{inner_type}>"
    
    return type_map.get(param_type, param_type.lower())

def parse_method_signature(line):
    """Extract method name and parameters from C# method signature."""
    # Pattern: public [return_type] MethodName([params])
    # Handle attributes like [Authorize], [HttpGet], etc.
    if 'public' not in line:
        return None, {}
    
    # Find method name and parameters
    pattern = r'public\s+(?:static\s+)?(?:async\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)'
    match = re.search(pattern, line)
    if not match:
        return None, {}
    
    return_type = match.group(1)
    method_name = match.group(2)
    params_str = match.group(3)
    
    # Skip constructors
    if method_name in ['BSE_MAGASINController', 'BSE_COMPTEController', 'TRS_TIERSController']:
        return None, {}
    
    # Parse parameters
    params = {}
    if params_str.strip():
        # Split by comma, handling generic types
        param_parts = re.split(r',\s*(?![^<]*>)', params_str)
        for param in param_parts:
            param = param.strip()
            if not param:
                continue
            
            # Remove attributes like [FromBody], [FromQuery]
            param = re.sub(r'\[[\w\s]+\]\s*', '', param)
            
            # Extract type and name
            # Pattern: "string CodeMagasin" or "List<string> ids"
            param_pattern = r'(\w+(?:<[^>]+>)?)\s+(\w+)'
            param_match = re.search(param_pattern, param)
            if param_match:
                param_type = param_match.group(1)
                param_name = param_match.group(2)
                
                # Skip 'this' parameter (extension methods)
                if param_name == 'this':
                    continue
                
                json_type = normalize_type(param_type)
                params[param_name] = json_type
    
    return method_name, params

def scan_controller_file(filepath):
    """Scan a controller file and extract all HTTP methods with routes."""
    methods = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        print(f"    Error reading {filepath}: {e}")
        return {}
    
    i = 0
    current_route = None
    current_http_method = None
    
    while i < len(lines):
        line = lines[i]
        
        # Check for HTTP method attributes
        http_patterns = [
            (r'\[HttpGet\]', 'GET'),
            (r'\[HttpPost\]', 'POST'),
            (r'\[HttpPut\]', 'PUT'),
            (r'\[HttpDelete\]', 'DELETE'),
        ]
        
        for pattern, http_method in http_patterns:
            if re.search(pattern, line):
                current_http_method = http_method
                break
        
        # Check for Route attribute
        route_match = re.search(r'\[Route\(["\']([^"\']+)["\']\)\]', line)
        if route_match:
            current_route = route_match.group(1)
        
        # Check for method signature (must have HTTP method and route)
        if current_http_method and current_route:
            if 'public' in line and '(' in line and ')' in line:
                method_name, params = parse_method_signature(line)
                if method_name:
                    methods[current_route] = {
                        'http_method': current_http_method,
                        'method_name': method_name,
                        'params': params,
                        'file': os.path.basename(filepath)
                    }
                # Reset for next method
                current_route = None
                current_http_method = None
        
        i += 1
    
    return methods

def get_endpoints_with_empty_params():
    """Fetch all endpoints with empty parameters from the API."""
    url = f"{API_BASE_URL}/endpoints"
    response = requests.get(url, auth=(AUTH_USER, AUTH_PASS))
    response.raise_for_status()
    
    endpoints = response.json()
    empty_param_endpoints = []
    
    for ep in endpoints:
        params = ep.get('parameters', '{}')
        if params == '{}' or params == '' or params is None:
            empty_param_endpoints.append(ep)
    
    return empty_param_endpoints

def build_params_json(params_dict):
    """Build JSON string for parameters field."""
    if not params_dict:
        return '{}'
    return json.dumps(params_dict)

def update_endpoint(endpoint_id, params_json, description):
    """Update an endpoint in the database via API."""
    url = f"{API_BASE_URL}/endpoints"
    payload = {
        "id": endpoint_id,
        "parameters": params_json,
        "description": description
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, auth=(AUTH_USER, AUTH_PASS), headers=headers)
    return response.status_code in [200, 201]

def enhance_description(original_desc, params_dict, route):
    """Enhance description with parameter information."""
    if not params_dict:
        return original_desc
    
    # Build parameter text
    param_parts = []
    for name, ptype in params_dict.items():
        param_parts.append(f"`{name}` ({ptype})")
    
    param_text = " Paramètres : " + ", ".join(param_parts)
    
    # Avoid duplication
    if "Paramètres" in original_desc or "Paramètre" in original_desc:
        return original_desc
    
    return original_desc.rstrip('.') + '.' + param_text

def find_controller_files(base_dir):
    """Find all .cs controller files recursively."""
    controller_files = []
    
    for root, dirs, files in os.walk(base_dir):
        if 'Controllers' in root:
            for file in files:
                if file.endswith('.cs'):
                    controller_files.append(os.path.join(root, file))
    
    return controller_files

def main():
    print("=== LinkedApiDoc Parameter Fix Script (Improved) ===")
    print(f"Scanning controllers in: {WORKSPACE_DIR}")
    print()
    
    # Step 1: Find and scan all controller files
    print("Step 1: Scanning all controller files...")
    all_methods = {}
    controller_files = find_controller_files(WORKSPACE_DIR)
    
    for filepath in controller_files:
        methods = scan_controller_file(filepath)
        if methods:
            all_methods.update(methods)
            print(f"  ✓ {os.path.basename(filepath)}: {len(methods)} methods")
    
    print(f"  Total methods found: {len(all_methods)}")
    print()
    
    # Step 2: Get endpoints with empty parameters
    print("Step 2: Fetching endpoints with empty parameters...")
    empty_endpoints = get_endpoints_with_empty_params()
    print(f"  Found {len(empty_endpoints)} endpoints to fix")
    print()
    
    # Step 3: Match and update
    print("Step 3: Matching and updating endpoints...")
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    
    results = []
    
    for ep in empty_endpoints:
        route = ep['route']
        http_method = ep['http_method']
        
        # Normalize route for matching
        route_normalized = route.replace('api/', '').replace('api', '')
        
        # Try to find matching method
        matched = None
        for method_route, method_info in all_methods.items():
            method_route_normalized = method_route.replace('api/', '').replace('api', '')
            
            # Exact match
            if method_route == route or method_route_normalized == route_normalized:
                if method_info['http_method'] == http_method:
                    matched = method_info
                    break
            
            # Partial match (route ends with method route)
            if route_normalized.endswith(method_route_normalized):
                if method_info['http_method'] == http_method:
                    matched = method_info
                    break
        
        if matched and matched['params']:
            # Build new parameters JSON
            params_json = build_params_json(matched['params'])
            
            # Enhance description
            new_desc = enhance_description(ep['description'], matched['params'], route)
            
            # Update endpoint
            success = update_endpoint(ep['id'], params_json, new_desc)
            
            if success:
                updated_count += 1
                results.append({
                    'id': ep['id'],
                    'route': route,
                    'method': http_method,
                    'params': matched['params'],
                    'status': 'updated'
                })
                print(f"  ✓ Updated: {http_method} {route}")
            else:
                failed_count += 1
                print(f"  ✗ Failed: {http_method} {route}")
        else:
            skipped_count += 1
            results.append({
                'id': ep['id'],
                'route': route,
                'method': http_method,
                'params': {},
                'status': 'skipped',
                'reason': 'no matching method or no params'
            })
            print(f"  ⊘ Skipped: {http_method} {route}")
    
    print()
    print("=== Summary ===")
    print(f"  Updated: {updated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print()
    
    # Save results
    results_file = "/home/linked/.openclaw/workspaces/linked-dev/LinkedApiDoc/scripts/fix-results-v2.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")
    
    return updated_count, failed_count, skipped_count

if __name__ == '__main__':
    main()
