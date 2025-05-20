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
- the service uses Server-Sent Events (SSE) to stream responses back to the client
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
- `utils` - contains the utils (e.g. logging, database connections)
- `logs` - contains the application log files
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

# Logging Configuration
LOG_LEVEL=info  # Options: debug, info, warning, error, critical
```

## Running with Docker (Recommended)
The recommended way to run this application is using Docker, which provides a consistent environment with all dependencies pre-configured.

1. Start the Docker daemon (if not already running):
```bash
# On macOS
open -a Docker

# On Windows
# Start Docker Desktop manually

# On Linux
sudo systemctl start docker
```

2. Build and start all containers:
```bash
# Build and start all services in detached mode
docker compose up -d
```

3. Verify that containers are running:
```bash
docker ps
```

You should see both the PostgreSQL database container (`hdb_postgres`) and the API container (`hdb_api`) running. The API is accessible at http://localhost:8000.

## Troubleshooting Docker Setup
If you encounter issues with the Docker setup, here are some helpful commands:

1. **Check container logs**:
```bash
# View API container logs
docker logs hdb_api

# View PostgreSQL container logs  
docker logs hdb_postgres

# Follow logs in real-time
docker logs -f hdb_api
```

2. **Restart containers**:
```bash
# Restart a specific container
docker restart hdb_api

# Restart all containers
docker compose restart
```

3. **Rebuild containers after code changes**:
```bash
# Rebuild and restart API container
docker compose up -d --build api
```

4. **Access the container shell**:
```bash
# Access API container shell
docker exec -it hdb_api /bin/bash

# Access PostgreSQL container shell
docker exec -it hdb_postgres /bin/sh
```

5. **Common issues**:
   - Missing .env file or API keys: Ensure your .env file is properly set up with the required environment variables
   - Port conflicts: Make sure ports 8000 and 5432 are not already in use by other services
   - Model artifacts missing: Ensure the modeling/artifacts directory contains the trained model

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

## Running Without Docker (Alternative)
If you prefer to run the application without Docker, follow these steps:

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Set up a local PostgreSQL instance and update the environment variables accordingly.

3. Follow the data import steps above.

4. Start the application:
```bash
uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

Note that running without Docker requires additional setup and may introduce environment-specific issues. For most users, the Docker approach above is recommended.

# API Endpoints

When running with Docker, the API is accessible at http://localhost:8000 from your host machine. All examples below assume you're running the commands from your host, not from inside the containers.

## Streaming `/ask` Endpoint

The `/ask` endpoint is the primary endpoint for all chat-like interactions. It uses Server-Sent Events (SSE) to stream responses back to the client in real-time. This provides a more interactive experience, similar to modern chat applications.

Internally, it wraps the `query_database` and `predict_price` functions as tools, and uses Claude to decide which tool to use.

### Request
The system consists of three main components:

1. **PostgreSQL Database**: Runs on port 5432
2. **FastAPI Backend**: Runs on port 8000
3. **Next.js Frontend**: Runs on port 3000

With the full system running, you can access:
- Chat interface at http://localhost:3000
- Swagger API documentation at http://localhost:8000/docs

Assuming you have the docker container for the API running at port 8000:
```bash
curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "What is the average price per square meter for flats in Woodlands?"}' --no-buffer
data: {"type": "start"}

data: {"type": "assistant_message", "content": "I'll help you find the average price per square meter for flats in Woodlands. Let me query the database to get this information."}

data: {"type": "tool_call", "name": "query_database", "input": {"natural_query": "What is the average price per square meter for HDB flats in Woodlands?"}}

data: {"type": "tool_response", "name": "query_database", "response": {"data": [{"avg_price_per_sqm": 3017.486141870268}], "sql": "\n        SELECT \n            AVG(resale_price / floor_area_sqm) AS avg_price_per_sqm\n        FROM resale_prices\n        WHERE town = 'WOODLANDS'\n    ", "explanation": "This SQL query calculates the average price per square meter for HDB flats in the Woodlands town. It does this by selecting the average of the resale_price divided by the floor_area_sqm column from the resale_prices table, where the town is 'WOODLANDS'. This gives us the average price per square meter for flats in that town.\"\n"}}

data: {"type": "assistant_message", "content": "Based on the database query, the average price per square meter for HDB flats in Woodlands is approximately **$3,017.49 per square meter**.\n\nThis figure represents the average across all flat types and models in Woodlands, calculated by dividing each flat's resale price by its floor area in square meters, and then taking the average of these values."}

data: {"type": "end"}
```

