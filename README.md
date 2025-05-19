# Goal
Build an end-to-end ML system to analyse and predict resale flat prices across Singapore. The system will provide comprehensive market insights and location-specific comparisons through analysis of transaction data and property characteristics, supplemented with AI-generated natural language explanations.

# Tech Stack
Prefer:
- python fastapi for API
- postgres for database
- docker for containerization
- nextJS + tailwindCSS for frontend

# Service
- have an endpoint for receiving a question
- within the service it should iteratively decide if it should any of these functions:
  - query the database for data
  - run an exploratory analysis
  - make a prediction
  - make a recommendation
  - summarize all of the findings so far in a report formatted in markdown
- the report should be fetched from a separate endpoint
- no need for authentication (simplification for now)

# Database
- should contain the following data from data.gov.sg:
  - Resale Flat Prices. This is to allow us to train a model to predict flat prices
  - Completion Status of HDB Residential Units by Town/Estate. This is to allow us to know which estates have BTO flats built in them recently, and which do not.

# Modeling
- Use XGBoost for high quality predictions
- Use linear regression for interpretable analyses

# Monitoring
- should implement and/or recommend monitoring metrics
- should implement automated testing and establish operational processes, (e.g., model versioning and edge case testing)

# Tests
- Should have unit tests where appropriate
- Should have endpoint tests where appropriate

# Folder Structure
- `app` - contains the fastapi app
- `data` - contains the data (git LFS) and processing scripts
- `models` - contains the model and model training scripts
- `tests` - contains the tests
- `utils` - contains the utils (e.g. logging)
- `README.md` - contains the readme
- `Dockerfile` - contains the dockerfile
- `requirements.txt` - contains the dependencies

# Setup Instructions

## Environment Variables
Create a `.env` file in the root directory with the following variables:
```
# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=hdb_data
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# Claude API Configuration
CLAUDE_API_KEY=your_claude_api_key_here
```

## Docker Setup
1. Start the Docker daemon (if not already running):
```bash
# On macOS
open -a Docker

# On Windows
# Start Docker Desktop manually

# On Linux
sudo systemctl start docker
```

2. Start the PostgreSQL container:
```bash
docker compose up -d
```

## Data Import Process
The system uses HDB resale price data and completion status data from data.gov.sg. Follow these steps to download and import the data:

1. **Download and Process Data** (if not already done):
```bash
python data/download_data.py
```
This script will:
- Download raw data files from data.gov.sg into the `data/raw` directory
- Process and clean the data
- Save the processed data files to the `data/processed` directory

2. **Import Processed Data into PostgreSQL**:
```bash
python data/import_to_postgres.py
```
This script will:
- Create the necessary tables in the PostgreSQL database if they don't exist
- Import the resale prices data (~950,000 records)
- Import the HDB completion status data (~1,500 records)

The import process typically takes a few minutes to complete. You'll see progress indicators showing the chunks being imported.

## Running Without Docker
If you want to run the application without Docker:
1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Set up a local PostgreSQL instance and update the environment variables accordingly.

3. Follow the data import steps above.

4. Start the application:
```bash
uvicorn app.main:app --reload
```
