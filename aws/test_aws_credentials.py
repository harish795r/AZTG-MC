import os
import boto3
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")

print("=" * 75)
print("  AZTG-MC: AWS IAM Credentials Verification Test")
print(f"  Target Region: {REGION}")
print("=" * 75)

def get_env_cred(prefix):
    key = os.getenv(f"{prefix}_KEY") or os.getenv(f"{prefix.replace('_0', '_')}_KEY")
    secret = os.getenv(f"{prefix}_SECRET") or os.getenv(f"{prefix.replace('_0', '_')}_SECRET")
    return key, secret

aws_identities = [
    {"name": "aws-reader-01",  "class": 0, "expected_role": "ReadOnlyAccess",      "creds": get_env_cred("AWS_READER_01")},
    {"name": "aws-reader-02",  "class": 0, "expected_role": "ReadOnlyAccess",      "creds": get_env_cred("AWS_READER_02")},
    {"name": "aws-reader-03",  "class": 0, "expected_role": "ReadOnlyAccess",      "creds": get_env_cred("AWS_READER_03")},
    {"name": "aws-contrib-01", "class": 1, "expected_role": "PowerUserAccess",     "creds": get_env_cred("AWS_CONTRIB_01")},
    {"name": "aws-contrib-02", "class": 1, "expected_role": "PowerUserAccess",     "creds": get_env_cred("AWS_CONTRIB_02")},
    {"name": "aws-contrib-03", "class": 1, "expected_role": "PowerUserAccess",     "creds": get_env_cred("AWS_CONTRIB_03")},
    {"name": "aws-owner-01",   "class": 2, "expected_role": "AdministratorAccess", "creds": get_env_cred("AWS_OWNER_01")},
    {"name": "aws-owner-02",   "class": 2, "expected_role": "AdministratorAccess", "creds": get_env_cred("AWS_OWNER_02")},
    {"name": "aws-owner-03",   "class": 2, "expected_role": "AdministratorAccess", "creds": get_env_cred("AWS_OWNER_03")},
]

results = []

for id_info in aws_identities:
    name = id_info["name"]
    expected = id_info["expected_role"]
    ak_id, ak_secret = id_info["creds"]

    if not ak_id or not ak_secret:
        results.append((name, expected, "MISSING IN .ENV", "N/A", "❌ Key/Secret not found in .env"))
        continue

    # Obfuscate key for safe display
    masked_key = f"{ak_id[:4]}...{ak_id[-4:]}" if len(ak_id) >= 8 else "INVALID"

    try:
        session = boto3.Session(
            aws_access_key_id=ak_id,
            aws_secret_access_key=ak_secret,
            region_name=REGION
        )
        sts = session.client("sts")
        caller_identity = sts.get_caller_identity()
        arn = caller_identity["Arn"]
        account = caller_identity["Account"]
        results.append((name, expected, "VALID ✅", masked_key, f"Account: {account}"))
    except ClientError as e:
        err_code = e.response.get("Error", {}).get("Code", "AuthError")
        err_msg = e.response.get("Error", {}).get("Message", str(e))
        results.append((name, expected, f"FAILED ❌ ({err_code})", masked_key, err_msg[:40]))
    except Exception as e:
        results.append((name, expected, "FAILED ❌", masked_key, str(e)[:40]))

print(f"\n{'Identity':<16} | {'Expected Policy':<20} | {'Status':<14} | {'Access Key':<12} | {'Details'}")
print("-" * 95)
for name, policy, status, key, details in results:
    print(f"{name:<16} | {policy:<20} | {status:<14} | {key:<12} | {details}")

print("-" * 95)
success_count = sum(1 for r in results if "VALID" in r[2])
print(f"\nSummary: {success_count}/9 AWS IAM identities authenticated successfully.")
print("=" * 75)
