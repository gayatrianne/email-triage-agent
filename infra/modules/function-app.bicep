/*
  Module:      function-app.bicep
  Description: Creates Azure Function App (Flex Consumption, Python 3.11)
               with System-assigned Managed Identity and required app settings.
               Hosts two HTTP trigger functions: analyse_email and send_report.
  Author:      Gayatri Anne
  Created:     24-Jul-2026
*/

@description('Function App name — must be globally unique')
param functionAppName string

@description('Azure region for all resources')
param location string

@description('Resource tags')
param tags object

@description('Storage account name for Function App internal use')
param storageAccountName string

@description('Azure OpenAI endpoint from Azure AI Foundry')
param azureOpenAIEndpoint string

@description('Azure OpenAI API key from Azure AI Foundry')
@secure()
param azureOpenAIApiKey string

// ── App Service Plan — Flex Consumption ───────────────────────────────────────
resource flexPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'asp-${functionAppName}'
  location: location
  tags: tags
  sku: {
    name: 'FC1'     // Flex Consumption SKU
    tier: 'FlexConsumption'
  }
  kind: 'functionapp'
  properties: {
    reserved: true  // Required for Linux
  }
}

// ── Function App ───────────────────────────────────────────────────────────────
resource functionApp 'Microsoft.Web/sites@2023-12-01' = {
  name: functionAppName
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'   // Enables Managed Identity for Key Vault access
  }
  properties: {
    serverFarmId: flexPlan.id
    siteConfig: {
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};EndpointSuffix=${environment().suffixes.storage}'
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsFeatureFlags'
          value: 'EnableWorkerIndexing'   // Required for Python v2 programming model
        }
        {
          name: 'AZURE_OPENAI_ENDPOINT'
          value: azureOpenAIEndpoint
        }
        {
          name: 'AZURE_OPENAI_API_KEY'
          value: azureOpenAIApiKey
        }
      ]
      linuxFxVersion: 'Python|3.11'
    }
    httpsOnly: true
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────
output functionAppName string = functionApp.name
output functionAppId string = functionApp.id
output functionAppPrincipalId string = functionApp.identity.principalId
output functionAppHostname string = functionApp.properties.defaultHostName