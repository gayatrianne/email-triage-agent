# Architecture Document — Galaxy Telecom AI Email Triage Agent

**Author:** Gayatri Anne  
**Date:** 24 July 2026  
**Version:** 1.0 — POC  

---

## 1. Overview

This document describes the technical architecture of the Galaxy Telecom AI 
Email Triage Agent POC. The solution is built entirely on Microsoft Azure and 
uses a microservices pattern with clear separation of concerns between 
orchestration, AI analysis, and report delivery.

---

## 2. Architecture Principles

| Principle | Application |
|---|---|
| Separation of concerns | Logic App orchestrates; Function Apps do the work |
| Single responsibility | Each function does one thing only |
| Pay per use | Flex Consumption and Logic App Consumption plans |
| Secure by default | Managed Identity, Key Vault, no hardcoded secrets |
| Reusability | send_report function is generic — reusable by any future pipeline |

---

## 3. Component Design

### 3.1 Azure Logic App (Orchestrator)
- **Plan**: Consumption (Stateful)
- **Trigger**: HTTP request (manual for POC; Recurrence for production)
- **Responsibility**: Orchestrates the full pipeline — reads emails, 
  calls functions, builds CSV, saves to blob, generates SAS URL
- **Why Logic App**: No-code orchestration with built-in connectors for 
  Key Vault, Blob Storage and Graph API

### 3.2 Azure Function App — analyse_email
- **Runtime**: Python 3.11, Flex Consumption
- **Trigger**: HTTP POST
- **Input**: `{ subject, body, sender }`
- **Output**: `{ intent, sentiment, routing_team, priority, summary }`
- **Responsibility**: Single email AI analysis only
- **Why separate function**: Testable in isolation; reusable by other pipelines

### 3.3 Azure Function App — send_report
- **Runtime**: Python 3.11, Flex Consumption (same app as analyse_email)
- **Trigger**: HTTP POST
- **Input**: `{ to_email, csv_blob_url, email_count, report_date, access_token }`
- **Output**: `{ status, message, emails_processed }`
- **Responsibility**: Downloads CSV via SAS URL and sends as email attachment
- **Why separate function**: Generic, reusable by any future reporting pipeline

### 3.4 Azure AI Foundry — gpt-5-mini
- **Deployment type**: Global Standard
- **API**: Responses API (`/openai/v1/responses`)
- **Why gpt-5-mini**: Cost-effective, GA, strong reasoning for structured 
  output extraction; 400k context window handles large email bodies

### 3.5 Azure Blob Storage
- **Container**: email-triage-output
- **Naming**: `yyyy-MM-dd-triage-report.csv`
- **Lifecycle policy**:
  - Day 0-7: Hot tier
  - Day 7-21: Cool tier
  - Day 21+: Deleted automatically

### 3.6 Azure Key Vault
- **Secret**: graph-refresh-token
- **Access**: Logic App via System-assigned Managed Identity
- **Why Key Vault**: Secrets never appear in code or Logic App definitions

### 3.7 Microsoft Graph API
- **Permissions**: Mail.Read, Mail.Send (Delegated)
- **Auth flow**: OAuth 2.0 refresh token flow
- **Sender**: galaxy.telecom.helpdesk@outlook.com
- **Recipient**: galaxy.telecom.L3@outlook.com

---

## 4. Security Design

| Concern | Solution |
|---|---|
| OAuth token storage | Azure Key Vault |
| Key Vault access | Managed Identity (no credentials in code) |
| Function App access | Function key authentication |
| Blob Storage access | Managed Identity for read/write; Access Key for SAS generation |
| AI API key | Azure Function App environment variable |
| CI/CD credentials | Azure service principal stored as GitHub secret |

---

## 5. Data Flow

Logic App triggers (HTTP or schedule)
Logic App reads OAuth refresh token from Key Vault
Logic App exchanges refresh token for access token via Microsoft identity platform
Logic App reads unread emails from helpdesk inbox via Graph API
Logic App parses email list (JSON array)
For each email:
a. Logic App calls analyse_email Function App (HTTP POST)
b. analyse_email calls gpt-5-mini via Azure AI Foundry Responses API
c. gpt-5-mini returns structured JSON analysis
d. Logic App appends CSV row to string variable
e. Logic App increments email counter
Logic App saves CSV to Blob Storage (one file per run)
Logic App generates SAS URL for the CSV blob (24 hour expiry)
Logic App calls send_report Function App with SAS URL and access token
send_report downloads CSV via SAS URL
send_report encodes CSV as base64 and sends via Graph API sendMail
L3 team receives email with CSV attachment
---

## 6. CI/CD Pipeline
Developer pushes to main branch
↓
GitHub Actions workflow triggers
↓
Python 3.11 environment setup
↓
Dependencies installed (requirements.txt)
↓
Azure CLI login (service principal)
↓
src/ folder zipped and deployed to
func-email-triage-dev via Azure CLI

---

## 7. Known Limitations and Future Improvements

| Limitation | Future Improvement |
|---|---|
| OAuth token expires — manual renewal needed | Automate token refresh via scheduled Azure Function |
| No email deduplication | Track processed message IDs in Azure Table Storage |
| SAS generation uses Access Key | Build a dedicated SAS generation function using connection string from Key Vault |
| CSV only — no database | Write triage results to Azure SQL or Cosmos DB |
| No monitoring dashboard | Add Power BI report on top of Blob Storage data |
| Manual trigger for POC | Switch to Recurrence trigger for production (daily at 8am) |