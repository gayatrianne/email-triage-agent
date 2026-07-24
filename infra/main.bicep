/*
  Module:      main.bicep
  Description: Main Bicep template for the Galaxy Telecom AI Email Triage Agent.
               Deploys all Azure resources into a single resource group:
               - Storage Account with lifecycle management
               - Key Vault with RBAC for Managed Identities
               - Function App (Flex Consumption, Python 3.11)
               - Logic App (Consumption, Stateful)
  Author:      Gayatri Anne
  Created:     24-Jul-2026
  Usage:
               az deployment group create \
                 --resource-group rg-email-triage-dev \
                 --template-file infra/main.bicep \
                 --parameters @infra/parameters/dev.parameters.json
*/

@description('Azure region for all resources')
param location string = 'uksouth'

@description('Environment name — used in resource naming')
param environment string = 'dev'

@description('Azure OpenAI endpoint from Azure AI Foundry')
param azureOpenAIEndpoint string

@description('Azure OpenAI API key from Azure AI Foundry')
@secure()
param azureOpenAIApiKey string

// ── Resource naming ────────────────────────────────────────────────────────────
var storageAccountName = 'stemailtirage${environment}'
var keyVaultName = 'kv-email-triage-${environment}'
var functionAppName = 'func-email-triage-${environment}'
var logicAppName = 'logic-email-triage-${environment}'

// ── Tags applied to all resources ─────────────────────────────────────────────
var tags = {
  Project: 'customer-service-ai'
  Environment: environment
}

// ── Storage Account ────────────────────────────────────────────────────────────
module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    storageAccountName: storageAccountName
    location: location
    tags: tags
  }
}

// ── Function App ───────────────────────────────────────────────────────────────
// Deployed before Key Vault so we can pass its Managed Identity principal ID
module functionApp 'modules/function-app.bicep' = {
  name: 'functionApp'
  params: {
    functionAppName: functionAppName
    location: location
    tags: tags
    storageAccountName: storageAccountName
    azureOpenAIEndpoint: azureOpenAIEndpoint
    azureOpenAIApiKey: azureOpenAIApiKey
  }
  dependsOn: [storage]
}

// ── Logic App ──────────────────────────────────────────────────────────────────
// Deployed before Key Vault so we can pass its Managed Identity principal ID
module logicApp 'modules/logic-app.bicep' = {
  name: 'logicApp'
  params: {
    logicAppName: logicAppName
    location: location
    tags: tags
  }
}

// ── Key Vault ──────────────────────────────────────────────────────────────────
// Deployed