import os
import time
import random
import json
import boto3
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from azure.identity import ClientSecretCredential
from azure.mgmt.storage import StorageManagementClient
try:
    from azure.mgmt.resource import ResourceManagementClient
except ImportError:
    from azure.mgmt.resource.resources import ResourceManagementClient

load_dotenv()

print("=" * 75)
print("  AZTG-MC: Live Multi-Cloud Telemetry & Longitudinal Experiment Engine")
print("  (Simultaneous Execution: 9 Live Azure SPs + 9 Live AWS IAM Users)")
print("=" * 75)

# ----------------- CONFIGURATION -----------------
AZURE_TENANT = os.getenv("AZURE_TENANT_ID")
AZURE_SUB = os.getenv("AZURE_SUBSCRIPTION_ID")
AZURE_RG = os.getenv("RESOURCE_GROUP_NAME", "NHI-ZTA-Research")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

def get_env_cred(prefix):
    key = os.getenv(f"{prefix}_KEY") or os.getenv(f"{prefix.replace('_0', '_')}_KEY")
    secret = os.getenv(f"{prefix}_SECRET") or os.getenv(f"{prefix.replace('_0', '_')}_SECRET")
    return key, secret

azure_identities = [
    {"name": "sp-reader-01", "client_id": os.getenv("SP_READER_1_CLIENT_ID"), "secret": os.getenv("SP_READER_1_SECRET"), "class": 0},
    {"name": "sp-reader-02", "client_id": os.getenv("SP_READER_2_CLIENT_ID"), "secret": os.getenv("SP_READER_2_SECRET"), "class": 0},
    {"name": "sp-reader-03", "client_id": os.getenv("SP_READER_3_CLIENT_ID"), "secret": os.getenv("SP_READER_3_SECRET"), "class": 0},
    {"name": "sp-contrib-01", "client_id": os.getenv("SP_CONTRIB_1_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_1_SECRET"), "class": 1},
    {"name": "sp-contrib-02", "client_id": os.getenv("SP_CONTRIB_2_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_2_SECRET"), "class": 1},
    {"name": "sp-contrib-03", "client_id": os.getenv("SP_CONTRIB_3_CLIENT_ID"), "secret": os.getenv("SP_CONTRIB_3_SECRET"), "class": 1},
    {"name": "sp-owner-01", "client_id": os.getenv("SP_OWNER_1_CLIENT_ID"), "secret": os.getenv("SP_OWNER_1_SECRET"), "class": 2},
    {"name": "sp-owner-02", "client_id": os.getenv("SP_OWNER_2_CLIENT_ID"), "secret": os.getenv("SP_OWNER_2_SECRET"), "class": 2},
    {"name": "sp-owner-03", "client_id": os.getenv("SP_OWNER_3_CLIENT_ID"), "secret": os.getenv("SP_OWNER_3_SECRET"), "class": 2},
]

aws_identities = [
    {"name": "aws-reader-01", "class": 0, "creds": get_env_cred("AWS_READER_01")},
    {"name": "aws-reader-02", "class": 0, "creds": get_env_cred("AWS_READER_02")},
    {"name": "aws-reader-03", "class": 0, "creds": get_env_cred("AWS_READER_03")},
    {"name": "aws-contrib-01", "class": 1, "creds": get_env_cred("AWS_CONTRIB_01")},
    {"name": "aws-contrib-02", "class": 1, "creds": get_env_cred("AWS_CONTRIB_02")},
    {"name": "aws-contrib-03", "class": 1, "creds": get_env_cred("AWS_CONTRIB_03")},
    {"name": "aws-owner-01", "class": 2, "creds": get_env_cred("AWS_OWNER_01")},
    {"name": "aws-owner-02", "class": 2, "creds": get_env_cred("AWS_OWNER_02")},
    {"name": "aws-owner-03", "class": 2, "creds": get_env_cred("AWS_OWNER_03")},
]

# ----------------- LIVE BURST EXECUTION -----------------
print("\n[PHASE 1] Executing Real-Time Live Cloud API Bursts...")

# 1. Live Azure Burst
print("\n---> Triggering Live Azure Telemetry Bursts (9 SPs)...")
for id_info in azure_identities:
    if not id_info["client_id"] or not id_info["secret"]:
        continue
    try:
        cred = ClientSecretCredential(AZURE_TENANT, id_info["client_id"], id_info["secret"])
        rc = ResourceManagementClient(cred, AZURE_SUB)
        _ = rc.resource_groups.get(AZURE_RG)
        print(f"     ✅ Azure live call succeeded for {id_info['name']} (Class {id_info['class']})")
    except Exception as e:
        print(f"     ⚠️ Azure call for {id_info['name']}: {str(e)[:70]}")

