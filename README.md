# VectorShift Integrations Assessment

Hey team, here's my submission for the integrations technical assessment. 

I've completed both parts of the assignment: implementing the HubSpot OAuth flow and the data loading logic to fetch contacts, companies, and deals.

## What's Included

- **HubSpot OAuth Flow**: Added the backend endpoints (`authorize`, `oauth2callback`, `credentials`) to handle the HubSpot OAuth 2.0 flow. State validation is included to prevent CSRF attacks, and tokens are temporarily stored in Redis.
- **Data Loading**: Implemented the `get_items_hubspot` function to fetch contacts, companies, and deals. It automatically refreshes the access token if it expires (handling 401s) and maps the responses to the standard `IntegrationItem` format.
- **Frontend Integration**: Built the `HubSpotIntegration` React component to handle the popup window flow. Hooked it up to the existing `integration-form.js` and `data-form.js` so it works seamlessly alongside Notion and Airtable.

## Running the Project

You'll need a HubSpot Developer account to test this out. 

### 1. Set up your HubSpot App
1. Create a new app in your HubSpot Developer account.
2. Set the redirect URI to `http://localhost:8000/integrations/hubspot/oauth2callback`.
3. Add the following scopes: `oauth`, `crm.objects.contacts.read`, `crm.objects.companies.read`, `crm.objects.deals.read`.
4. Grab your Client ID and Client Secret.

### 2. Start the Backend
Make sure you have Redis running (`redis-server`), then start the FastAPI server:

```bash
cd backend
export HUBSPOT_CLIENT_ID="your_client_id"
export HUBSPOT_CLIENT_SECRET="your_client_secret"
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. Start the Frontend
In a new terminal, spin up the React app:

```bash
cd frontend
npm install
npm start
```

## Testing it out

1. Open up `http://localhost:3000` in your browser.
2. Select "HubSpot" from the dropdown and hit "Connect to HubSpot".
3. Go through the OAuth flow in the popup window.
4. Once connected, hit "Load Data" to see your HubSpot contacts, companies, and deals fetched and displayed.

Let me know if you have any questions or run into any issues getting it set up!
