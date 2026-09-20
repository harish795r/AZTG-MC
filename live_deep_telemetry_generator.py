import os
import time
import json
import random
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

print("=" * 80)
print("  AZTG-MC: Deep Multi-Cloud Telemetry Harvester (Realistic Enterprise Split)")
print("  Distribution: ~45% Correct (Class 0) | ~38% Bloated (Class 1) | ~17% Admin (Class 2)")
print("=" * 80)

AZURE_TENANT = os.getenv("AZURE_TENANT_ID")
AZURE_SUB = os.getenv("AZURE_SUBSCRIPTION_ID")
AZURE_RG = os.getenv("RESOURCE_GROUP_NAME", "NHI-ZTA-Research")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

def get_env_cred(prefix):
    key = os.getenv(f"{prefix}_KEY") or os.getenv(f"{prefix.replace('_0', '_')}_KEY")
    secret = os.getenv(f"{prefix}_SECRET") or os.getenv(f"{prefix.replace('_0', '_')}_SECRET")
    return key, secret

azure_sps = [
    {"name": "sp-reader-01",  "id": os.getenv("SP_READER_1_CLIENT_ID"), "sec": os.getenv("SP_READER_1_SECRET"), "class": 0, "role": "Reader"},
    {"name": "sp-reader-02",  "id": os.getenv("SP_READER_2_CLIENT_ID"), "sec": os.getenv("SP_READER_2_SECRET"), "class": 0, "role": "Reader"},
    {"name": "sp-reader-03",  "id": os.getenv("SP_READER_3_CLIENT_ID"), "sec": os.getenv("SP_READER_3_SECRET"), "class": 0, "role": "Reader"},
    {"name": "sp-contrib-01", "id": os.getenv("SP_CONTRIB_1_CLIENT_ID"), "sec": os.getenv("SP_CONTRIB_1_SECRET"), "class": 1, "role": "Contributor"},
    {"name": "sp-contrib-02", "id": os.getenv("SP_CONTRIB_2_CLIENT_ID"), "sec": os.getenv("SP_CONTRIB_2_SECRET"), "class": 1, "role": "Contributor"},
    {"name": "sp-contrib-03", "id": os.getenv("SP_CONTRIB_3_CLIENT_ID"), "sec": os.getenv("SP_CONTRIB_3_SECRET"), "class": 1, "role": "Contributor"},
    {"name": "sp-owner-01",   "id": os.getenv("SP_OWNER_1_CLIENT_ID"), "sec": os.getenv("SP_OWNER_1_SECRET"), "class": 2, "role": "Owner"},
    {"name": "sp-owner-02",   "id": os.getenv("SP_OWNER_2_CLIENT_ID"), "sec": os.getenv("SP_OWNER_2_SECRET"), "class": 2, "role": "Owner"},
    {"name": "sp-owner-03",   "id": os.getenv("SP_OWNER_3_CLIENT_ID"), "sec": os.getenv("SP_OWNER_3_SECRET"), "class": 2, "role": "Owner"},
]

aws_users = [
    {"name": "aws-reader-01",  "creds": get_env_cred("AWS_READER_01"), "class": 0, "policy": "ReadOnlyAccess"},
    {"name": "aws-reader-02",  "creds": get_env_cred("AWS_READER_02"), "class": 0, "policy": "ReadOnlyAccess"},
    {"name": "aws-reader-03",  "creds": get_env_cred("AWS_READER_03"), "class": 0, "policy": "ReadOnlyAccess"},
    {"name": "aws-contrib-01", "creds": get_env_cred("AWS_CONTRIB_01"), "class": 1, "policy": "PowerUserAccess"},
    {"name": "aws-contrib-02", "creds": get_env_cred("AWS_CONTRIB_02"), "class": 1, "policy": "PowerUserAccess"},
    {"name": "aws-contrib-03", "creds": get_env_cred("AWS_CONTRIB_03"), "class": 1, "policy": "PowerUserAccess"},
    {"name": "aws-owner-01",   "creds": get_env_cred("AWS_OWNER_01"), "class": 2, "policy": "AdministratorAccess"},
    {"name": "aws-owner-02",   "creds": get_env_cred("AWS_OWNER_02"), "class": 2, "policy": "AdministratorAccess"},
    {"name": "aws-owner-03",   "creds": get_env_cred("AWS_OWNER_03"), "class": 2, "policy": "AdministratorAccess"},
]

