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

print("=" * 60)
print("  Checking Live Telemetry from Azure Blob Storage")
print("=" * 60)

try:
    cred = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=cred)

    containers = list(blob_service.list_containers())
    print(f"\n✅ Connected to Storage Account: {STORAGE_ACCOUNT}")
    print(f"📦 Containers Found ({len(containers)}):")
    for c in containers:
        print(f"   - {c['name']}")

    # Inspect first available container
    for c in containers:
        container_client = blob_service.get_container_client(c['name'])
        blobs = list(container_client.list_blobs())
        print(f"\n📄 Found {len(blobs)} log file(s) in '{c['name']}':")
        for b in blobs[:3]:
            print(f"   -> {b.name}")
            # Download and preview first blob
            blob_client = container_client.get_blob_client(b.name)
            data = blob_client.download_blob().readall().decode('utf-8')
            print("\n🔍 Sample Log Content (First 300 chars):")
            print(data[:300] + "...\n")
            break

except Exception as e:
    print(f"\n❌ Error connecting to storage: {str(e)}")
