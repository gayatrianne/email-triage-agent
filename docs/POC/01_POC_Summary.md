# POC Summary — Galaxy Telecom AI Email Triage Agent

**Author:** Gayatri Anne  
**Date:** 24 July 2026  
**Status:** POC Complete  

---

## 1. Business Hypothesis

Customer service teams at Galaxy Telecom spend significant time manually reading, 
categorising and routing incoming customer emails. The hypothesis was:

> *"Can an AI agent automatically read customer emails, determine intent and sentiment, 
> and route them to the correct support team — reducing manual triage effort?"*

---

## 2. What We Built

An end to end AI-powered email triage pipeline on Microsoft Azure that:

- Reads unread customer emails from the Galaxy Telecom helpdesk inbox
- Analyses each email using Azure AI Foundry (gpt-5-mini) to extract intent, 
  sentiment, routing team, priority and a one-sentence summary
- Compiles all results into a single CSV report
- Saves the CSV to Azure Blob Storage with automated lifecycle management
- Emails the CSV report as an attachment to the L3 support team daily

---

## 3. Architecture

```
Customer Email
(galaxy.telecom.helpdesk@outlook.com)
↓
Microsoft Graph API (Mail.Read)
↓
Azure Logic App (Orchestrator)
├── Azure Key Vault (OAuth token)
├── analyse_email Function App → Azure AI Foundry (gpt-5-mini)
├── Azure Blob Storage (CSV output)
└── send_report Function App → Microsoft Graph API (Mail.Send)
↓
L3 Team Email with CSV Attachment
(galaxy.telecom.L3@outlook.com)
```

### Azure Components

| Component | Resource | Purpose |
|---|---|---|
| Azure AI Foundry | proj-email-triage-dev | Hosts gpt-5-mini model |
| Azure Function App | func-email-triage-dev | analyse_email + send_report |
| Azure Logic App | logic-email-triage-dev | Orchestration |
| Azure Blob Storage | email-triage-output | CSV storage with lifecycle |
| Azure Key Vault | kv-email-triage-dev | OAuth refresh token |
| Microsoft Graph API | App registration | Mail.Read + Mail.Send |

---

## 4. AI Analysis Output

Each email is analysed for:

| Field | Values |
|---|---|
| Intent | billing_query, technical_support, account_management, complaint, general_enquiry |
| Sentiment | positive, neutral, negative, urgent |
| Routing Team | Billing, Technical, Account, Complaints, General |
| Priority | high, medium, low |
| Summary | One sentence description of the email |

---

## 5. Test Results

Two realistic customer emails were processed:

| Subject | Intent | Sentiment | Team | Priority |
|---|---|---|---|---|
| Mobile Internet Not Working Since Yesterday | technical_support | urgent | Technical | high |
| Charged Twice for My Monthly Bill | billing_query | urgent | Billing | high |

Both emails were correctly classified and routed. The CSV report was emailed 
to the L3 team with the attachment successfully received.

---

## 6. Key Lessons Learned

- **Test components individually before integration** — the Function App should 
  have been tested before building the Logic App workflow
- **Flex Consumption cold start** — the Function App takes time to warm up on 
  first call; retry policies are essential
- **Flex Consumption URL** — uses a unique subdomain 
  (`func-name-uniqueid.region.azurewebsites.net`) not the standard 
  `azurewebsites.net` URL
- **Managed Identity limitations** — cannot generate SAS tokens; Access Key 
  connection required for SAS URI generation
- **gpt-5-mini Responses API** — uses a different response structure than the 
  Chat Completions API; output is nested under `output[n].content[n].text`
- **Logic App expressions** — do not support arrow functions or complex 
  transformations; string variables are more reliable than array mapping

---

## 7. Known Limitations

- OAuth refresh token stored in Key Vault will expire and need manual renewal
- SAS URI generation uses Access Key connection (less secure than Managed Identity)
- No deduplication — if the same email is unread on two consecutive runs it 
  will be processed twice
- Email body is plain text only — HTML emails may contain noise

---

## 8. Recommended Next Steps

- Add email deduplication by tracking processed message IDs in a database
- Automate refresh token renewal using a scheduled Azure Function
- Replace Access Key with a custom Function that generates SAS tokens securely
- Add a Power BI dashboard on top of the CSV data in Blob Storage
- Extend to write triage results into a CRM system in real time

---

## 9. Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Orchestration | Logic App | Separation of concerns; no code orchestration |
| AI Model | gpt-5-mini | Cost-effective, GA, strong reasoning capability |
| Auth | OAuth + Key Vault | Secure token storage with Managed Identity |
| Storage | Blob + lifecycle | Auto-archival after 7 days, deletion after 21 days |
| Deployment | Flex Consumption | Pay per execution, no idle cost |
| CI/CD | GitHub Actions + Azure CLI | Automated deployment on every push to main |