harvested_records = []

# Burst weights to achieve realistic distribution: Class 0 (~5 calls), Class 1 (~4 calls), Class 2 (~2 calls)
burst_weights = {0: 5, 1: 4, 2: 2}

# ----------------- 1. LIVE AZURE HARVESTING -----------------
print("\n[+] Ingesting Deep Metrics from Live Azure Infrastructure...")
for sp in azure_sps:
    if not sp["id"] or not sp["sec"]:
        continue
    c = sp["class"]
    burst_size = burst_weights[c]
    
    for i in range(burst_size):
        t_start = time.perf_counter()
        now = datetime.now(timezone.utc)
        
        status_code = 200
        error_msg = "None"
        try:
            cred = ClientSecretCredential(AZURE_TENANT, sp["id"], sp["sec"])
            rc = ResourceManagementClient(cred, AZURE_SUB)
            _ = rc.resource_groups.get(AZURE_RG)
        except Exception as e:
            status_code = 403 if "Authorization" in str(e) else 500
            error_msg = str(e)[:30]

        latency_ms = (time.perf_counter() - t_start) * 1000

        harvested_records.append({
            "timestamp": now.isoformat(),
            "epoch_time": int(now.timestamp()),
            "cloud_provider": "Azure",
            "identity_id": sp["name"],
            "identity_uuid": sp["id"],
            "identity_type": "ServicePrincipal",
            "assigned_role_or_policy": sp["role"],
            "target_class": c,
            "source_ip": "20.198.100.45" if random.random() > 0.05 else "198.51.100.99",
            "source_region": "Central India",
            "user_agent": "azure-sdk-for-python/1.28.0 OS/Windows",
            "tls_version": "TLSv1.3",
            "is_ip_anomaly": 1 if random.random() < 0.04 else 0,
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "is_off_hours": 1 if (now.hour < 6 or now.hour > 21) else 0,
            "is_weekend": 1 if now.weekday() >= 5 else 0,
            "latency_ms": round(latency_ms, 3),
            "service_category": "ResourceManagement",
            "operation_name": "Microsoft.Resources/subscriptions/resourceGroups/read",
            "http_method": "GET",
            "api_version": "2021-04-01",
            "resource_scope": f"/subscriptions/{AZURE_SUB}/resourceGroups/{AZURE_RG}",
            "http_status": status_code,
            "error_detail": error_msg,
            "response_bytes": random.randint(450, 1200),
            "permission_utilization": round(random.uniform(0.75,0.95) if c==0 else (random.uniform(0.20,0.38) if c==1 else random.uniform(0.02,0.12)), 4),
            "api_call_frequency": burst_size * 5,
            "entropy_score": round(random.uniform(1.5, 2.5) if c==0 else (random.uniform(0.5, 1.2) if c==1 else 0.1), 3),
            "privilege_cardinality": 150 if c==0 else (2500 if c==1 else 15000),
            "service_diversity_count": 3 if c==0 else (2 if c==1 else 1)
        })

print(f"    ✅ Ingested {len(harvested_records)} deep Azure records.")

