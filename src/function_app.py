"""
Module:
    function_app.py
Description:
    Azure Function App (HTTP trigger) that receives a single customer email
    via HTTP POST, calls Azure AI Foundry (gpt-5-mini) to analyse the email,
    and returns a structured JSON response containing intent, sentiment,
    routing team, and summary. This function is called by the Logic App
    orchestrator for each email retrieved from the Galaxy Telecom helpdesk
    inbox.
Author:
    Gayatri Anne
Created:
    23-Jul-2026
"""

import azure.functions as func  # Azure Functions SDK
import logging                  # For Application Insights logging
import json                     # For parsing and returning JSON
import os                       # For reading environment variables
from openai import AzureOpenAI  # Azure OpenAI client

# Initialise the Function App using Python v2 programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Initialise Azure OpenAI client using environment variables
# These are set in Function App configuration in Azure Portal
client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version="2025-01-01-preview",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
)

@app.route(route="analyse_email", methods=["POST"])
def analyse_email(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function that analyses a customer email using gpt-5-mini.
    
    Expected request body:
        {
            "subject": "Email subject line",
            "body": "Full email body text",
            "sender": "customer@example.com"
        }
    
    Returns:
        JSON with intent, sentiment, routing_team, priority, and summary
    """
    logging.info("analyse_email function triggered")

    try:
        # Parse the incoming JSON request body
        req_body = req.get_json()
        subject = req_body.get("subject", "")
        body = req_body.get("body", "")
        sender = req_body.get("sender", "")

        # Validate that required fields are present
        if not subject and not body:
            return func.HttpResponse(
                json.dumps({"error": "Request must include subject or body"}),
                status_code=400,
                mimetype="application/json"
            )

        # Build the prompt for gpt-5-mini
        # Instructs the model to return structured JSON only
        prompt = f"""
You are an AI assistant for Galaxy Telecom customer service.
Analyse the following customer email and return a JSON response only.

Email Subject: {subject}
Email Body: {body}
Sender: {sender}

Return ONLY a JSON object with these fields:
{{
    "intent": "one of: billing_query, technical_support, account_management, complaint, general_enquiry",
    "sentiment": "one of: positive, neutral, negative, urgent",
    "routing_team": "one of: Billing, Technical, Account, Complaints, General",
    "priority": "one of: high, medium, low",
    "summary": "one sentence summary of the email"
}}
"""

        # Call gpt-5-mini via Azure AI Foundry endpoint
        response = client.chat.completions.create(
            model="gpt-5-mini",         # Deployment name in Azure AI Foundry
            messages=[
                {"role": "system", "content": "You are a customer service triage assistant. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,             # Enough for the structured JSON response
            temperature=0.1             # Low temperature for consistent, predictable output
        )

        # Extract the text response from the model
        result_text = response.choices[0].message.content.strip()

        # Parse the model response as JSON to validate it
        result_json = json.loads(result_text)

        # Log the routing decision for monitoring in Application Insights
        logging.info(f"Email routed to: {result_json.get('routing_team')} | Priority: {result_json.get('priority')}")

        # Return the structured analysis as HTTP response
        return func.HttpResponse(
            json.dumps(result_json),
            status_code=200,
            mimetype="application/json"
        )

    except json.JSONDecodeError as e:
        # Model returned something that wasn't valid JSON
        logging.error(f"JSON parse error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Model returned invalid JSON", "detail": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as e:
        # Catch all other errors and return 500
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "detail": str(e)}),
            status_code=500,
            mimetype="application/json"
        )