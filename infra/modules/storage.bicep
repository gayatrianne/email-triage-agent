/*
  Module:      storage.bicep
  Description: Creates Azure Storage Account and Blob container for CSV output
               with lifecycle management policy (Hot 7 days, Cool to day 21, Delete day 21)
  Author:      Gayatri Anne
  Created:     24-Jul-2026
*/

@description('Storage account name — must be globally unique, lowercase, 3-24 chars')
param storageAccountName string

@description('Azure region for all resources')
param location string

@description('Resource tags')
param tags object

// ── Storage Account ────────────────────────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS'   // Locally redundant — cheapest option for dev
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}

// ── Blob Service ───────────────────────────────────────────────────────────────
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// ── Container for CSV output ───────────────────────────────────────────────────
resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'email-triage-output'
  properties: {
    publicAccess: 'None'   // Private — access via Managed Identity or SAS only
  }
}

// ── Lifecycle management policy ────────────────────────────────────────────────
resource lifecyclePolicy 'Microsoft.Storage/storageAccounts/managementPolicies@2023-01-01' = {
  parent: storageAccount
  name: 'default'
  properties: {
    policy: {
      rules: [
        {
          name: 'csv-lifecycle'
          enabled: true
          type: 'Lifecycle'
          definition: {
            filters: {
              blobTypes: ['blockBlob']
              prefixMatch: ['email-triage-output/']
            }
            actions: {
              baseBlob: {
                tierToCool: {
                  daysAfterModificationGreaterThan: 7    // Move to Cool after 7 days
                }
                delete: {
                  daysAfterModificationGreaterThan: 21   // Delete after 21 days
                }
              }
            }
          }
        }
      ]
    }
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────
output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id