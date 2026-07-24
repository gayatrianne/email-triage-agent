# Deployment Guide — Galaxy Telecom AI Email Triage Agent

**Author:** Gayatri Anne  
**Date:** 24 July 2026  

This guide walks through rebuilding the entire environment from scratch using
the Bicep templates in the `infra/` folder.

---

## Prerequisites

Before starting, ensure you have:

- An active Azure subscription
- A GitHub account
- Two Outlook personal accounts created:
  - `<your-helpdesk>@outlook.com` — customer helpdesk inbox
  - `<your-l3-team>@outlook.com` — L3 team inbox
- Azure CLI installed locally (`az --version` to verify)
- Python 3.11+ installed locally
- Git installed locally

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/gayatrianne/email-triage-agent.git
cd email-triage-agent
```

---

## Step 2 — Create Azure Resource Group

```bash
az login
az group create \
  --name rg-email-triage-dev \
  --location uksouth \
  --tags Project=customer-service-ai Environment=dev
```

---

## Step 3 — Deploy Azure AI Foundry

Azure AI Foundry is not yet fully supported in Bicep for all resource types.
Create it manually via the portal:

1. Go to [ai.azure.com](https://ai.azure.com)
2. Create a new **Hub** in `rg-email-triage-dev`, UK South
3. Create a **Project** inside the hub
4. Deploy **gpt-5-mini** (Generally Available version) with Default settings
5. From the project **Details** tab, copy:
   - **Azure OpenAI endpoint** — save for Step 4
   - **API key** — save for Step 4

---

## Step 4 — Update Parameters File

Open `infra/parameters/dev.parameters.json` and replace:

```json
"azureOpenAIEndpoint": {
  "value": "REPLACE_WITH_YOUR_AZURE_AI_FOUNDRY_ENDPOINT"
},
"azureOpenAIApiKey": {
  "value": "REPLACE_WITH_YOUR_AZURE_AI_FOUNDRY_API_KEY"
}
```

With your actual values from Step 3.

> ⚠️ Never commit real API keys to GitHub. Use this file locally only.

---

## Step 5 — Deploy Infrastructure via Bicep

```bash
az deployment group create \
  --resource-group rg-email-triage-dev \
  --template-file infra/main.bicep \
  --parameters @infra/parameters/dev.parameters.json
```

This deploys:
- Storage Account with `email-triage-output` container and lifecycle policy
- Function App (Flex Consumption, Python 3.11) with Managed Identity
- Logic App (Consumption, Stateful) with Managed Identity
- Key Vault with RBAC roles for both Managed Identities

---

## Step 6 — Set Up GitHub Repository Secrets

Create a service principal for CI/CD:

```bash
az ad sp create-for-rbac \
  --name "sp-email-triage-dev" \
  --role contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID>/resourceGroups/rg-email-triage-dev \
  --sdk-auth
```

Copy the JSON output. Then in GitHub:

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Add secret: `AZURE_CREDENTIALS` — paste the JSON output

---

## Step 7 — Deploy Function App Code via CI/CD

Push any change to the `main` branch to trigger the GitHub Actions pipeline:

```bash
git commit --allow-empty -m "ci: trigger initial deployment"
git push origin main
```

Check **Actions** tab in GitHub — wait for the green tick.

---

## Step 8 — Register Microsoft Graph API App

1. Go to **Microsoft Entra ID** → **App registrations** → **+ New registration**
2. Fill in:
   - **Name**: `app-email-triage-graph`
   - **Supported account types**: Accounts in any organisational directory and personal Microsoft accounts
   - **Redirect URI**: Mobile and desktop → `https://login.microsoftonline.com/common/oauth2/nativeclient`
3. Click **Register**
4. Go to **API permissions** → **+ Add a permission** → **Microsoft Graph** → **Delegated**
5. Add: `Mail.Read` and `Mail.Send`
6. Click **Grant admin consent**
7. Go to **Authentication** → **Advanced settings** → set **Allow public client flows** to **Yes**
8. Note down the **Application (client) ID**

---

## Step 9 — Generate OAuth Refresh Token

Install dependencies:

```bash
pip install msal azure-identity azure-keyvault-secrets
```

Open `src/generate_refresh_token.py` and update:

```python
CLIENT_ID = "YOUR_APPLICATION_CLIENT_ID"   # From Step 8
```

Run the script:

```bash
python src/generate_refresh_token.py
```

Follow the device login instructions. Copy the refresh token printed to the console.

---

## Step 10 — Store Refresh Token in Key Vault

1. Go to `kv-email-triage-dev` in Azure Portal
2. Click **Secrets** → **+ Generate/Import**
3. Fill in:
   - **Name**: `graph-refresh-token`
   - **Value**: paste the refresh token from Step 9
4. Click **Create**

---

## Step 11 — Get Function App Host Key

1. Go to `func-email-triage-dev` → **Functions** → `analyse_email`
2. Click **Get Function URL** → copy the **default (Host key)** URL
3. Note the full URL including the `?code=` parameter — needed for Step 12

---

## Step 12 — Import Logic App Workflow

The Logic App is deployed empty by Bicep. Import the workflow:

1. Go to `logic-email-triage-dev` → **Logic app designer** → **Code view**
2. Replace the content with the JSON from `docs/backup/logic-app-workflow.json`
3. Update these values in the JSON:
   - `client_id` — your Application (client) ID from Step 8
   - Function App URL in `HTTP_2` and `Send_email_with_attachment` — use the URL from Step 11
   - Helpdesk email address — your helpdesk Outlook account
   - L3 team email address — your L3 Outlook account
4. Click **Save**

---

## Step 13 — Set Up Blob Storage Connection for SAS URI

The `Create SAS URI by path` action requires an Access Key connection:

1. Go to storage account → **Access keys** → copy **key1**
2. In Logic App designer, click on **Create SAS URI by path (V2)**
3. Click **Change connection** → **Add new**
4. Select **Access Key** authentication
5. Enter storage account name and key1
6. Click **Create**

---

## Step 14 — Test End to End

1. Send a test email to your helpdesk Outlook account
2. Go to the Logic App → **Run** → **Run trigger**
3. Check **Overview** → **Runs history** for a successful run
4. Verify the L3 team inbox received the email with CSV attachment
5. Verify the CSV file appears in Blob Storage `email-triage-output` container

---

## Step 15 — Switch to Scheduled Trigger (Optional)

To run daily automatically, update the Logic App trigger in code view from:

```json
"When_an_HTTP_request_is_received": {
  "type": "Request",
  "kind": "Http"
}
```

To:

```json
"Recurrence": {
  "type": "Recurrence",
  "recurrence": {
    "frequency": "Day",
    "interval": 1,
    "schedule": {
      "hours": ["8"],
      "minutes": [0]
    },
    "timeZone": "GMT Standard Time"
  }
}
```

---

## Environment Variables Reference

| Variable | Where to get it | Set in |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure AI Foundry → Project → Details | Function App env vars |
| `AZURE_OPENAI_API_KEY` | Azure AI Foundry → Project → Details | Function App env vars |
| `AzureWebJobsFeatureFlags` | Fixed value: `EnableWorkerIndexing` | Function App env vars |
| `AZURE_CREDENTIALS` | Service principal JSON (Step 6) | GitHub secret |
| `graph-refresh-token` | Generated in Step 9 | Key Vault secret |

---

## Resource Naming Convention

| Resource | Name |
|---|---|
| Resource Group | `rg-email-triage-dev` |
| Storage Account | `stemailtiagedev` |
| Key Vault | `kv-email-triage-dev` |
| Function App | `func-email-triage-dev` |
| Logic App | `logic-email-triage-dev` |
| Graph API App | `app-email-triage-graph` |

---

## Estimated Monthly Cost (Dev)

| Resource | Estimated Cost |
|---|---|
| Function App (Flex Consumption) | < $1 |
| Logic App (Consumption) | < $1 |
| Blob Storage | < $1 |
| Key Vault | < $1 |
| Azure AI Foundry (gpt-5-mini) | ~$1-2 depending on volume |
| **Total** | **< $5/month** |