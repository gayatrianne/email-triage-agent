# Test Evidence — Galaxy Telecom AI Email Triage Agent

**Author:** Gayatri Anne  
**Date:** 24 July 2026  
**Status:** POC Testing Complete  

---

## 1. Test Approach

The POC was tested end to end using two realistic customer emails sent to the 
Galaxy Telecom helpdesk inbox. The full pipeline was triggered manually via the 
Logic App HTTP trigger and all components were verified individually before 
integration testing.

---

## 2. Test Emails

### Email 1 — Technical Support
- **Subject**: Mobile Internet Not Working Since Yesterday
- **Sender**: galaxy.telecom.helpdesk@outlook.com
- **Body**: Customer reports mobile data not working since yesterday afternoon 
  despite full 5G signal. Has already restarted phone and reset network settings. 
  Voice calls working normally. Customer ID: CUST-20481. Signed: David Williams.

### Email 2 — Billing Query
- **Subject**: Charged Twice for My Monthly Bill
- **Sender**: galaxy.telecom.helpdesk@outlook.com
- **Body**: Customer reports being charged twice for the same monthly subscription 
  on 18 July and the following day. Raised issue three days ago with no response. 
  Requests investigation and refund. Customer ID: CUST-10245. Signed: Sarah Johnson.

---

## 3. Component Test Results

### 3.1 Function App — analyse_email (Unit Test)

Tested directly via Azure Portal Test/Run with sample payload:

**Input:**
```json
{
    "subject": "My broadband has been down for 2 days",
    "body": "Hi, my internet has not been working for 2 days. I work from home and this is really affecting my job. Please can someone help urgently.",
    "sender": "david.williams@email.com"
}
```

**Output:**
```json
{
    "intent": "technical_support",
    "sentiment": "urgent",
    "routing_team": "Technical",
    "priority": "high",
    "summary": "Customer reports their broadband has been down for two days, impacting their ability to work from home and requesting urgent assistance."
}
```

**Result**: ✅ Pass — correct intent, sentiment, routing and priority

---

### 3.2 End to End Pipeline Test

**Trigger**: Logic App HTTP trigger (manual run)  
**Date**: 24 July 2026  
**Emails processed**: 2  

| Step | Status | Duration |
|---|---|---|
| When HTTP request received | ✅ Pass | 0s |
| Get secret (Key Vault) | ✅ Pass | 0.2s |
| HTTP — Get OAuth token | ✅ Pass | 0.5s |
| HTTP 1 — Read emails | ✅ Pass | 0.3s |
| Parse JSON | ✅ Pass | 0s |
| Initialize CSV | ✅ Pass | 0s |
| Initialize count | ✅ Pass | 0s |
| For each (2 emails) | ✅ Pass | 7s |
| Create blob | ✅ Pass | 0.1s |
| Create SAS URI | ✅ Pass | 0s |
| Send email with attachment | ✅ Pass | 0.7s |

---

### 3.3 AI Analysis Results

| Subject | Intent | Sentiment | Team | Priority | Result |
|---|---|---|---|---|---|
| Mobile Internet Not Working Since Yesterday | technical_support | urgent | Technical | high | ✅ Correct |
| Charged Twice for My Monthly Bill | billing_query | urgent | Billing | high | ✅ Correct |

---

### 3.4 CSV Output Verification

CSV file `2026-07-24-triage-report.csv` saved to Blob Storage container 
`email-triage-output` with correct data for both emails.

**Result**: ✅ Pass

---

### 3.5 Email Delivery Verification

Email received at `galaxy.telecom.L3@outlook.com` with:
- Subject: Galaxy Telecom — Daily Email Triage Report — 24 Jul 2026
- Body: Total emails processed: 2
- Attachment: triage-report-24-Jul-2026.csv (1KB)

**Result**: ✅ Pass

---

## 4. Issues Encountered and Resolved

| Issue | Root Cause | Resolution |
|---|---|---|
| Function App 403 error from Logic App | Wrong URL — Flex Consumption uses unique subdomain | Updated to correct URL with unique suffix |
| gpt-5-mini API version error | gpt-5-mini uses Responses API not Chat Completions | Switched to `/openai/v1/responses` endpoint |
| Logic App For each expression error | Response body was a string not an array | Added Parse JSON step before For each |
| SAS URI generation failed with Managed Identity | Managed Identity cannot generate SAS tokens | Created separate Access Key connection for SAS step |
| Refresh token not saved to Key Vault via script | DefaultAzureCredential could not find local credentials | Stored token manually via Azure Portal |

---

## 5. Test Evidence Screenshots

Screenshots captured on 24 July 2026:

1. Logic App run — all steps green
2. L3 team inbox — email received with CSV attachment
3. CSV open in Excel — two rows of correctly analysed email data
4. Blob Storage — CSV files in email-triage-output container
5. Function App — both analyse_email and send_report enabled