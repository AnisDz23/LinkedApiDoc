#!/usr/bin/env python3
"""
Fix ALL duplicate endpoints - updates every copy of each route.
"""

import json
import requests

API_BASE_URL = "http://localhost:3000/api"
AUTH_USER = "admin"
AUTH_PASS = "admin"

# Same mapping as before
ENDPOINT_FIXES = {
    "api/GetDesignMagasin": {"CodeMagasin": "string"},
    "api/BSE_MAGASIN/ChangeType": {"ids": "List<string>", "tpe": "short"},
    "api/GetDesignCaisses": {"CodeCaisse": "string"},
    "api/RecalculSoldeCaisse": {},
    "api/GetListCaisses": {},
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
    "api/ACH_DOCUMENT/GetAllowCreance": {},
    "api/ACH_DOCUMENT_DETAIL/GetRecapClientsQte": {},
    "api/BSE_COLIS/SaveMesures": {},
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
    "api/BSE_PRODUIT_PACK/SelectProdPack": {},
    "api/BSE_VARIANTS/ImportData": {},
    "api/CHG_DOCUMENT/SaveCharges": {},
    "api/CRM_GAOLS/GetTypeGoals": {},
    "api/CRM_GAOLS/GetTypeGoalsFidelite": {},
    "api/CRM_GAOLS/GetGoalsTiers": {},
    "api/CRM_GAOLS_VENDORS/SelectVendors": {},
    "api/GetNbrPromo": {},
    "api/CRM_TOURNEE/GetRecapTour": {},
    "api/DbTools/BackupBdd": {},
    "api/DbTools/GetProgress": {},
    "api/GetInitDbSource": {},
    "api/RunInitDatabase": {},
    "api/RecalculSoldeTiersExe": {},
    "api/EMP_CONTRAT/DeleteEmp": {},
    "api/EMP_SHEET/SaveSheet": {},
    "api/ProdComposit/ImportData": {},
    "api/ProdPrix/LoadListPrix": {},
    "api/ProdPrix/ImportData": {},
    "api/REST_OBSERVATION/ImportData": {},
    "api/REST_SUPLEMENT/ImportData": {},
    "api/REST_TABLES/GetEmproteeState": {},
    "api/GetCurrentInvent": {},
    "api/STK_INVENTAIRE_DETAIL/AjustStock": {},
    "api/STK_INVENTAIRE_DETAIL/ImportData": {},
    "api/STK_PRODUCTION_COLORS/UpdateColors": {},
    "api/STK_STOCK/RecalculStockOld": {},
    "api/STK_STOCK/CorrectionStock": {},
    "api/STK_STOCK/FusionALL": {},
    "api/STK_STOCK/LoadDiagnostic": {},
    "api/GetStkPrintDetail": {},
    "api/STK_STOCK/ClearProgres": {},
    "api/STK_STOCK/ImportData": {},
    "api/STK_STOCK/GetListExp": {},
    "api/STK_TRANSFERT/GetSortCode": {},
    "api/STK_VENTE/GetPriceList": {},
    "api/GetListExercices1": {},
    "api/SYS_EXERCICE/GetProgress": {},
    "api/DeletePaiements": {},
    "api/TRS_CREANCE/SelectNPDocs": {},
    "api/TRS_ENCAISS/GetAgencesBancaires": {},
    "api/TRS_ENCAISS/RestoreDeleted": {},
    "api/TRS_MONEY/Convert": {},
    "api/VTE_COMPTOIR/GetNewSalesMobile": {},
    "api/VTE_COMPTOIR/PaiementCash": {},
    "api/VTE_COMPTOIR/SelectDetailGroup": {},
    "api/VTE_COMPTOIR/SelectGroup": {},
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
    "api/WF_STATES/GetWFDocuments": {},
    "/api/TEST_PERSIST": {},
}

def get_all_endpoints():
    """Fetch all endpoints from the API."""
    url = f"{API_BASE_URL}/endpoints"
    response = requests.get(url, auth=(AUTH_USER, AUTH_PASS))
    response.raise_for_status()
    return response.json()

def build_params_json(params_dict):
    if not params_dict:
        return '{}'
    return json.dumps(params_dict)

def update_endpoint(ep, params_dict, new_desc):
    """Update an endpoint with complete payload."""
    url = f"{API_BASE_URL}/endpoints"
    payload = {
        "id": ep['id'],
        "http_method": ep['http_method'],
        "route": ep['route'],
        "controller": ep.get('controller', ''),
        "parameters": build_params_json(params_dict),
        "description": new_desc
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, auth=(AUTH_USER, AUTH_PASS), headers=headers)
    return response.status_code in [200, 201]

def enhance_description(original_desc, params_dict):
    if not params_dict:
        return original_desc
    param_parts = []
    for name, ptype in params_dict.items():
        param_parts.append(f"`{name}` ({ptype})")
    param_text = " Paramètres : " + ", ".join(param_parts)
    if "Paramètres" in original_desc or "Paramètre" in original_desc:
        return original_desc
    return original_desc.rstrip('.') + '.' + param_text

def main():
    print("=== Fix ALL Duplicate Endpoints ===")
    print()
    
    # Get all endpoints
    print("Fetching all endpoints...")
    all_endpoints = get_all_endpoints()
    print(f"  Total endpoints: {len(all_endpoints)}")
    
    # Find all endpoints with empty params that match our fixes
    to_update = []
    for ep in all_endpoints:
        route = ep['route']
        params = ep.get('parameters', '{}')
        
        # Check if params is empty
        if params in ['{}', '', None]:
            # Check if we have a fix for this route
            route_key = route.replace('api/', '') if route.startswith('api/') else route
            if route_key in ENDPOINT_FIXES or route in ENDPOINT_FIXES:
                to_update.append(ep)
    
    print(f"  Endpoints to fix: {len(to_update)}")
    print()
    
    # Update all
    print("Updating endpoints...")
    updated = 0
    failed = 0
    
    for ep in to_update:
        route = ep['route']
        params_dict = ENDPOINT_FIXES.get(route, ENDPOINT_FIXES.get(route.replace('api/', ''), {}))
        new_desc = enhance_description(ep['description'], params_dict)
        
        success = update_endpoint(ep, params_dict, new_desc)
        if success:
            updated += 1
            print(f"  ✓ Updated: {ep['http_method']} {route} (ID: {ep['id']})")
        else:
            failed += 1
            print(f"  ✗ Failed: {ep['http_method']} {route} (ID: {ep['id']})")
    
    print()
    print("=== Summary ===")
    print(f"  Updated: {updated}")
    print(f"  Failed: {failed}")
    
    return updated, failed

if __name__ == '__main__':
    main()
