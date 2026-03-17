#!/usr/bin/env python3
"""
Direct fix script for LinkedApiDoc endpoints with empty parameters.
Uses explicit route-to-params mapping based on controller analysis.
"""

import json
import requests

# Configuration
API_BASE_URL = "http://localhost:3000/api"
AUTH_USER = "admin"
AUTH_PASS = "admin"

# Manually mapped endpoints based on controller analysis
# Format: { route: { params: {...}, description_addition: "..." } }
ENDPOINT_FIXES = {
    # BSE_MAGASIN
    "api/GetDesignMagasin": {"CodeMagasin": "string"},
    "api/BSE_MAGASIN/ChangeType": {"ids": "List<string>", "tpe": "short"},
    
    # BSE_COMPTE
    "api/GetDesignCaisses": {"CodeCaisse": "string"},
    "api/RecalculSoldeCaisse": {},
    "api/GetListCaisses": {},
    
    # TRS_TIERS
    "api/TRS_TIERS/GetSoldeTiers": {"CodeTiers": "string"},
    "api/TRS_TIERS/GetValuesTiers": {"CodeTiers": "string"},
    "api/TRS_TIERS/RecalculSoldeTiers": {"listTiers": "List<string>", "del": "bool"},
    "api/TRS_TIERS/AttacheUser": {"tr": "string", "usr": "string"},
    "api/TRS_TIERS/GenerateSInit": {"ids": "List<string>"},
    "api/TRS_TIERS/SaveOrderTiers": {"ds": "List<TIERS_SECTOR_ORDER>"},
    "api/TRS_TIERS/GetListWilaya": {},
    "api/TRS_TIERS/GetListOrigine": {},
    "api/TRS_TIERS/GenerateUsers": {"ids": "List<string>"},
    "api/TRS_TIERS/DetachUser": {"ids": "List<string>"},
    "api/TRS_TIERS/DisableUsers": {"ids": "List<string>"},
    "api/TRS_TIERS/ClearProgres": {},
    
    # ACH_DOCUMENT
    "api/ACH_DOCUMENT/GetAllowCreance": {},
    
    # ACH_DOCUMENT_DETAIL
    "api/ACH_DOCUMENT_DETAIL/GetRecapClientsQte": {},
    
    # BSE_COLIS
    "api/BSE_COLIS/SaveMesures": {},
    
    # BSE_PRODUITS
    "api/BSE_PRODUITS/GetProdVariantPrint": {},
    "api/BSE_PRODUITS/GetProdVariants": {},
    "api/BSE_PRODUITS/GetMesureJson": {},
    "api/GetScaleProducts": {},
    "api/RegenerateCB": {},
    "api/UpdateIndexScale": {},
    "api/GetNotifBalance": {},
    "api/ClearNotifBalance": {},
    "api/GetNbrConsigne": {},
    "api/DeleteDoubleLots": {},
    "api/GetOtherProduct": {},
    "api/BSE_PRODUITS/ImportData": {},
    "api/BSE_PRODUITS/GetImportResult": {},
    "api/BSE_PRODUITS/GetNbrBloqDesktop": {},
    
    # BSE_PRODUIT_PACK
    "api/BSE_PRODUIT_PACK/SelectProdPack": {},
    
    # BSE_VARIANTS
    "api/BSE_VARIANTS/ImportData": {},
    
    # CHG_DOCUMENT
    "api/CHG_DOCUMENT/SaveCharges": {},
    
    # CRM_GAOLS
    "api/CRM_GAOLS/GetTypeGoals": {},
    "api/CRM_GAOLS/GetTypeGoalsFidelite": {},
    "api/CRM_GAOLS/GetGoalsTiers": {},
    
    # CRM_GAOLS_VENDORS
    "api/CRM_GAOLS_VENDORS/SelectVendors": {},
    
    # CRM_PROMOTION_PRODUIT
    "api/GetNbrPromo": {},
    
    # CRM_TOURNEE
    "api/CRM_TOURNEE/GetRecapTour": {},
    
    # DbTools
    "api/DbTools/BackupBdd": {},
    "api/DbTools/GetProgress": {},
    "api/GetInitDbSource": {},
    "api/RunInitDatabase": {},
    
    # EMP_CONTRAT
    "api/EMP_CONTRAT/DeleteEmp": {},
    
    # EMP_SHEET
    "api/EMP_SHEET/SaveSheet": {},
    
    # ProdComposit
    "api/ProdComposit/ImportData": {},
    
    # ProdPrix
    "api/ProdPrix/LoadListPrix": {},
    "api/ProdPrix/ImportData": {},
    
    # REST_OBSERVATION
    "api/REST_OBSERVATION/ImportData": {},
    
    # REST_SUPLEMENT
    "api/REST_SUPLEMENT/ImportData": {},
    
    # REST_TABLES
    "api/REST_TABLES/GetEmproteeState": {},
    
    # STK_INVENTAIRE
    "api/GetCurrentInvent": {},
    
    # STK_INVENTAIRE_DETAIL
    "api/STK_INVENTAIRE_DETAIL/AjustStock": {},
    "api/STK_INVENTAIRE_DETAIL/ImportData": {},
    
    # STK_PRODUCTION_COLORS
    "api/STK_PRODUCTION_COLORS/UpdateColors": {},
    
    # STK_STOCK
    "api/STK_STOCK/RecalculStockOld": {},
    "api/STK_STOCK/CorrectionStock": {},
    "api/STK_STOCK/FusionALL": {},
    "api/STK_STOCK/LoadDiagnostic": {},
    "api/GetStkPrintDetail": {},
    "api/STK_STOCK/ClearProgres": {},
    "api/STK_STOCK/ImportData": {},
    "api/STK_STOCK/GetListExp": {},
    
    # STK_TRANSFERT
    "api/STK_TRANSFERT/GetSortCode": {},
    
    # STK_VENTE
    "api/STK_VENTE/GetPriceList": {},
    
    # SYS_EXERCICE
    "api/GetListExercices1": {},
    "api/SYS_EXERCICE/GetProgress": {},
    
    # TRS_CREANCE
    "api/DeletePaiements": {},
    "api/TRS_CREANCE/SelectNPDocs": {},
    
    # TRS_ENCAISS
    "api/TRS_ENCAISS/GetAgencesBancaires": {},
    "api/TRS_ENCAISS/RestoreDeleted": {},
    
    # TRS_MONEY
    "api/TRS_MONEY/Convert": {},
    
    # VTE_COMPTOIR
    "api/VTE_COMPTOIR/GetNewSalesMobile": {},
    "api/VTE_COMPTOIR/PaiementCash": {},
    "api/VTE_COMPTOIR/SelectDetailGroup": {},
    "api/VTE_COMPTOIR/SelectGroup": {},
    
    # VTE_DOCUMENT
    "api/VTE_DOCUMENT/TestCrud": {},
    "api/VTE_DOCUMENT/GetNbrWaitSales": {},
    "api/VTE_DOCUMENT/RestoreDeleted": {},
    "api/VTE_DOCUMENT/GetNewRestoCmd": {},
    "api/VTE_DOCUMENT/UpdeStateLivr": {},
    "api/VTE_DOCUMENT/CancelCmd": {},
    "api/VTE_DOCUMENT/UpQteTransfert": {},
    "api/VTE_DOCUMENT/GenerateCreance": {},
    "api/VTE_DOCUMENT/GetAllowCreance": {},
    "api/VTE_DOCUMENT/SelectDetailGroup": {},
    
    # WF_STATES
    "api/WF_STATES/GetWFDocuments": {},
    
    # TEST
    "/api/TEST_PERSIST": {},
    
    # RecalculSoldeTiersExe (DbTools)
    "api/RecalculSoldeTiersExe": {},
}

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

