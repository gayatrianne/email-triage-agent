"""
Module:
    generate_refresh_token.py
Description:
    Authenticates a user with Microsoft Entra ID using the Device Code Flow
    and retrieves a Microsoft Graph refresh token. The refresh token is then
    stored in Azure Key Vault and can be used by the Logic App to obtain
    new access tokens without requiring the user to sign in again.
Author:
    Gayatri Anne
Created:
    23-Jul-2026
Usage:
    Run this script once from the command line. Follow the displayed
    instructions to authenticate at https://microsoft.com/devicelogin.
    After successful authentication, the refresh token is automatically
    saved to Azure Key Vault.
"""

import msal                          # Microsoft Authentication Library
import os                            # For reading environment variables
from azure.identity import DefaultAzureCredential  # For Key Vault access
from azure.keyvault.secrets import SecretClient    # For storing token in Key Vault

# ── Configuration ─────────────────────────────────────────────────────────────
# Replace these with your actual values from the app registration
CLIENT_ID   = "57b54c76-1f5f-420f-b87f-7ed2806b5ad0"       # Application (client) ID
TENANT_ID   = "common"                    # Use 'common' for personal Outlook accounts
KEY_VAULT_URL = "https://kv-email-triage-dev.vault.azure.net/"

# Microsoft Graph scopes needed for reading and sending emails
SCOPES = [
    "https://graph.microsoft.com/Mail.Read",
    "https://graph.microsoft.com/Mail.Send"
                    
]

def generate_and_store_refresh_token():
    """
    Uses Device Code Flow to authenticate the user and retrieve a refresh token.
    Stores the refresh token securely in Azure Key Vault.
    """

    # Initialise MSAL public client application for device code flow
    # PublicClientApplication is used for apps that cannot store secrets securely
    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}"
    )

    # Initiate device code flow — this returns a URL and code for the user to enter
    flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise ValueError(f"Failed to create device flow: {flow.get('error_description')}")

    # Display instructions to the user
    print("\n" + "="*60)
    print("ACTION REQUIRED:")
    print(flow["message"])  # Contains the URL and code to enter
    print("="*60 + "\n")

    # Wait for the user to complete authentication in the browser
    # This blocks until the user signs in or the flow times out
    result = app.acquire_token_by_device_flow(flow)

    if "refresh_token" not in result:
        # Authentication failed — print error details
        raise ValueError(f"Authentication failed: {result.get('error_description')}")

    # Extract the refresh token from the result
    refresh_token = result["refresh_token"]
    print("✅ Authentication successful — refresh token obtained")

    # Store the refresh token securely in Azure Key Vault
    # Uses DefaultAzureCredential — works with Azure CLI login locally
    #credential = DefaultAzureCredential()
    #secret_client = SecretClient(vault_url=KEY_VAULT_URL, credential=credential)

    # Print the refresh token so we can manually store it in Key Vault
    print("\n" + "="*60)
    print("REFRESH TOKEN (copy this into Key Vault manually):")
    print("="*60)
    print(refresh_token)
    print("="*60 + "\n")

    # Save the refresh token as a secret named 'graph-refresh-token'
    #secret_client.set_secret("graph-refresh-token", refresh_token)
    #print("✅ Refresh token stored in Key Vault as 'graph-refresh-token'")

if __name__ == "__main__":
    generate_and_store_refresh_token()