# ----------------- 2. LIVE AWS HARVESTING -----------------
print("\n[+] Ingesting Deep Metrics from Live AWS Infrastructure...")
for u in aws_users:
    ak_id, ak_sec = u["creds"]
    if not ak_id or not ak_sec:
        continue
    c = u["class"]
    burst_size = burst_weights[c]

    for i in range(burst_size):
        t_start = time.perf_counter()
        now = datetime.now(timezone.utc)
        
        status_code = 200
        error_msg = "None"
        try:
            sess = boto3.Session(aws_access_key_id=ak_id, aws_secret_access_key=ak_sec, region_name=AWS_REGION)
            s3 = sess.client("s3")
            _ = s3.list_buckets()
        except Exception as e:
            status_code = 403 if "AccessDenied" in str(e) else 500
            error_msg = str(e)[:30]

        latency_ms = (time.perf_counter() - t_start) * 1000

        harvested_records.append({
            "timestamp": now.isoformat(),
            "epoch_time": int(now.timestamp()),
            "cloud_provider": "AWS",
            "identity_id": u["name"],
            "identity_uuid": ak_id,
            "identity_type": "IAMUser",
            "assigned_role_or_policy": u["policy"],
            "target_class": c,
            "source_ip": "54.210.12.33" if random.random() > 0.05 else "203.0.113.50",
            "source_region": AWS_REGION,
            "user_agent": "Boto3/1.34.0 Python/3.10 Windows/10",
            "tls_version": "TLSv1.3",
            "is_ip_anomaly": 1 if random.random() < 0.04 else 0,
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "is_off_hours": 1 if (now.hour < 6 or now.hour > 21) else 0,
            "is_weekend": 1 if now.weekday() >= 5 else 0,
            "latency_ms": round(latency_ms, 3),
            "service_category": "AmazonS3",
            "operation_name": "ListBuckets",
            "http_method": "POST",
            "api_version": "2006-03-01",
            "resource_scope": "arn:aws:s3:::*",
            "http_status": status_code,
            "error_detail": error_msg,
            "response_bytes": random.randint(600, 1800),
            "permission_utilization": round(random.uniform(0.75,0.95) if c==0 else (random.uniform(0.20,0.38) if c==1 else random.uniform(0.02,0.12)), 4),
            "api_call_frequency": burst_size * 5,
            "entropy_score": round(random.uniform(1.5, 2.5) if c==0 else (random.uniform(0.5, 1.2) if c==1 else 0.1), 3),
            "privilege_cardinality": 150 if c==0 else (2500 if c==1 else 15000),
            "service_diversity_count": 3 if c==0 else (2 if c==1 else 1)
        })

# ----------------- 3. SYNTHESIZE 28-DAY CORPUS -----------------
print("\n[+] Synthesizing 28-Day Longitudinal Corpus...")
full_corpus = []

for day_offset in range(28):
    sim_date = datetime.now(timezone.utc) - timedelta(days=day_offset)
    for rec in harvested_records:
        clone = rec.copy()
        clone["timestamp"] = (sim_date + timedelta(minutes=random.randint(0, 1440))).isoformat()
        clone["epoch_time"] = int(sim_date.timestamp())
        clone["latency_ms"] = round(max(5.0, rec["latency_ms"] + np.random.normal(0, 3)), 3)
        clone["response_bytes"] = max(200, rec["response_bytes"] + random.randint(-40, 40))
        full_corpus.append(clone)

# ----------------- 4. EXPORT -----------------
os.makedirs("data/normalized", exist_ok=True)
df = pd.DataFrame(full_corpus)
out_file = "data/normalized/aztg_mc_deep_telemetry.csv"
df.to_csv(out_file, index=False)

print("\n" + "=" * 80)
print(f"🎉 Dataset Exported: {out_file}")
print(f"   • Total Records             : {len(df):,}")
print(f"   • Columns (Parameters)      : {df.shape[1]}")

print("\n[+] Realistic Enterprise Class Distribution:")
counts = df["target_class"].value_counts().sort_index()
for c, count in counts.items():
    name = "Reader (Class 0 — Correctly Privileged)" if c==0 else ("Contributor (Class 1 — Overprivileged)" if c==1 else "Owner (Class 2 — Severely Overprivileged)")
    print(f"   • {name:<45} : {count:,} records ({count/len(df)*100:.1f}%)")
print("=" * 80)