> **Note**: The `--no-buffer` flag is crucial for proper streaming with curl. It ensures that responses are displayed immediately as they are received, rather than being buffered until completion.

### Response Format
The streaming response consists of a series of SSE events. Each event has a specific type:

1. **start** - Indicates the beginning of the response stream
2. **assistant_message** - Text generated by the assistant
3. **tool_call** - When the assistant uses a tool (query_database, predict_price)
4. **tool_response** - Results returned by the tool
5. **end** - Indicates the end of the response stream


## Other Endpoints

These other endpoints are more for testing individual functions, such as querying the database and predicting prices.

### `/predict`
Predicts HDB resale prices for a given set of property attributes.

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "town": "TAMPINES",
    "flat_type": "4 ROOM",
    "storey_range": "07 TO 09",
    "floor_area_sqm": 90.0,
    "flat_model": "Improved",
    "lease_commence_date": 1990,
    "remaining_lease": 65.5
  }' | jq
# response:
{
  "predicted_price": 449041.482220012,
  "property": {
    "town": "TAMPINES",
    "flat_type": "4 ROOM",
    "storey_range": "07 TO 09",
    "floor_area_sqm": 90.0,
    "flat_model": "Improved",
    "lease_commence_date": 1990,
    "remaining_lease_years": 65.5
  }
}
```

### `/query`
Allows natural language queries to the database.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top 5 most expensive HDB towns in the last 3 years?"}' | jq
# response:
{
  "data": [
    {
      "town": "BUKIT TIMAH",
      "avg_resale_price": 848882.4818604651
    },
    {
      "town": "BISHAN",
      "avg_resale_price": 795191.2953871774
    },
    {
      "town": "CENTRAL AREA",
      "avg_resale_price": 723743.8865866209
    },
    {
      "town": "BUKIT MERAH",
      "avg_resale_price": 704757.0424530169
    },
    {
      "town": "QUEENSTOWN",
      "avg_resale_price": 684816.0194741967
    }
  ],
  "sql": "\n        SELECT town, AVG(resale_price) AS avg_resale_price\n        FROM resale_prices\n        WHERE month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '3 years')\n        GROUP BY town\n        ORDER BY avg_resale_price DESC\n        LIMIT 5;\n    ",
  "explanation": "This query retrieves the top 5 most expensive HDB towns in the last 3 years based on the average resale price. It does this by:\n    1. Filtering the resale_prices table to only include records from the last 3 years using the month column and the DATE_TRUNC function.\n    2. Grouping the results by the town column and calculating the average resale_price for each town.\n    3. Ordering the results by the average resale price in descending order.\n    4. Limiting the output to the top 5 rows.\"\n"
}
```

# Frontend

## Overview
The system includes a modern, user-friendly chat interface built with Next.js and Tailwind CSS. This frontend provides an intuitive way to interact with the HDB price analysis system through natural language questions.

## Features
- **Interactive Chat Interface**: A clean, responsive design for asking questions and viewing answers
- **Real-time Streaming**: Responses stream in real-time using Server-Sent Events (SSE)
- **Markdown Support**: Rich text formatting for tables, lists, and other structured data
- **Debugging Tools**: Expandable sections showing tool calls and responses for transparency
- **Mobile-Friendly**: Responsive design that works on various screen sizes

