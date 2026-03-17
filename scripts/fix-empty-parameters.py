#!/usr/bin/env python3
"""
Script to fix all LinkedApiDoc endpoints with empty parameters.
Extracts method signatures from .cs controller files and updates the API.
"""

import json
import re
import os
import sys
import requests
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:3000/api"
AUTH_USER = "admin"
AUTH_PASS = "admin"
CONTROLLERS_DIR = "/home/linked/.openclaw/workspaces/linked-dev/linked-api/API/ComService.Controllers"
VERSIONS_FILE = "/home/linked/.openclaw/workspaces/linked-dev/LinkedApiDoc/VERSIONS.md"

def parse_method_signature(line, next_lines):
    """Extract method name and parameters from C# method signature."""
    # Pattern for method signature: public [type] MethodName([params])
    pattern = r'public\s+\w+\s+(\w+)\s*\(([^)]*)\)'
    match = re.search(pattern, line)
    if not match:
        return None, {}
    
    method_name = match.group(1)
    params_str = match.group(2)
    
    # Parse parameters
    params = {}
    if params_str.strip():
        # Split by comma, handling complex types
        param_parts = re.split(r',\s*(?![^<]*>)', params_str)
        for param in param_parts:
            param = param.strip()
            if not param:
                continue
            
            # Extract parameter name (last word) and type
            # Patterns: "string CodeMagasin", "[FromBody] List<string> ids", "short tpe"
            param_pattern = r'(?:\[\w+\]\s*)?(\w+(?:<[^>]+>)?)\s+(\w+)'
            param_match = re.search(param_pattern, param)
            if param_match:
                param_type = param_match.group(1)
                param_name = param_match.group(2)
                
                # Normalize type to JSON schema type
                json_type = "string"
                if "List<" in param_type or "[]" in param_type:
                    json_type = "List<string>"
                elif param_type in ["int", "short", "decimal", "bool", "bool?"]:
                    json_type = param_type
                elif param_type == "string":
                    json_type = "string"
                elif "XpertQueryDAL" in param_type:
                    json_type = "XpertQueryDAL"
                elif "PrintInfos" in param_type:
                    json_type = "PrintInfos"
                else:
                    json_type = param_type.lower()
                
                params[param_name] = json_type
    
    return method_name, params

def scan_controller_file(filepath):
    """Scan a controller file and extract all method signatures."""
    methods = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Look for route annotations
        route_match = re.search(r'\[Route\("api/([^"]+)"\)\]', line)
        if route_match:
            route = route_match.group(1)
            # Find the method signature (next few lines)
            for j in range(i+1, min(i+5, len(lines))):
                method_line = lines[j]
                if 'public' in method_line and ('(' in method_line):
                    method_name, params = parse_method_signature(method_line, lines[j+1:j+3])
                    if method_name:
                        methods[route] = {
                            'method': method_name,
                            'params': params,
                            'file': os.path.basename(filepath)
                        }
                    break
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
        if params == '{}' or params == '':
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
    return response.status_code == 200

def enhance_description(original_desc, params_dict):
    """Enhance description with parameter information."""
    if not params_dict:
        return original_desc
    
    param_text = " Paramètres : "
    param_parts = []
    for name, ptype in params_dict.items():
        param_parts.append(f"{name} ({ptype})")
    
    param_text += ", ".join(param_parts)
    
    # Avoid duplication if params already mentioned
    if "Paramètres" in original_desc or "Paramètre" in original_desc:
        return original_desc
    
    return original_desc.rstrip('.') + '.' + param_text

def main():
    print("=== LinkedApiDoc Parameter Fix Script ===")
    print(f"Scanning controllers in: {CONTROLLERS_DIR}")
    print()
    
    # Step 1: Scan all controller files
    print("Step 1: Scanning controller files...")
    all_methods = {}
    
    for filename in os.listdir(CONTROLLERS_DIR):
        if filename.endswith('.cs'):
            filepath = os.path.join(CONTROLLERS_DIR, filename)
            methods = scan_controller_file(filepath)
            all_methods.update(methods)
            print(f"  ✓ {filename}: {len(methods)} methods")
    
    print(f"  Total: {len(all_methods)} methods found")
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
        # Normalize route (remove leading api/ if present)
        route_normalized = route.replace('api/', '')
        
        # Try to find matching method
        matched = None
        for method_route, method_info in all_methods.items():
            if method_route == route_normalized or method_route.endswith(route_normalized):
                matched = method_info
                break
        
        if matched and matched['params']:
            # Build new parameters JSON
            params_json = build_params_json(matched['params'])
            
            # Enhance description
            new_desc = enhance_description(ep['description'], matched['params'])
            
            # Update endpoint
            success = update_endpoint(ep['id'], params_json, new_desc)
            
            if success:
                updated_count += 1
                results.append({
                    'id': ep['id'],
                    'route': route,
                    'method': ep['http_method'],
                    'params': matched['params'],
                    'status': 'updated'
                })
                print(f"  ✓ Updated: {ep['http_method']} {route}")
            else:
                failed_count += 1
                print(f"  ✗ Failed: {ep['http_method']} {route}")
        else:
            skipped_count += 1
            results.append({
                'id': ep['id'],
                'route': route,
                'method': ep['http_method'],
                'params': {},
                'status': 'skipped (no match)'
            })
            print(f"  ⊘ Skipped: {ep['http_method']} {route} (no matching method)")
    
    print()
    print("=== Summary ===")
    print(f"  Updated: {updated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print()
    
    # Save results
    results_file = "/home/linked/.openclaw/workspaces/linked-dev/LinkedApiDoc/scripts/fix-results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")
    
    return updated_count, failed_count, skipped_count

if __name__ == '__main__':
    main()
