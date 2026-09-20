Python-based Azure telemetry workflow for:
- simulating service principal activity in Azure,
- verifying telemetry pipeline output in Blob Storage,
- fetching and parsing live logs, and
- inspecting identity activity from extracted records.

## Project Structure

`/home/runner/work/AZTG-MC/AZTG-MC/azure`

- `azure_simulator.py` – generates stochastic Azure API activity using Reader/Contributor/Owner identities.
- `check_azure_pipeline.py` – validates storage connectivity and previews stored telemetry logs.
- `fetch_azure_logs.py` – downloads blobs and extracts telemetry into local JSON.
- `read_storage_logs.py` – quick check of available containers/blobs and sample content.
- `verify_identities.py` – summarizes service principal identity usage from extracted logs.

## Prerequisites

- Python 3.9+
- Azure tenant and subscription
- Service principal credentials configured in `.env`
- Access to the Azure Storage account used for telemetry logs

## Setup

1. Go to the repository:
   ```bash
   cd /home/runner/work/AZTG-MC/AZTG-MC
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install python-dotenv azure-identity azure-mgmt-storage azure-mgmt-resource azure-storage-blob numpy pandas
   ```
4. Create your env file:
   ```bash
   cp .env.example .env
   ```
5. Fill `.env` with valid Azure tenant, subscription, and service principal credentials.

## Usage

From `/home/runner/work/AZTG-MC/AZTG-MC`:

1. Simulate telemetry generation:
   ```bash
   python azure/azure_simulator.py
   ```
2. Validate telemetry pipeline output:
   ```bash
   python azure/check_azure_pipeline.py
   ```
3. Download and extract logs locally:
   ```bash
   python azure/fetch_azure_logs.py
   ```
4. Inspect extracted identity activity:
   ```bash
   python azure/verify_identities.py
   ```
5. Optional raw storage preview:
   ```bash
   python azure/read_storage_logs.py
   ```

## Output Artifacts

- Raw downloaded files: `data/azure/raw_downloaded_logs/`
- Combined extracted records: `data/azure/live_extracted_azure_records.json`

## Notes

- Some scripts expect `SP_OWNER_1_*` credentials for storage diagnostics and retrieval.
- Missing blob-level role assignments (for example, Storage Blob Data Reader) can limit content preview/extraction.
