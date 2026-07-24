"""
Module:
    function_app.py
Description:
    Azure Function App with two HTTP triggers:
    1. analyse_email — receives a single customer email, calls Azure AI Foundry
       (gpt-5-mini) to analyse it, and returns a structured JSON response
       containing intent, sentiment, routing team, priority and summary.
    2. send_report — receives a CSV blob URL and access token, downloads the
       CSV from Azure Blob Storage and sends it as an email attachment to the
       L3 team via Microsoft Graph API.
    Both functions are called by the Logic App orchestrator as part of the
    Galaxy Telecom AI Email Triage pipeline.
Author:
    Gayatri Anne
Created:
    23-Jul-2026
"""

import azure.functions as func  # Azure Functions SDK
import logging                  # For Application Insights logging
import json                     # For parsing and returning JSON
import os                       # For reading environment variables
import urllib.request           # For making HTTP requests
import urllib.error             # For handling HTTP errors
import base64                   # For encoding CSV as base64 email attachment

# Initialise the Function App using Python v2 programming model
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ── Function 1: analyse_email ──────────────────────────────────────────────────

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


# ── Function 2: send_report ────────────────────────────────────────────────────

@app.route(route="send_report", methods=["POST"])
def send_report(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function that downloads a CSV from Blob Storage and sends
    it as an email attachment to the L3 team via Microsoft Graph API.

    Expected request body:
        {
            "to_email": "galaxy.telecom.L3@outlook.com",
            "csv_blob_url": "https://storage.blob.core.windows.net/...",
            "email_count": 2,
            "report_date": "23 Jul 2026",
            "access_token": "Bearer token string"
        }

    Returns:
        JSON with status and emails_processed count
    """
    logging.info("send_report function triggered")

    try:
        # Parse the incoming JSON request body
        req_body = req.get_json()
        to_email = req_body.get("to_email", "")
        csv_blob_url = req_body.get("csv_blob_url", "")
        email_count = req_body.get("email_count", 0)
        report_date = req_body.get("report_date", "")
        access_token = req_body.get("access_token", "")

        # Validate required fields
        if not to_email or not csv_blob_url or not access_token:
            return func.HttpResponse(
                json.dumps({"error": "Missing required fields: to_email, csv_blob_url, access_token"}),
                status_code=400,
                mimetype="application/json"
            )

        # Download the CSV file from Blob Storage using the blob URL
        logging.info(f"Downloading CSV from: {csv_blob_url}")
        with urllib.request.urlopen(csv_blob_url) as response:
            csv_content = response.read()

        # Encode the CSV content as base64 for the email attachment
        csv_base64 = base64.b64encode(csv_content).decode("utf-8")

        # Build the attachment filename from the report date
        attachment_name = f"triage-report-{report_date.replace(' ', '-')}.csv"

        # Build the Graph API sendMail request payload
        # Note: @odata.type is a required Graph API field for typed attachments
        email_payload = {
            "message": {
                "subject": f"Galaxy Telecom — Daily Email Triage Report — {report_date}",
                "body": {
                    "contentType": "Text",
                    "content": f"Please find attached the daily email triage report for {report_date}.\n\nTotal emails processed: {email_count}\n\nAll customer emails have been analysed and routed accordingly.\n\nThis is an automated report generated by the Galaxy Telecom AI Email Triage Agent."
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_email
                        }
                    }
                ],
                "attachments": [
                    {
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": attachment_name,
                        "contentType": "text/csv",
                        "contentBytes": csv_base64
                    }
                ]
            }
        }

        # Send email via Microsoft Graph API using the helpdesk account as sender
        sender_email = "galaxy.telecom.helpdesk@outlook.com"
        graph_url = f"https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail"

        request_data = json.dumps(email_payload).encode("utf-8")
        graph_request = urllib.request.Request(
            graph_url,
            data=request_data,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        # Execute the Graph API request — successful sendMail returns 202
        with urllib.request.urlopen(graph_request) as response:
            status_code = response.status

        logging.info(f"Email sent successfully to {to_email}, status: {status_code}")

        # Return success response
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "message": f"Report sent to {to_email}",
                "emails_processed": email_count
            }),
            status_code=200,
            mimetype="application/json"
        )

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        logging.error(f"HTTP error: {e.code} - {error_body}")
        return func.HttpResponse(
            json.dumps({"error": f"HTTP error: {e.code}", "detail": error_body}),
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