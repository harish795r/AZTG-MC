import os
import json
import pandas as pd
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("SP_OWNER_1_CLIENT_ID")
CLIENT_SECRET = os.getenv("SP_OWNER_1_SECRET")
STORAGE_ACCOUNT = "nhiztaresearchlogs"

LOCAL_RAW_DIR = "data/azure/raw_downloaded_logs"
os.makedirs(LOCAL_RAW_DIR, exist_ok=True)

print("=" * 65)
print("  AZTG-MC: Fetching Real Live Telemetry from Azure Storage")
print("=" * 65)

try:
    cred = ClientSecretCredential(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    account_url = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=cred)

    containers = list(blob_service.list_containers())
    all_extracted_records = []
    total_files_downloaded = 0

    for container in containers:
        c_name = container['name']
        print(f"\n📂 Scanning container: {c_name}...")
        container_client = blob_service.get_container_client(c_name)
        blobs = list(container_client.list_blobs())

        for b in blobs:
            blob_client = container_client.get_blob_client(b.name)
            raw_content = blob_client.download_blob().readall().decode('utf-8')
            
            # Save raw file locally for reproducibility
            safe_filename = f"{c_name}_{b.name.replace('/', '_')}"
            local_path = os.path.join(LOCAL_RAW_DIR, safe_filename)
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(raw_content)
            total_files_downloaded += 1

            # Parse lines (Azure diagnostic format outputs newline-delimited JSON or JSON arrays)
            for line in raw_content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    # If Azure nested multiple records in a "records" array:
                    if "records" in record:
                        for sub_rec in record["records"]:
                            sub_rec["_source_container"] = c_name
                            all_extracted_records.append(sub_rec)
                    else:
                        record["_source_container"] = c_name
                        all_extracted_records.append(record)
                except Exception:
                    # Ignore partial headers/footers if JSON array
                    continue

    print("\n" + "=" * 65)
    print(f"✅ Extraction Summary:")
    print(f"   • Raw Blob Files Downloaded : {total_files_downloaded}")
    print(f"   • Total Telemetry Records   : {len(all_extracted_records)}")
    
    # Save combined raw records
    output_json = "data/azure/live_extracted_azure_records.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_extracted_records, f, indent=2)
    print(f"   • Saved Combined Records To : {output_json}")
    print("=" * 65)

except Exception as e:
    print(f"\n❌ Error during log extraction: {str(e)}")
