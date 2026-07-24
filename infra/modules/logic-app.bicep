/*
  Module:      logic-app.bicep
  Description: Creates Azure Logic App (Consumption, Stateful) with
               System-assigned Managed Identity for secure access to
               Key Vault and Blob Storage.
  Author:      Gayatri Anne
  Created:     24-Jul-2026
*/

@description('Logic App name — must be globally unique')
param logicAppName string

@description('Azure region for all resources')
param location string

@description('Resource tags')
param tags object

// ── Logic App ──────────────────────────────────────────────────────────────────
resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
  name: logicAppName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'   // Enables Managed Identity for Key Vault and Blob access
  }
  properties: {
    state: 'Enabled'
    definition: {
      '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
      contentVersion: '1.0.0.0'
      triggers: {}
      actions: {}
      outputs: {}
    }
    parameters: {}
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────
output logicAppName string = logicApp.name
output logicAppId string = logicApp.id
output logicAppPrincipalId string = logicApp.identity.principalId