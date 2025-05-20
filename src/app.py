"""
Main FastAPI application for HDB price prediction service.
"""
import asyncio
import json
from decimal import Decimal
from typing import Optional

import pandas as pd
from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils.config import get_claude_api_key
from utils.logger import get_logger
from utils.db import get_session
from src.predict import predict_property_price
from src.query import query_database

# Initialize logger
logger = get_logger(__name__)

# Custom JSON encoder to handle Decimal objects
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Check for Claude API key at startup
CLAUDE_API_KEY = get_claude_api_key()
if not CLAUDE_API_KEY:
    logger.error("CLAUDE_API_KEY environment variable not set. Please set it in the .env file or in the environment variables.")
    exit(1)

# Initialize Claude client (will raise error if API key not available)
def get_claude_client():
    if not CLAUDE_API_KEY:
        raise ValueError("Claude API key not configured")
    return Anthropic(api_key=CLAUDE_API_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="HDB Price Analysis API",
    description="API for analyzing and predicting HDB resale prices in Singapore",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class QuestionRequest(BaseModel):
    question: str

class PredictionRequest(BaseModel):
    town: str
    flat_type: str
    storey_range: str
    floor_area_sqm: float
    flat_model: str
    lease_commence_date: int
    remaining_lease: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.info("Health check endpoint called")
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint with basic information about the API."""
    logger.info("Root endpoint called")
    return {
        "message": "Welcome to the HDB Price Analysis API",
        "endpoints": {
            "/ask": "Ask a question about HDB prices and data (streaming response)",
            "/query": "Query the database with natural language",
            "/predict": "Predict HDB resale price for given property attributes"
        }
    }

async def stream_chat_response(request: QuestionRequest):
    """
    Generator function that streams the chat response as SSE events.
    """
    logger.info(f"Streaming response for question: {request.question}")
    
    try:
        client = get_claude_client()
    except ValueError as e:
        yield f"data: {json.dumps({'error': str(e)}, cls=DecimalEncoder)}\n\n"
        return
    
    # Initialize the conversation with the user's question
    messages = [
        {
            "role": "user",
            "content": f"Use the tools provided to answer the user's question. {request.question}"
        }
    ]
    
    # Define the tools available to the LLM
    tools = [
        {
            "name": "query_database",
            "description": """Query the database with SQL to get information about HDB properties and prices.
This function has access to:
- resale price data from 1990 to 2025
- BTO completion status data split by town/estate/year

You can use this function to answer questions about HDB properties and prices, such as:
- Which HDB estates have the lowest number of BTO units completed in the past decade?
- What is the median price of HDB flats in different flat types?
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "natural_query": {
                        "type": "string",
                        "description": "Natural language query about HDB data"
                    }
                },
                "required": ["natural_query"]
            }
        },
        {
            "name": "predict_price",
            "description": """Predict the resale price for a given HDB property.
This function uses a pre-trained gradient boosting model to predict the resale price for a given HDB property.
The model was trained on resale price data from 1990 to 2025, and is able to predict the resale price for a given HDB property.
Impute missing values for the function parameters (ie features) using reasonable defaults.
For example, if the storey_range is not provided, use the median storey range for the given flat_type.
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "town": {"type": "string"},
                    "flat_type": {"type": "string"},
                    "storey_range": {"type": "string"},
                    "floor_area_sqm": {"type": "number"},
                    "flat_model": {"type": "string"},
                    "lease_commence_date": {"type": "integer"},
                    "remaining_lease_years": {"type": "number"}
                },
                "required": ["town", "flat_type", "storey_range", "floor_area_sqm", 
                            "flat_model", "lease_commence_date", "remaining_lease_years"]
            }
        }
    ]
    
    # Maximum iterations to prevent infinite loops
    max_iterations = 10
    current_iteration = 0
    
    # Send initial event to indicate start of streaming
    yield f"data: {json.dumps({'type': 'start'}, cls=DecimalEncoder)}\n\n"
    
    # Process the conversation in a loop until the LLM completes or max iterations reached
    while current_iteration < max_iterations:
        current_iteration += 1
        
        # Send message to Claude
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4000,
            messages=messages,
            tools=tools,
            temperature=0.1,
        )
        
        logger.info(f"Response content length: {len(response.content)}")
        
        # Process all content blocks in the response
        has_tool_call = False
        for content_block in response.content:
            logger.info(f"Content block: {content_block}")
            # Stream text content
            if isinstance(content_block, TextBlock) and content_block.text:
                yield f"data: {json.dumps({'type': 'assistant_message', 'content': content_block.text}, cls=DecimalEncoder)}\n\n"
                await asyncio.sleep(0.01)  # Small delay to ensure chunks are sent properly
                messages.append({
                    "role": "assistant",
                    "content": content_block.text
                })
            
            # Process tool calls - check for type being 'tool_use'
            if isinstance(content_block, ToolUseBlock) and content_block.type == 'tool_use':
                has_tool_call = True
                tool_name = content_block.name
                tool_input = json.loads(content_block.input) if isinstance(content_block.input, str) else content_block.input
                
                # Send event for tool call
                yield f"data: {json.dumps({'type': 'tool_call', 'name': tool_name, 'input': tool_input}, cls=DecimalEncoder)}\n\n"
                
                # Process the tool call based on the tool name
                if tool_name == "query_database":
                    try:
                        db_session = get_session()
                        result, sql, explanation = query_database(
                            natural_query=tool_input["natural_query"],
                            session=db_session
                        )
                        # Convert dataframe to dict for JSON serialization
                        result_dict = result.to_dict(orient="records") if isinstance(result, pd.DataFrame) else []
                        
                        tool_response = {
                            "data": result_dict,
                            "sql": sql,
                            "explanation": explanation
                        }
                        
                    except Exception as e:
                        # TODO: Future work - implement retry mechanisms and more robust error recovery
                        error_message = f"Error executing database query: {str(e)}"
                        logger.error(error_message, exc_info=True)
                        tool_response = {
                            "error": error_message,
                            "success": False,
                            "details": "There was an issue executing your database query. Please check your question and try again."
                        }
                    
                elif tool_name == "predict_price":
                    try:
                        predicted_price = predict_property_price(**tool_input)
                        tool_response = {"predicted_price": predicted_price}
                    except Exception as e:
                        # TODO: Future work - implement better validation of inputs and fallback prediction methods
                        error_message = f"Error predicting property price: {str(e)}"
                        logger.error(error_message, exc_info=True)
                        tool_response = {
                            "error": error_message,
                            "success": False,
                            "details": "There was an issue predicting the property price. Please check the input parameters and try again."
                        }
                
                # Send event for tool response
                yield f"data: {json.dumps({'type': 'tool_response', 'name': tool_name, 'response': tool_response}, cls=DecimalEncoder)}\n\n"
                
                # Add the assistant's message with the tool call to the conversation
                last_text = ""
                for block in response.content:
                    if isinstance(block, TextBlock) and block.text:
                        last_text = block.text
                        break
                        
                messages.append({
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": last_text
                        },
                        {
                            "type": "tool_use",
                            "id": content_block.id if hasattr(content_block, 'id') else "unknown",
                            "name": tool_name,
                            "input": tool_input
                        }
                    ]
                })
                
                # Add the tool response to the conversation
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content_block.id if hasattr(content_block, 'id') else "unknown",
                            "content": json.dumps(tool_response, cls=DecimalEncoder)
                        }
                    ]
                })
        
        # Check for end_turn stop reason to break the loop
        if response.stop_reason == "end_turn" and not has_tool_call:
            yield f"data: {json.dumps({'type': 'end'}, cls=DecimalEncoder)}\n\n"
            break
        elif not has_tool_call:
            # If no tool call and not end_turn, we still have our final response
            yield f"data: {json.dumps({'type': 'end (no tool call)'}, cls=DecimalEncoder)}\n\n"
            break
    
    # If we reached max iterations without a final response, send end event
    if current_iteration >= max_iterations:
        yield f"data: {json.dumps({'type': 'end', 'message': 'Max iterations reached'}, cls=DecimalEncoder)}\n\n"

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Process a user question using Claude LLM and stream the response as SSE events.
    
    The LLM will work in a loop, using available tools until it generates a final response.
    Each step of the process is streamed back to the client as an event.
    """
    logger.info(f"Ask endpoint called with question: {request.question}")
    
    if not CLAUDE_API_KEY:
        raise HTTPException(status_code=500, detail="Claude API key not configured")
    
    return StreamingResponse(
        stream_chat_response(request),
        media_type="text/event-stream"
    )

@app.post("/query")
async def query_endpoint(request: QuestionRequest, db: Session = Depends(get_session)):
    """
    Translate a natural language question to SQL and query the database.
    Returns data, SQL query, and a natural language explanation.
    """
    logger.info(f"Query endpoint called with question: {request.question}")
    
    try:
        data, sql, explanation = query_database(request.question, db)
        logger.debug(f"Query executed: {sql}")
        
        # Convert DataFrame to list of dicts for JSON response
        if isinstance(data, pd.DataFrame):
            data_json = data.to_dict(orient="records")
            logger.info(f"Query returned {len(data_json)} results")
        else:
            data_json = []
            logger.info("Query returned no results")
            
        return {
            "data": data_json,
            "sql": sql,
            "explanation": explanation
        }
    except Exception as e:
        logger.error(f"Error in query endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict")
async def predict_endpoint(request: PredictionRequest):
    """
    Predict HDB resale price for a given set of property attributes.
    """
    logger.info(f"Predict endpoint called for {request.flat_type} in {request.town}")
    
    try:
        predicted_price = predict_property_price(
            town=request.town,
            flat_type=request.flat_type,
            storey_range=request.storey_range,
            floor_area_sqm=request.floor_area_sqm,
            flat_model=request.flat_model,
            lease_commence_date=request.lease_commence_date,
            remaining_lease_years=request.remaining_lease
        )
        
        logger.info(f"Predicted price: {predicted_price}")
        
        return {
            "predicted_price": predicted_price,
            "property": {
                "town": request.town,
                "flat_type": request.flat_type,
                "storey_range": request.storey_range,
                "floor_area_sqm": request.floor_area_sqm,
                "flat_model": request.flat_model,
                "lease_commence_date": request.lease_commence_date,
                "remaining_lease_years": request.remaining_lease
            }
        }
    except Exception as e:
        logger.error(f"Error in predict endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True) 