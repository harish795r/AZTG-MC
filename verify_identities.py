import json
import os

LOG_FILE = "data/azure/live_extracted_azure_records.json"

if not os.path.exists(LOG_FILE):
    print(f"File {LOG_FILE} not found. Run fetch_azure_logs.py first.")
    exit()

with open(LOG_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

print("=" * 65)
print("  AZTG-MC: Inspecting Service Principal Identities in Live Logs")
print("=" * 65)
print(f"Total Raw Records Loaded: {len(records)}\n")

identities_found = {}

for r in records:
    # Check properties (Entra ID Sign-In logs)
    props = r.get("properties", {})
    if isinstance(props, str):
        try:
            props = json.loads(props)
        except Exception:
            props = {}
            
    sp_name = props.get("servicePrincipalName") or r.get("caller") or props.get("appDisplayName")
    app_id = props.get("appId") or r.get("claims", {}).get("appid")
    
    if sp_name:
        if sp_name not in identities_found:
            identities_found[sp_name] = {"count": 0, "app_id": app_id, "categories": set()}
        identities_found[sp_name]["count"] += 1
        identities_found[sp_name]["categories"].add(r.get("category", r.get("_source_container", "ActivityLog")))

print(f"{'Identity / Caller':<35} | {'App ID':<38} | {'Events':<6} | {'Source Container'}")
print("-" * 110)
for identity, data in identities_found.items():
    cats = ", ".join(data["categories"])
    app = str(data["app_id"]) if data["app_id"] else "N/A"
    print(f"{identity:<35} | {app:<38} | {data['count']:<6} | {cats}")

print("\n" + "=" * 65)
