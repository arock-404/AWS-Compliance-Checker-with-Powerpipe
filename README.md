# AWS-Compliance-Checker-with-Powerpipe
This project automates the process of scanning AWS resources for compliance using Powerpipe. The script accepts AWS credentials, runs a compliance benchmark, processes the output, and stores the results in a PostgreSQL database.

## Features
- AWS Compliance Scanning: Uses Powerpipe to perform compliance checks based on predefined benchmarks.
- Database Storage: Saves the raw JSON output and parsed results into a PostgreSQL database for further analysis.
- REST API: A Flask-based API that allows triggering compliance scans via HTTP requests.
- UUID to BigInt Conversion: Generates unique request IDs in a format compatible with databases.
- Control Extraction: Recursively extracts compliance control details from Powerpipe's output.

## Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Powerpipe installed and accessible from /usr/local/bin/powerpipe
- Flask, psycopg2, and other required Python libraries

## Installation

#### Step 1: Clone the Repository
```
git clone https://github.com/arock-404/AWS-Compliance-Checker-with-Powerpipe.git

```
#### Step 2: Install Dependencies
```
pip install -r requirements.txt
```

#### Configure PostgreSQL Database
Create a PostgreSQL database and table:
```sql
CREATE DATABASE aws_compliance;
\c aws_compliance

CREATE TABLE json_storage (
    requestid BIGINT PRIMARY KEY,
    added_date TIMESTAMP NOT NULL,
    json_result JSONB,
    parsed_result JSONB
);

```

#### Step 4: Environment Configuration
Ensure Powerpipe is installed on the system and accessible. Update the PostgreSQL credentials and host in the script:
```python
psycopg2.connect(
    dbname="aws_compliance",
    user="postgres",          # Replace with your PostgreSQL username
    password="your_password", # Replace with your PostgreSQL password
    host="your_database_host" # Replace with your PostgreSQL host
)

```
## Usage
### Run the Flask Server
Start the API server using:
```
python app.py
```

### Trigger a Compliance Scan
Send a POST request to the `/run_powerpipe/` endpoint with AWS credentials:
```json
POST http://127.0.0.1:5000/run_powerpipe/
Content-Type: application/json

{
  "AWS_ACCESS_KEY_ID": "your-access-key-id",
  "AWS_SECRET_ACCESS_KEY": "your-secret-access-key"
}

```

