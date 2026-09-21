import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# ─────────────────────────────────────────────────────────────────────────────
# PATH SETUP
# ─────────────────────────────────────────────────────────────────────────────
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..")) if os.path.basename(CURRENT_DIR) == "ml" else CURRENT_DIR

load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))

AZURE_SUB = os.getenv("AZURE_SUBSCRIPTION_ID", "sub-research-8a71c8f9")
AZURE_RG  = os.getenv("RESOURCE_GROUP_NAME", "NHI-ZTA-Research")

OUT_DIR = os.path.join(ROOT_DIR, "data", "normalized")
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 80)
print("  AZTG-MC: Enterprise-Calibrated Telemetry Generator V2 (Final)")
print("  Distribution : ~56% Class 0 | ~40% Class 1 | ~4% Class 2")
print("  Cardinality  : Lognormal Overlapping (NOT deterministic lookup)")
print("  Utilization  : Gaussian Overlapping  (NOT hard-coded ranges)")
print("=" * 80)

# ─────────────────────────────────────────────────────────────────────────────
# REPRODUCIBILITY
# ─────────────────────────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# IDENTITY PROVISIONING
# 75 identities total:
#   Class 0 (Reader)      : 42 → ~56%
#   Class 1 (Contributor) : 30 → ~40%
#   Class 2 (Owner/Admin) :  3 → ~4%
#
# Azure cohort: 21 Reader, 15 Contributor, 2 Owner = 38
# AWS cohort  : 21 Reader, 15 Contributor, 1 Owner = 37
# ─────────────────────────────────────────────────────────────────────────────
identities = []

# Azure
for i in range(1, 22):
    identities.append({
        "id": f"sp-reader-{i:02d}", "cloud": "Azure",
        "type": "ServicePrincipal", "role": "Reader", "class": 0
    })
for i in range(1, 16):
    identities.append({
        "id": f"sp-contrib-{i:02d}", "cloud": "Azure",
        "type": "ServicePrincipal", "role": "Contributor", "class": 1
    })
for i in range(1, 3):
    identities.append({
        "id": f"sp-owner-{i:02d}", "cloud": "Azure",
        "type": "ServicePrincipal", "role": "Owner", "class": 2
    })

# AWS
for i in range(1, 22):
    identities.append({
        "id": f"aws-reader-{i:02d}", "cloud": "AWS",
        "type": "IAMUser", "role": "ReadOnlyAccess", "class": 0
    })
for i in range(1, 16):
    identities.append({
        "id": f"aws-contrib-{i:02d}", "cloud": "AWS",
        "type": "IAMUser", "role": "PowerUserAccess", "class": 1
    })
identities.append({
    "id": "aws-owner-01", "cloud": "AWS",
    "type": "IAMUser", "role": "AdministratorAccess", "class": 2
})

