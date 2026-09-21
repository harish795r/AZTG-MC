import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Detect root directory reliably
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..")) if os.path.basename(CURRENT_DIR) == "ml" else CURRENT_DIR

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))

AZURE_SUB = os.getenv("AZURE_SUBSCRIPTION_ID", "sub-research-8a71c8f9")
AZURE_RG = os.getenv("RESOURCE_GROUP_NAME", "NHI-ZTA-Research")

OUT_DIR = os.path.join(ROOT_DIR, "data", "normalized")
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 80)
print("  AZTG-MC: Realistic Multi-Cloud Telemetry Generator V2")
print(f"  Target Save Directory: {OUT_DIR}")
print("=" * 80)

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# 1. Define 75 Distinct Identities across Azure and AWS
identities = []

# Azure Identities (39 total)
for i in range(1, 19):
    identities.append({"id": f"sp-reader-{i:02d}", "cloud": "Azure", "type": "ServicePrincipal", "role": "Reader", "class": 0})
for i in range(1, 14):
    identities.append({"id": f"sp-contrib-{i:02d}", "cloud": "Azure", "type": "ServicePrincipal", "role": "Contributor", "class": 1})
for i in range(1, 9):
    identities.append({"id": f"sp-owner-{i:02d}", "cloud": "Azure", "type": "ServicePrincipal", "role": "Owner", "class": 2})

# AWS Identities (36 total)
for i in range(1, 18):
    identities.append({"id": f"aws-reader-{i:02d}", "cloud": "AWS", "type": "IAMUser", "role": "ReadOnlyAccess", "class": 0})
for i in range(1, 13):
    identities.append({"id": f"aws-contrib-{i:02d}", "cloud": "AWS", "type": "IAMUser", "role": "PowerUserAccess", "class": 1})
for i in range(1, 8):
    identities.append({"id": f"aws-owner-{i:02d}", "cloud": "AWS", "type": "IAMUser", "role": "AdministratorAccess", "class": 2})

print(f"[+] Provisioned {len(identities)} Distinct Cloud Identities:")
print(f"    • Class 0 (Correctly Privileged)   : 35 identities")
print(f"    • Class 1 (Overprivileged)         : 25 identities")
print(f"    • Class 2 (Severely Overprivileged): 15 identities")

# 2. Simulate 28-Day Telemetry with Intra-Identity Variance & Overlaps
records = []
NUM_DAYS = 28
start_time = datetime.now(timezone.utc) - timedelta(days=NUM_DAYS)

azure_ops = [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Network/networkSecurityGroups/read"
]

aws_ops = [
    "DescribeInstances", "ListBuckets", "GetAccountSummary", "DescribeSecurityGroups",
    "GetObject", "DescribeVolumes"
]

print(f"\n[+] Synthesizing 28-Day Stochastic Telemetry Stream...")

