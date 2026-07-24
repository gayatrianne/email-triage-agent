# Environment Variables Reference

These are the environment variables required by the Function App.
Do NOT store actual values here — retrieve them from Azure AI Foundry and Key Vault.

| Variable | Description |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | Azure AI Foundry project endpoint ending in `/openai/v1/responses` |
| `AZURE_OPENAI_API_KEY` | Azure AI Foundry API key |
| `AzureWebJobsFeatureFlags` | Set to `EnableWorkerIndexing` — required for Python v2 model |