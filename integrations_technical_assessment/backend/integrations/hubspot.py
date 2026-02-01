import json
import secrets
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
import httpx
import asyncio
import base64

# Import the IntegrationItem class and Redis helpers
from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, get_value_redis, delete_key_redis

# --- Configuration ---
# Your Specific Public App Credentials
CLIENT_ID = '45b45c3d-7950-448e-ae29-54a335ad33ff'
CLIENT_SECRET = '9fc1f6bd-86ab-400e-90f2-2461c4a9cac4'

# Ensure this matches your HubSpot App settings exactly
REDIRECT_URI = 'http://localhost:8000/integrations/hubspot/oauth2callback'

# The HubSpot OAuth URL with the required 'contacts' scope
AUTHORIZATION_URL = f'https://app.hubspot.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=crm.objects.contacts.read'


async def authorize_hubspot(user_id, org_id):
    # Create a random state to prevent CSRF attacks and pass user context
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id
    }
    encoded_state = base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')

    # Construct the full auth URL
    auth_url = f'{AUTHORIZATION_URL}&state={encoded_state}'

    # Save the state to Redis (expires in 10 minutes) to verify later
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)

    return auth_url


async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description'))

    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')

    if not encoded_state:
        raise HTTPException(status_code=400, detail='State parameter missing.')

    # Decode state
    try:
        state_data = json.loads(base64.urlsafe_b64decode(encoded_state).decode('utf-8'))
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid state parameter encoding.')
        
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    # Verify state against what we saved in Redis
    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')

    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    # Exchange the code for an access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.hubapi.com/oauth/v1/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        # Clean up the used state
        await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f'Failed to retrieve token: {response.text}')

    # Save the credentials (access_token) to Redis
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)

    # Return a script to close the popup window
    close_window_script = """
    <html>
        <script>
            window.close();
        </script>
    </html>
    """
    return HTMLResponse(content=close_window_script)


async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        # If no credentials, return None so the frontend knows to show "Connect"
        return None
    
    credentials = json.loads(credentials)
    # Note: We do NOT delete the key here so you can reload the page or click 'Load Data' multiple times.
    return credentials


async def create_integration_item_metadata_object(response_json):
    """
    Maps a single HubSpot contact dictionary to an IntegrationItem object.
    """
    properties = response_json.get('properties', {})
    
    # Robust name handling: Try First+Last, then Email, then ID
    first_name = properties.get('firstname', '')
    last_name = properties.get('lastname', '')
    email = properties.get('email', '')
    
    name = f"{first_name} {last_name}".strip()
    if not name:
        name = email or response_json.get('id', 'Unknown Contact')

    integration_item_metadata = IntegrationItem(
        id=response_json.get('id', None),
        name=name,
        type='Contact',
        parent_id=None,
        parent_path_or_name=None,
    )

    return integration_item_metadata


async def get_items_hubspot(credentials):
    """
    Fetches contacts from HubSpot using the access token.
    """
    credentials = json.loads(credentials)
    access_token = credentials.get('access_token')
    
    # HubSpot V3 Contacts API Endpoint
    url = 'https://api.hubapi.com/crm/v3/objects/contacts'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    list_of_integration_item_metadata = []

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code == 200:
        results = response.json().get('results', [])
        for contact in results:
            item = await create_integration_item_metadata_object(contact)
            list_of_integration_item_metadata.append(item)
    else:
        print(f"Error fetching HubSpot contacts: {response.status_code} - {response.text}")

    print(f'list_of_integration_item_metadata: {list_of_integration_item_metadata}')
    return list_of_integration_item_metadata