## Architecture
The frontend is containerized alongside the backend services:
- **Next.js**: Provides the React framework and development server
- **Tailwind CSS**: Used for styling the components
- **React Markdown**: Renders formatted content from the API

## Accessing the Frontend
Once the system is running, the chat interface is available at:
```
http://localhost:3000
```

## Using the Chat Interface
1. **Ask a Question**: Type your question in the input field at the bottom of the screen
2. **View Response**: The assistant's answer will stream in real-time
3. **See Details**: Click "Show processing details" under any response to view the behind-the-scenes API calls
4. **Examples of Good Questions**:
   - "What is the average price per square meter for flats in Woodlands?"
   - "Which HDB towns have seen the highest price increases in the last 5 years?"
   - "Predict the price of a 4-room flat in Tampines with 90 square meters."
   - "What are the least expensive neighborhoods for 3-room flats?"

# End-to-End Testing

## Testing the Complete System
To test the entire system end-to-end:

1. **Start all services**:
```bash
docker compose up -d
```

2. **Verify the services**:
```bash
docker ps
```
You should see three containers running: `hdb_postgres`, `hdb_api`, and `hdb_frontend`.

3. **Access the web interface**:
   - Open a browser and navigate to http://localhost:3000
   - The chat interface should load, indicating a successful frontend deployment

4. **Test API connectivity**:
   - Type a question in the chat interface, e.g., "What's the average price of HDB flats in Woodlands?"
   - You should receive a streaming response with the assistant's answer
   - Expanding "Show processing details" should reveal the API calls made

5. **Verify database connectivity**:
   - Ask a question that requires database access, e.g., "Show me the top 5 most expensive towns"
   - The response should include data retrieved from the PostgreSQL database

## Example Test Flow

A comprehensive test might include:

1. **Simple database query**: "What is the average price of 4-room flats?"
2. **Complex analysis**: "Which towns have seen the highest price increase in the past 5 years?"
3. **Price prediction**: "Predict the price of a 5-room flat in Tampines built in 1990."
4. **Error handling**: Enter an ambiguous or nonsensical question to test error responses

## Troubleshooting End-to-End Issues

If the end-to-end test fails, check the following:

1. **Frontend logs**:
```bash
docker logs hdb_frontend
```

2. **API logs**:
```bash
docker logs hdb_api
```

3. **Network connectivity**: Ensure the API URL is correctly configured in the frontend

4. **CORS settings**: Verify that the API is allowing cross-origin requests from the frontend

# Logging System

The application implements a centralized logging system to support monitoring, debugging, and auditing. Key features include:

## Log Configuration

- **Default Level**: INFO (captures standard operational events)
- **Log Format**: `timestamp - module_name - log_level - message`
- **Environment Variable**: Set `LOG_LEVEL` to override the default level (options: debug, info, warning, error, critical)

## Log Locations

- **Console Output**: All logs are output to the console for immediate visibility
- **File Output**: Daily log files are created in the `logs` directory with date-based naming (`YYYY-MM-DD.log`)

## Using the Logger

The logger can be imported and used in any module as follows:

```python
from utils.logger import get_logger

# Initialize with the current module name
logger = get_logger(__name__)

# Usage examples
logger.debug("Detailed information for debugging")
logger.info("Standard operational information")
logger.warning("Warning about potential issues")
logger.error("Error information when something fails")
logger.critical("Critical error affecting application functionality")
```

## Log Categories

The system captures different types of events:

- **API Requests**: Endpoint access with request details
- **Database Operations**: SQL queries and database connections
- **Model Operations**: Model loading and prediction results
- **Configuration**: Environment variable loading and configuration details
- **Errors and Exceptions**: Captured with full stack traces for troubleshooting

## Viewing Logs

When running with Docker:
```bash
# View the most recent logs
docker logs hdb_api 

# View the last 50 log entries
docker logs --tail 50 hdb_api

# Get logs from a specific date
docker exec hdb_api cat /app/logs/YYYY-MM-DD.log
```

When running without Docker, logs are stored in the `logs` directory of the project.
