import os
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("SP_OWNER_1_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_OWNER_1_SECRET")
STORAGE_ACCOUNT = "nhiztaresearchlogs"

print("=" * 65)
print("  AZTG-MC: Purging Old Logs from Azure Blob Storage")
print("=" * 65)

try:
    cred = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=cred)

    containers = list(blob_service.list_containers())
    print(f"\nScanning storage account: {STORAGE_ACCOUNT}...")

    total_deleted = 0
    for container in containers:
        c_name = container['name']
        container_client = blob_service.get_container_client(c_name)
        blobs = list(container_client.list_blobs())
        
        if blobs:
            print(f"🗑️  Deleting {len(blobs)} blob(s) from container: '{c_name}'...")
            for b in blobs:
                container_client.delete_blob(b.name)
                total_deleted += 1
        else:
            print(f"ℹ️  Container '{c_name}' is already empty.")

    print("\n" + "=" * 65)
    print(f"✅ Cleanup Complete! Deleted {total_deleted} old log blob(s).")
    print("=" * 65)

except Exception as e:
    print(f"\n❌ Error during cleanup: {str(e)}")
