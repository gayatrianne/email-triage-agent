# Email Triage Agent 📧

AI-powered customer email triage agent built on Microsoft Azure for Galaxy Telecom — a fictional UK telecom company.

## Overview

This proof of concept (POC) demonstrates an intelligent email triage pipeline that automatically reads unread customer emails, analyses them using a large language model, and delivers a structured triage report to the L3 support team as a CSV email attachment — with no human intervention required.

## Architecture

```
Customer Email (Outlook)
        ↓
Microsoft Graph API (Mail.Read)
        ↓
Azure Logic App (Orchestrator)
    ├── Azure Key Vault → OAuth refresh token
    ├── analyse_email Function App → Azure AI Foundry (gpt-5-mini)
    ├── Azure Blob Storage → CSV report with lifecycle management
    ├── Create SAS URI → secure time-limited download link
    └── send_report Function App → Microsoft Graph API (Mail.Send)
        ↓
L3 Team Email with CSV Attachment
```
## Azure Components

| Component | Resource | Purpose |
|---|---|---|
| Azure AI Foundry | proj-email-triage-dev | Hosts gpt-5-mini model |
| Azure Function App | func-email-triage-dev | analyse_email + send_report functions |
| Azure Logic App | logic-email-triage-dev | Orchestration |
| Azure Blob Storage | email-triage-output | CSV storage with lifecycle management |
| Azure Key Vault | kv-email-triage-dev | OAuth refresh token storage |
| Microsoft Graph API | app-email-triage-graph | Mail.Read + Mail.Send permissions |

## Function App

Two HTTP trigger functions deployed in the same Flex Consumption Function App:

- **analyse_email** — receives a single email (subject, body, sender), calls gpt-5-mini via Azure AI Foundry Responses API, returns structured JSON
- **send_report** — receives a SAS URL and access token, downloads the CSV from Blob Storage and sends it as an email attachment via Graph API

## Email Analysis Output

Each email is analysed for:
- **Intent** — billing_query, technical_support, account_management, complaint, general_enquiry
- **Sentiment** — positive, neutral, negative, urgent
- **Routing Team** — Billing, Technical, Account, Complaints, General
- **Priority** — high, medium, low
- **Summary** — one sentence description

## Tech Stack

- Python 3.11
- Azure Functions v2 programming model (Flex Consumption)
- Azure AI Foundry (gpt-5-mini — Responses API)
- Azure Logic Apps (Consumption, Stateful)
- Microsoft Graph API (OAuth 2.0 refresh token flow)
- Azure Key Vault + Managed Identity
- Azure Blob Storage with lifecycle policy
- GitHub Actions CI/CD (Azure CLI deployment)

## Repository Structure

```
email-triage-agent/
├── src/
│   ├── function_app.py            ← analyse_email + send_report functions
│   ├── generate_refresh_token.py  ← one-time OAuth token generation
│   ├── host.json                  ← Function App configuration
│   └── requirements.txt           ← Python dependencies
├── docs/
│   └── POC/
│       ├── 01_POC_Summary.md      ← hypothesis, results, lessons learned
│       ├── 02_Architecture.md     ← component design and data flow
│       └── 03_Test_Evidence.md    ← test results and screenshots
├── sample-data/
│   └── sample_emails.json         ← sample test emails
└── .github/
    └── workflows/
        └── deploy.yml             ← CI/CD pipeline
```
## Key Lessons Learned

- Test Function App directly before building Logic App workflow
- Flex Consumption uses a unique subdomain URL (not the standard azurewebsites.net)
- gpt-5-mini uses the Responses API — different response structure from Chat Completions
- Managed Identity cannot generate SAS tokens — Access Key connection required
- Logic Apps string variables are more reliable than array mapping for CSV building

## Status

✅ POC Complete — 24 July 2026

## Author

Gayatri Anne
[github.com/gayatrianne](https://github.com/gayatrianne)