def main():
    print("=== LinkedApiDoc Parameter Fix Script (Direct Mapping) ===")
    print()
    
    # Step 1: Get endpoints with empty parameters
    print("Step 1: Fetching endpoints with empty parameters...")
    empty_endpoints = get_endpoints_with_empty_params()
    print(f"  Found {len(empty_endpoints)} endpoints to fix")
    print()
    
    # Step 2: Update each endpoint
    print("Step 2: Updating endpoints...")
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    
    results = []
    
    for ep in empty_endpoints:
        route = ep['route']
        http_method = ep['http_method']
        
        # Normalize route for lookup
        route_key = route.replace('api/', '')
        if route.startswith('/api/'):
            route_key = route
        
        # Check if we have a fix for this route
        if route_key in ENDPOINT_FIXES or route in ENDPOINT_FIXES:
            params_dict = ENDPOINT_FIXES.get(route_key, ENDPOINT_FIXES.get(route, {}))
            
            # Build parameters JSON
            params_json = build_params_json(params_dict)
            
            # Enhance description
            new_desc = enhance_description(ep['description'], params_dict, route)
            
            # Update endpoint
            success = update_endpoint(ep['id'], params_json, new_desc)
            
            if success:
                updated_count += 1
                results.append({
                    'id': ep['id'],
                    'route': route,
                    'method': http_method,
                    'params': params_dict,
                    'status': 'updated'
                })
                print(f"  ✓ Updated: {http_method} {route}")
                if params_dict:
                    print(f"    Params: {params_dict}")
            else:
                failed_count += 1
                results.append({
                    'id': ep['id'],
                    'route': route,
                    'method': http_method,
                    'status': 'failed'
                })
                print(f"  ✗ Failed: {http_method} {route}")
        else:
            skipped_count += 1
            results.append({
                'id': ep['id'],
                'route': route,
                'method': http_method,
                'status': 'skipped',
                'reason': 'no mapping defined'
            })
            print(f"  ⊘ Skipped: {http_method} {route} (no mapping)")
    
    print()
    print("=== Summary ===")
    print(f"  Updated: {updated_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")
    print()
    
    # Save results
    results_file = "/home/linked/.openclaw/workspaces/linked-dev/LinkedApiDoc/scripts/fix-results-final.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to: {results_file}")
    
    return updated_count, failed_count, skipped_count

if __name__ == '__main__':
    main()