for day_idx in range(NUM_DAYS):
    current_date = start_time + timedelta(days=day_idx)
    is_weekend = 1 if current_date.weekday() >= 5 else 0

    for ident in identities:
        c = ident["class"]
        cloud = ident["cloud"]

        # Base activity frequency with weekend suppression
        base_lam = 14 if c == 0 else (6 if c == 1 else 2)
        if is_weekend:
            base_lam = max(1, base_lam * 0.4)

        # Poisson daily event count
        num_events = np.random.poisson(lam=base_lam)
        if num_events == 0:
            continue

        for _ in range(num_events):
            event_time = current_date + timedelta(minutes=random.randint(0, 1439))
            hour = event_time.hour
            is_off_hours = 1 if (hour < 6 or hour > 21) else 0

            # Feature 1: Overlapping Permission Utilization (Gaussian)
            if c == 0:
                util = np.clip(np.random.normal(0.78, 0.10), 0.45, 0.98)
            elif c == 1:
                util = np.clip(np.random.normal(0.38, 0.14), 0.12, 0.72)
            else:
                util = np.clip(np.random.normal(0.08, 0.06), 0.01, 0.32)

            # Feature 2: API Call Frequency with Jitter
            if c == 0:
                freq = max(5, int(np.random.normal(45, 15)))
            elif c == 1:
                freq = max(2, int(np.random.normal(25, 12)))
            else:
                freq = max(1, int(np.random.normal(8, 6)))

            # Feature 3: Action Entropy
            if c == 0:
                entropy = np.clip(np.random.normal(2.1, 0.4), 1.1, 3.0)
            elif c == 1:
                entropy = np.clip(np.random.normal(1.2, 0.5), 0.4, 2.3)
            else:
                entropy = np.clip(np.random.normal(0.3, 0.25), 0.02, 1.1)

            # Feature 4: Latency & Response Bytes (anchored in live measurements)
            base_latency = 85.0 if cloud == "Azure" else 45.0
            latency = max(8.0, np.random.normal(base_latency, 18.0))
            resp_bytes = max(150, int(np.random.normal(850, 250)))

            # Feature 5: Injected Anomalies & Edge Cases (5% noise)
            is_anomaly = 1 if random.random() < 0.05 else 0
            if is_anomaly:
                is_off_hours = 1
                freq = int(freq * 2.5)
                entropy = max(0.1, entropy * 0.5)

            cardinality = 150 if c == 0 else (2500 if c == 1 else 15000)
            diversity = 3 if c == 0 else (2 if c == 1 else 1)
            if is_anomaly and random.random() < 0.5:
                diversity += 1

            operation = random.choice(azure_ops if cloud == "Azure" else aws_ops)
            status_code = 200 if not is_anomaly or random.random() > 0.3 else 403

            records.append({
                "timestamp": event_time.isoformat(),
                "epoch_time": int(event_time.timestamp()),
                "cloud_provider": cloud,
                "identity_id": ident["id"],
                "identity_uuid": f"uuid-{ident['id']}",
                "identity_type": ident["type"],
                "assigned_role_or_policy": ident["role"],
                "target_class": c,
                "source_ip": "20.198.100.45" if cloud == "Azure" else "54.210.12.33",
                "source_region": "Central India" if cloud == "Azure" else "ap-south-1",
                "user_agent": "azure-sdk-for-python/1.28.0" if cloud == "Azure" else "Boto3/1.34.0",
                "tls_version": "TLSv1.3",
                "is_ip_anomaly": is_anomaly,
                "hour_of_day": hour,
                "day_of_week": event_time.weekday(),
                "is_off_hours": is_off_hours,
                "is_weekend": is_weekend,
                "latency_ms": round(latency, 3),
                "service_category": "ResourceManagement" if cloud == "Azure" else "AmazonS3",
                "operation_name": operation,
                "http_method": "GET" if cloud == "Azure" else "POST",
                "api_version": "2021-04-01" if cloud == "Azure" else "2006-03-01",
                "resource_scope": f"/subscriptions/{AZURE_SUB}/rg/{AZURE_RG}" if cloud == "Azure" else "arn:aws:s3:::*",
                "http_status": status_code,
                "error_detail": "None" if status_code == 200 else "AccessDenied",
                "response_bytes": resp_bytes,
                "permission_utilization": round(util, 4),
                "api_call_frequency": freq,
                "entropy_score": round(entropy, 3),
                "privilege_cardinality": cardinality,
                "service_diversity_count": diversity
            })

df_v2 = pd.DataFrame(records)

# 3. Explicitly Save and Verify Files
main_file = os.path.join(OUT_DIR, "aztg_mc_deep_telemetry.csv")
v2_file = os.path.join(OUT_DIR, "aztg_mc_deep_telemetry_v2.csv")

df_v2.to_csv(main_file, index=False)
df_v2.to_csv(v2_file, index=False)

print("\n" + "=" * 80)
if os.path.exists(main_file):
    size_kb = os.path.getsize(main_file) / 1024
    print(f"✅ SUCCESS: File written to disk!")
    print(f"   • Primary Dataset Path : {main_file}")
    print(f"   • File Size on Disk    : {size_kb:.2f} KB")
    print(f"   • Total Records Saved  : {len(df_v2):,} rows")
    print(f"   • Total Features Saved : {df_v2.shape[1]} columns")
else:
    print(f"❌ ERROR: File could not be written to {main_file}")
print("=" * 80)
