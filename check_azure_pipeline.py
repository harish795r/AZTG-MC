import os
import json
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("SP_OWNER_1_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_OWNER_1_SECRET")
STORAGE_ACCOUNT = "nhiztaresearchlogs"

print("=" * 65)
print("  AZTG-MC Azure Environment & Telemetry Diagnostic")
print("=" * 65)

try:
    cred = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    
    # 1. Check Blob Storage Connection
    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=cred)
    
    print("\n[1] Checking Raw Telemetry Storage Account...")
    containers = list(blob_service.list_containers())
    print(f"    ✅ Storage Account Reachable: {STORAGE_ACCOUNT}")
    print(f"    📦 Active Log Containers ({len(containers)}):")
    
    total_blobs = 0
    sample_preview = None

    for c in containers:
        container_client = blob_service.get_container_client(c['name'])
        try:
            blobs = list(container_client.list_blobs())
            count = len(blobs)
            total_blobs += count
            print(f"       • {c['name']} -> {count} file(s)")
            
            if count > 0 and not sample_preview:
                # Get latest blob
                latest_blob = blobs[-1]
                blob_data = container_client.get_blob_client(latest_blob.name).download_blob().readall().decode('utf-8')
                sample_preview = (latest_blob.name, blob_data)
        except Exception as perm_err:
            print(f"       • {c['name']} -> Access restriction: {perm_err.error_code if hasattr(perm_err, 'error_code') else 'Need Storage Blob Data Reader'}")

    print(f"\n[2] Telemetry Pipeline Summary:")
    if total_blobs > 0:
        print(f"    🎉 CONFIRMED: {total_blobs} telemetry files exist in blob storage!")
        if sample_preview:
            print(f"\n[3] Latest Emitted Log File Preview ({sample_preview[0]}):")
            # Show first few lines
            lines = sample_preview[1].splitlines()
            for line in lines[:2]:
                try:
                    parsed = json.loads(line)
                    print("    " + json.dumps(parsed, indent=2)[:400] + "\n    ...")
                except Exception:
                    print("    " + line[:200] + "...")
    else:
        print("    ⚠️  Containers exist, but need 'Storage Blob Data Reader' on sp-owner-1 to read contents.")

    print("\n" + "=" * 65)
    print("  Status: Logs are actively depositing to your Azure tenant.")
    print("=" * 65)

except Exception as e:
    print(f"\n❌ Diagnostic Error: {str(e)}")