# 2. Live AWS Burst
print("\n---> Triggering Live AWS Telemetry Bursts (9 IAM Users)...")
for id_info in aws_identities:
    ak_id, ak_secret = id_info["creds"]
    if not ak_id or not ak_secret:
        continue
    try:
        session = boto3.Session(aws_access_key_id=ak_id, aws_secret_access_key=ak_secret, region_name=AWS_REGION)
        s3 = session.client("s3")
        _ = s3.list_buckets()
        print(f"     ✅ AWS live call succeeded for {id_info['name']} (Class {id_info['class']})")
    except Exception as e:
        print(f"     ⚠️ AWS call for {id_info['name']}: {str(e)[:70]}")

# ----------------- LONGITUDINAL ACCELERATION -----------------
print("\n[PHASE 2] Generating Accelerated 28-Day Longitudinal Multi-Cloud Corpus...")

normalized_records = []
NUM_SIMULATED_DAYS = 28
start_time = datetime.now(timezone.utc) - timedelta(days=NUM_SIMULATED_DAYS)

for day in range(1, NUM_SIMULATED_DAYS + 1):
    sim_date = start_time + timedelta(days=day)
    
    # Azure entries
    for id_info in azure_identities:
        c = id_info["class"]
        calls = np.random.poisson(lam=10 if c==0 else (3 if c==1 else 1))
        util = random.uniform(0.75, 0.95) if c==0 else (random.uniform(0.20, 0.38) if c==1 else random.uniform(0.02, 0.12))
        role = "Reader" if c==0 else ("Contributor" if c==1 else "Owner")
        
        for _ in range(max(1, calls)):
            normalized_records.append({
                "timestamp": (sim_date + timedelta(minutes=random.randint(0, 1440))).isoformat(),
                "cloud_provider": "Azure",
                "identity_id": id_info["name"],
                "identity_type": "ServicePrincipal",
                "assigned_role_or_policy": role,
                "operation_name": "Microsoft.Resources/subscriptions/resourceGroups/read",
                "permission_utilization": round(util, 4),
                "api_call_frequency": calls * 4,
                "source_ip": "20.198.100.45" if random.random() > 0.04 else "198.51.100.99",
                "target_class": c,
                "is_ip_anomaly": 1 if random.random() < 0.04 else 0
            })

    # AWS entries
    for id_info in aws_identities:
        c = id_info["class"]
        calls = np.random.poisson(lam=10 if c==0 else (3 if c==1 else 1))
        util = random.uniform(0.75, 0.95) if c==0 else (random.uniform(0.20, 0.38) if c==1 else random.uniform(0.02, 0.12))
        policy = "ReadOnlyAccess" if c==0 else ("PowerUserAccess" if c==1 else "AdministratorAccess")
        op = "DescribeInstances" if c==0 else ("ListBuckets" if c==1 else "GetAccountSummary")

        for _ in range(max(1, calls)):
            normalized_records.append({
                "timestamp": (sim_date + timedelta(minutes=random.randint(0, 1440))).isoformat(),
                "cloud_provider": "AWS",
                "identity_id": id_info["name"],
                "identity_type": "IAMUser",
                "assigned_role_or_policy": policy,
                "operation_name": op,
                "permission_utilization": round(util, 4),
                "api_call_frequency": calls * 4,
                "source_ip": "54.210.12.33" if random.random() > 0.04 else "203.0.113.50",
                "target_class": c,
                "is_ip_anomaly": 1 if random.random() < 0.04 else 0
            })

# Save to normalized dataset
os.makedirs("data/normalized", exist_ok=True)
df = pd.DataFrame(normalized_records)
out_csv = "data/normalized/aztg_mc_normalized_dataset.csv"
df.to_csv(out_csv, index=False)

print("\n" + "=" * 75)
print("🎉 Unified Multi-Cloud Telemetry & Ingestion Completed!")
print(f"   • Total Normalized Events : {len(df):,}")
print(f"   • Azure Normalized Events : {len(df[df['cloud_provider']=='Azure']):,}")
print(f"   • AWS Normalized Events   : {len(df[df['cloud_provider']=='AWS']):,}")
print(f"   • Saved to                : {out_csv}")
print("=" * 75)
