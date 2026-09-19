import os
import time
import random
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient

try:
    from azure.mgmt.resource import ResourceManagementClient
except ImportError:
    from azure.mgmt.resource.resources import ResourceManagementClient

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")
RG_NAME = os.getenv("RESOURCE_GROUP_NAME", "NHI-ZTA-Research")

if not TENANT_ID or not SUBSCRIPTION_ID:
    raise ValueError("Missing AZURE_TENANT_ID or AZURE_SUBSCRIPTION_ID in .env file!")

identities = [
    {"name": "sp-reader-1", "client_id": os.getenv("SP_READER_1_CLIENT_ID"), "secret": os.getenv("SP_READER_1_SECRET"), "class": 0},
    {"name": "sp-reader-2", "client_id": os.getenv("SP_READER_2_CLIENT_ID"), "secret": os.getenv("SP_READER_2_SECRET"), "class": 0},
    {"name": "sp-reader-3", "client_id": os.getenv("SP_READER_3_CLIENT_ID"), "secret": os.getenv("SP_READER_3_SECRET"), "class": 0},
    {"name": "sp-contributor-1", "client_id": os.getenv("SP_CONTRIB_1_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_1_SECRET"), "class": 1},
    {"name": "sp-contributor-2", "client_id": os.getenv("SP_CONTRIB_2_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_2_SECRET"), "class": 1},
    {"name": "sp-contributor-3", "client_id": os.getenv("SP_CONTRIB_3_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_3_SECRET"), "class": 1},
    {"name": "sp-owner-1", "client_id": os.getenv("SP_OWNER_1_CLIENT_ID"), "secret": os.getenv("SP_OWNER_1_SECRET"), "class": 2},
    {"name": "sp-owner-2", "client_id": os.getenv("SP_OWNER_2_CLIENT_ID"), "secret": os.getenv("SP_OWNER_2_SECRET"), "class": 2},
    {"name": "sp-owner-3", "client_id": os.getenv("SP_OWNER_3_CLIENT_ID"), "secret": os.getenv("SP_OWNER_3_SECRET"), "class": 2},
]

def get_utc_time_str():
    return datetime.now(timezone.utc).strftime('%H:%M:%S')

def simulate_dynamic_traffic(id_info):
    name = id_info["name"]
    client_id = id_info["client_id"]
    secret = id_info["secret"]
    id_class = id_info["class"]

    if not client_id or not secret:
        return

    # Stochastic Activity Factor
    activity_prob = 0.95 if id_class == 0 else (0.60 if id_class == 1 else 0.30)
    if random.random() > activity_prob:
        print(f"[{get_utc_time_str()}] ⏸️  {name} is dormant during this operational window.")
        return

    print(f"[{get_utc_time_str()}] 🔐 Authenticating as {name} (Class {id_class})...")

    try:
        credential = ClientSecretCredential(
            tenant_id=TENANT_ID,
            client_id=client_id,
            client_secret=secret
        )
        resource_client = ResourceManagementClient(credential, SUBSCRIPTION_ID)
        storage_client = StorageManagementClient(credential, SUBSCRIPTION_ID)

        # Poisson Arrival Workloads
        if id_class == 0:
            num_calls = np.random.poisson(lam=8)
            print(f"  -> Active workload: Generating {num_calls} stochastic read events...")
            for _ in range(max(1, num_calls)):
                action = random.choice(["list_resources", "list_storage", "check_rg"])
                if action == "list_resources":
                    _ = list(resource_client.resources.list_by_resource_group(RG_NAME))
                elif action == "list_storage":
                    _ = list(storage_client.storage_accounts.list_by_resource_group(RG_NAME))
                else:
                    _ = resource_client.resource_groups.get(RG_NAME)
                time.sleep(random.expovariate(1.0 / 0.8))

        elif id_class == 1:
            num_calls = np.random.poisson(lam=2)
            print(f"  -> Underutilized contributor: Emitting {num_calls} read events...")
            for _ in range(max(1, num_calls)):
                _ = list(resource_client.resources.list_by_resource_group(RG_NAME))
                time.sleep(random.uniform(0.5, 2.0))

        elif id_class == 2:
            print("  -> Dormant owner: Single sporadic permission probe...")
            _ = resource_client.resource_groups.get(RG_NAME)

        # Injected behavioral drift (5% chance)
        if random.random() < 0.05:
            print(f"  ⚠️ [Injected Drift] {name} attempting permission boundary inspection...")
            try:
                _ = list(resource_client.providers.list())
            except Exception:
                pass

        print(f"  ✅ Completed run for {name}")

    except Exception as e:
        print(f"  ❌ Operational error on {name}: {str(e)}")

def run_simulation():
    print("=" * 65)
    print("  AZTG-MC: Dynamic Multi-Modal Azure Telemetry Generator")
    print(f"  Target RG: {RG_NAME} | Subscription: {SUBSCRIPTION_ID}")
    print("=" * 65)
    
    shuffled_identities = identities.copy()
    random.shuffle(shuffled_identities)

    for id_info in shuffled_identities:
        simulate_dynamic_traffic(id_info)
        time.sleep(random.uniform(1.0, 4.0))

    print("=" * 65)
    print("🎉 Telemetry burst complete. Ingested into Azure Log Analytics.")
    print("=" * 65)

if __name__ == "__main__":
    run_simulation()
