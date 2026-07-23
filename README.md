# Email Triage Agent 📧

AI-powered customer email triage agent built on Microsoft Azure for Galaxy Telecom — a fictional UK telecom company.

## Overview

This proof of concept (POC) demonstrates an intelligent email triage system that automatically reads customer emails, analyses them using a large language model, and routes them to the correct support team.

## Architecture
Customer Email (Outlook)
↓
Microsoft Graph API (Mail.Read)
↓
Azure Logic App (Orchestrator)
↓
Azure Function App (AI Analysis)
↓
Azure AI Foundry — gpt-5-mini
↓
Blob Storage (CSV output)
↓
L3 Team Email (Mail.Send)

## Azure Components

| Component | Resource | Purpose |
|---|---|---|
| Azure AI Foundry | proj-email-triage-dev | Hosts gpt-5-mini model |
| Azure Function App | func-email-triage-dev | AI analysis via HTTP trigger |
| Azure Logic App | logic-email-triage-dev | Orchestration |
| Azure Blob Storage | email-triage-output | CSV storage with lifecycle |
| Azure Key Vault | kv-email-triage-dev | OAuth token storage |

## Email Analysis Output

Each email is analysed for:
- **Intent** — billing_query, technical_support, account_management, complaint, general_enquiry
- **Sentiment** — positive, neutral, negative, urgent
- **Routing Team** — Billing, Technical, Account, Complaints, General
- **Priority** — high, medium, low
- **Summary** — one sentence description

## Tech Stack

- Python 3.11
- Azure Functions v2 programming model
- Azure AI Foundry (gpt-5-mini)
- Azure Logic Apps
- Microsoft Graph API
- Azure Key Vault + Managed Identity

## Status

🚧 POC — In Development

## Author

Gayatri Anne
