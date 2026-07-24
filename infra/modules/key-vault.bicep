/*
  Module:      key-vault.bicep
  Description: Creates Azure Key Vault for storing the Microsoft Graph API
               OAuth refresh token. Access is granted to the Logic App and
               Function App via Managed Identity (RBAC).
  Author:      Gayatri Anne
  Created:     24-Jul-2026
*/

@description('Key Vault name — must be globally unique, 3-24 chars')
param keyVaultName string

@description('Azure region for all resources')
param location string

@description('Resource tags')
param tags object

@description('Principal ID of the Logic App Managed Identity')
param logicAppPrincipalId string

@description('Principal ID of the Function App Managed Identity')
param functionAppPrincipalId string

// ── Key Vault ──────────────────────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true    // Use RBAC instead of access policies
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

// ── Key Vault Secrets User role for Logic App ──────────────────────────────────
// Allows Logic App Managed Identity to read secrets
resource logicAppKeyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, logicAppPrincipalId, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'   // Key Vault Secrets User built-in role ID
    )
    principalId: logicAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ── Key Vault Secrets User role for Function App ───────────────────────────────
// Allows Function App Managed Identity to read secrets
resource functionAppKeyVaultRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, functionAppPrincipalId, 'KeyVaultSecretsUser')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '4633458b-17de-408a-b874-0445c86b69e6'   // Key Vault Secrets User built-in role ID
    )
    principalId: functionAppPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// ── Outputs ────────────────────────────────────────────────────────────────────
output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
output keyVaultUri string = keyVault.properties.vaultUri