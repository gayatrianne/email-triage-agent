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
import urllib.request           # For making HTTP requests to Azure AI Foundry
import urllib.error             # For handling HTTP errors

# Initialise the Function App using Python v2 programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

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

        # Get Azure AI Foundry credentials from environment variables
        api_key = os.environ["AZURE_OPENAI_API_KEY"]
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]

        # Build the request payload for the Responses API
        payload = {
            "model": "gpt-5-mini",
            "input": prompt
        }

        # Make HTTP POST request to Azure AI Foundry Responses API
        request_data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            endpoint,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "api-key": api_key
            },
            method="POST"
        )

        # Execute the request and parse the response
        with urllib.request.urlopen(request) as response:
            response_data = json.loads(response.read().decode("utf-8"))

        # Extract text from Responses API
        # output[0] is reasoning block, output[1] is the message block
        result_text = None
        for output_item in response_data.get("output", []):
            if output_item.get("type") == "message":
                for content_item in output_item.get("content", []):
                    if content_item.get("type") == "output_text":
                        result_text = content_item["text"].strip()
                        break

        if not result_text:
            return func.HttpResponse(
                json.dumps({"error": "No text output found in API response"}),
                status_code=500,
                mimetype="application/json"
            )

        # Clean up markdown code blocks if model wraps response in them
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

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
        logging.error(f"JSON parse error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Model returned invalid JSON", "detail": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logging.error(f"HTTP error calling AI Foundry: {e.code} - {error_body}")
        return func.HttpResponse(
            json.dumps({"error": f"Error code: {e.code}", "detail": error_body}),
            status_code=500,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error", "detail": str(e)}),
            status_code=500,
            mimetype="application/json"
        )