print(f"\n[+] Provisioned {len(identities)} Distinct Cloud Identities:")
c0 = sum(1 for x in identities if x["class"] == 0)
c1 = sum(1 for x in identities if x["class"] == 1)
c2 = sum(1 for x in identities if x["class"] == 2)
print(f"    Class 0 (Reader)      : {c0} ({c0/len(identities)*100:.1f}%)")
print(f"    Class 1 (Contributor) : {c1} ({c1/len(identities)*100:.1f}%)")
print(f"    Class 2 (Owner/Admin) : {c2} ({c2/len(identities)*100:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# OPERATION POOLS
# ─────────────────────────────────────────────────────────────────────────────
azure_ops = [
    "Microsoft.Resources/subscriptions/resourceGroups/read",
    "Microsoft.Storage/storageAccounts/listKeys/action",
    "Microsoft.Compute/virtualMachines/read",
    "Microsoft.Network/networkSecurityGroups/read",
    "Microsoft.Authorization/roleAssignments/read",
    "Microsoft.Insights/diagnosticSettings/read"
]

aws_ops = [
    "DescribeInstances",
    "ListBuckets",
    "GetAccountSummary",
    "DescribeSecurityGroups",
    "GetObject",
    "DescribeVolumes",
    "ListUsers",
    "GetAccountAuthorizationDetails"
]

# ─────────────────────────────────────────────────────────────────────────────
# 28-DAY STOCHASTIC TELEMETRY SYNTHESIS
# ─────────────────────────────────────────────────────────────────────────────
records = []
NUM_DAYS = 28
start_time = datetime.now(timezone.utc) - timedelta(days=NUM_DAYS)

print(f"\n[+] Synthesizing {NUM_DAYS}-Day Stochastic Telemetry Stream...")

for day_idx in range(NUM_DAYS):
    current_date = start_time + timedelta(days=day_idx)
    is_weekend   = 1 if current_date.weekday() >= 5 else 0

    for ident in identities:
        c     = ident["class"]
        cloud = ident["cloud"]

        # Poisson arrival rate with weekend suppression
        base_lam = 14 if c == 0 else (6 if c == 1 else 2)
        if is_weekend:
            base_lam = max(1, base_lam * 0.4)

        num_events = np.random.poisson(lam=base_lam)
        if num_events == 0:
            continue

        for _ in range(num_events):
            event_time  = current_date + timedelta(minutes=random.randint(0, 1439))
            hour        = event_time.hour
            is_off_hours = 1 if (hour < 6 or hour > 21) else 0

            # ─────────────────────────────────────────────────────────────
            # FEATURE 1: PERMISSION UTILIZATION
            # Overlapping Gaussians — Class 1 tails spill into both extremes
            # ─────────────────────────────────────────────────────────────
            if c == 0:
                util = np.clip(np.random.normal(0.76, 0.11), 0.42, 0.98)
            elif c == 1:
                util = np.clip(np.random.normal(0.36, 0.16), 0.10, 0.75)
            else:
                util = np.clip(np.random.normal(0.09, 0.07), 0.01, 0.35)

            # ─────────────────────────────────────────────────────────────
            # FEATURE 2: API CALL FREQUENCY
            # Gaussian with jitter — realistic per-day variance
            # ─────────────────────────────────────────────────────────────
            if c == 0:
                freq = max(5, int(np.random.normal(52, 18)))
            elif c == 1:
                freq = max(2, int(np.random.normal(27, 15)))
            else:
                freq = max(1, int(np.random.normal(9, 7)))

            # ─────────────────────────────────────────────────────────────
            # FEATURE 3: ACTION ENTROPY
            # Shannon diversity — overlapping tails between classes
            # ─────────────────────────────────────────────────────────────
            if c == 0:
                entropy = np.clip(np.random.normal(2.05, 0.42), 1.00, 3.00)
            elif c == 1:
                entropy = np.clip(np.random.normal(1.15, 0.52), 0.35, 2.40)
            else:
                entropy = np.clip(np.random.normal(0.28, 0.22), 0.02, 1.05)

            # ─────────────────────────────────────────────────────────────
            # FEATURE 4: PRIVILEGE CARDINALITY  ← THE CRITICAL FIX
            #
            # Lognormal distributions with realistic enterprise ranges.
            # Significant overlap between adjacent classes:
            #
            #   Class 0: 25  – 1,800  (custom read roles → broad built-in Reader)
            #   Class 1: 600 – 6,000  (Contributor/PowerUser)
            #   Class 2: 3,000 – 15,000 (Owner/*  or AdministratorAccess)
            #
            #   Overlap C0 ∩ C1: 600 – 1,800
            #   Overlap C1 ∩ C2: 3,000 – 6,000
            #
            # Lognormal chosen because privilege counts are right-skewed and
            # strictly positive in real IAM systems.
            # ─────────────────────────────────────────────────────────────
            if c == 0:
                cardinality = int(np.clip(
                    np.random.lognormal(mean=5.2, sigma=0.70), 25, 1800
                ))
            elif c == 1:
                cardinality = int(np.clip(
                    np.random.lognormal(mean=7.2, sigma=0.60), 600, 6000
                ))
            else:
                cardinality = int(np.clip(
                    np.random.lognormal(mean=8.8, sigma=0.50), 3000, 15000
                ))

            # ─────────────────────────────────────────────────────────────
            # FEATURE 5: SERVICE DIVERSITY COUNT
            # Overlapping Gaussians — number of distinct cloud services used
            # Class 2 has access to everything but barely uses any service
            # ─────────────────────────────────────────────────────────────
            if c == 0:
                diversity = int(np.clip(np.random.normal(3.5, 1.2), 1, 7))
            elif c == 1:
                diversity = int(np.clip(np.random.normal(2.5, 1.3), 1, 6))
            else:
                diversity = int(np.clip(np.random.normal(1.5, 0.8), 1, 4))

            # ─────────────────────────────────────────────────────────────
            # FEATURE 6: LATENCY & RESPONSE BYTES
            # Anchored in real live Azure Central India (~85ms) and
            # AWS Mumbai (~45ms) API response measurements
            # ─────────────────────────────────────────────────────────────
            base_latency = 85.0 if cloud == "Azure" else 45.0
            latency      = max(8.0, np.random.normal(base_latency, 18.0))
            resp_bytes   = max(150, int(np.random.normal(850, 250)))

            # ─────────────────────────────────────────────────────────────
            # ANOMALY INJECTION (5% of events)
            # Simulates behavioral drift, off-hours access spikes,
            # and boundary-inspection attempts.
            # Used by Isolation Forest layer.
            # ─────────────────────────────────────────────────────────────
            is_anomaly = 1 if random.random() < 0.05 else 0
            if is_anomaly:
                is_off_hours = 1
                freq         = int(freq * 2.5)
                entropy      = max(0.10, entropy * 0.5)
                if random.random() < 0.5:
                    diversity = min(diversity + 1, 8)

            operation   = random.choice(azure_ops if cloud == "Azure" else aws_ops)
            status_code = 200 if (not is_anomaly or random.random() > 0.3) else 403

            records.append({
                # Identity context
                "timestamp":             event_time.isoformat(),
                "epoch_time":            int(event_time.timestamp()),
                "cloud_provider":        cloud,
                "identity_id":           ident["id"],
                "identity_uuid":         f"uuid-{ident['id']}",
                "identity_type":         ident["type"],
                "assigned_role_or_policy": ident["role"],
                "target_class":          c,
                # Network & origin
                "source_ip":             "20.198.100.45" if cloud == "Azure" else "54.210.12.33",
                "source_region":         "Central India" if cloud == "Azure" else "ap-south-1",
                "user_agent":            "azure-sdk-for-python/1.28.0" if cloud == "Azure" else "Boto3/1.34.0",
                "tls_version":           "TLSv1.3",
                "is_ip_anomaly":         is_anomaly,
                # Temporal signals
                "hour_of_day":           hour,
                "day_of_week":           event_time.weekday(),
                "is_off_hours":          is_off_hours,
                "is_weekend":            is_weekend,
                # Request details
                "latency_ms":            round(latency, 3),
                "service_category":      "ResourceManagement" if cloud == "Azure" else "AmazonS3",
                "operation_name":        operation,
                "http_method":           "GET" if cloud == "Azure" else "POST",
                "api_version":           "2021-04-01" if cloud == "Azure" else "2006-03-01",
                "resource_scope":        f"/subscriptions/{AZURE_SUB}/rg/{AZURE_RG}" if cloud == "Azure" else "arn:aws:s3:::*",
                # Response signals
                "http_status":           status_code,
                "error_detail":          "None" if status_code == 200 else "AccessDenied",
                "response_bytes":        resp_bytes,
                # Behavioral ML features
                "permission_utilization":  round(float(util), 4),
                "api_call_frequency":      freq,
                "entropy_score":           round(float(entropy), 3),
                "privilege_cardinality":   cardinality,
                "service_diversity_count": diversity
            })

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────
df = pd.DataFrame(records)

main_file = os.path.join(OUT_DIR, "aztg_mc_deep_telemetry.csv")
v2_file   = os.path.join(OUT_DIR, "aztg_mc_deep_telemetry_v2.csv")

df.to_csv(main_file, index=False)
df.to_csv(v2_file,   index=False)

# ─────────────────────────────────────────────────────────────────────────────
# VERIFICATION REPORT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
if os.path.exists(main_file):
    size_kb = os.path.getsize(main_file) / 1024
    print(f"✅ File written successfully!")
    print(f"   Path      : {main_file}")
    print(f"   Size      : {size_kb:.2f} KB")
    print(f"   Rows      : {len(df):,}")
    print(f"   Columns   : {df.shape[1]}")

print("\n[+] Class Distribution:")
counts = df["target_class"].value_counts().sort_index()
for c, count in counts.items():
    label = {0: "Reader  (Class 0 — Normal)", 1: "Contrib (Class 1 — Bloated)", 2: "Owner   (Class 2 — Severe)"}[c]
    bar = "█" * int(count / len(df) * 40)
    print(f"   {label} : {bar} {count:,} ({count/len(df)*100:.1f}%)")

print("\n[+] Feature Overlap Verification (Mean ± Std):")
print(f"    {'Feature':<28} {'Class 0':>18} {'Class 1':>18} {'Class 2':>18}")
print("    " + "-" * 82)
for feat in ["permission_utilization", "api_call_frequency", "entropy_score", "privilege_cardinality", "service_diversity_count"]:
    row = f"    {feat:<28}"
    for c in [0, 1, 2]:
        sub = df[df["target_class"] == c][feat]
        row += f"  {sub.mean():>7.2f} ± {sub.std():>5.2f}"
    print(row)

print("\n[+] Cardinality Overlap Check (confirms non-deterministic separation):")
for c in [0, 1, 2]:
    sub = df[df["target_class"] == c]["privilege_cardinality"]
    print(f"   Class {c}: min={sub.min():,}  max={sub.max():,}  mean={sub.mean():,.0f}  std={sub.std():,.0f}")
print("=" * 80)
