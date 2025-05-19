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
