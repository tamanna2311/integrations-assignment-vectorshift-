# HubSpot Integration Changes

This document details the exact changes made to the codebase to implement the HubSpot integration.

## Backend Changes

### 1. `backend/integrations/hubspot.py`
**Action:** Modified existing file (implemented empty functions).
**Changes:**
- Added necessary imports (`json`, `os`, `secrets`, `base64`, `urllib.parse`, `asyncio`, `httpx`, `HTTPException`, `Request`, `HTMLResponse`).
- Defined environment variables for `CLIENT_ID`, `CLIENT_SECRET`, and `REDIRECT_URI`.
- Defined `SCOPES` required for the integration (`oauth crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read`).
- Implemented `authorize_hubspot(user_id, org_id)`: Generates a secure state, stores it in Redis, and returns the HubSpot OAuth authorization URL.
- Implemented `oauth2callback_hubspot(request)`: Handles the OAuth callback, validates the state, exchanges the authorization code for an access token and refresh token via HubSpot's API, stores the credentials in Redis, and returns an HTML response to close the popup window.
- Implemented `get_hubspot_credentials(user_id, org_id)`: Retrieves the stored credentials from Redis and deletes the key.
- Implemented `get_items_hubspot(credentials)`: Parses the credentials, fetches contacts, companies, and deals concurrently using `asyncio.gather`, handles token expiration by refreshing the token if a 401 error occurs, and maps the results to `IntegrationItem` objects.
- Implemented `create_integration_item_metadata_object(response_json, item_type, portal_id)`: Maps HubSpot API responses to the standard `IntegrationItem` format, extracting names, IDs, timestamps, and generating direct URLs to the HubSpot records.

### 2. `backend/main.py`
**Action:** Modified existing file.
**Changes:**
- Changed the endpoint for loading HubSpot items from `@app.post('/integrations/hubspot/get_hubspot_items')` to `@app.post('/integrations/hubspot/load')`. This change was made to match the dynamic endpoint pattern used by the frontend in `data-form.js` (`/integrations/${endpoint}/load`).
- Renamed the handler function from `load_slack_data_integration` to `load_hubspot_data_integration` for clarity.

## Frontend Changes

### 3. `frontend/src/integrations/hubspot.js`
**Action:** Created new file.
**Changes:**
- Created the `HubSpotIntegration` React component.
- Implemented `handleConnectClick`: Opens a popup window to the backend's `/integrations/hubspot/authorize` endpoint and polls for the window to close.
- Implemented `handleWindowClosed`: Calls the backend's `/integrations/hubspot/credentials` endpoint to retrieve the OAuth credentials once the popup closes, and updates the integration parameters state.
- Added a UI button that toggles between "Connect to HubSpot" and "HubSpot Connected" based on the connection state.

### 4. `frontend/src/integration-form.js`
**Action:** Modified existing file.
**Changes:**
- Imported the `HubSpotIntegration` component from `./integrations/hubspot`.
- Added `'HubSpot': HubSpotIntegration` to the `integrationMapping` object so that HubSpot appears as an option in the Integration Type dropdown.

### 5. `frontend/src/data-form.js`
**Action:** Modified existing file.
**Changes:**
- Added `'HubSpot': 'hubspot'` to the `endpointMapping` object. This ensures that when "HubSpot" is selected, the "Load Data" button correctly calls the `/integrations/hubspot/load` endpoint on the backend.
