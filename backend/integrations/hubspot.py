import json
import os
import secrets
import base64
import urllib.parse

import asyncio
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, delete_key_redis, get_value_redis

def _encode_state(state_data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')

def _decode_state(encoded_state: str) -> dict:
    padding = '=' * (-len(encoded_state) % 4)
    return json.loads(base64.urlsafe_b64decode(f'{encoded_state}{padding}').decode('utf-8'))

async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id,
    }
    encoded_state = _encode_state(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
    
    params = {
        'code': 'mock_code_123',
        'state': encoded_state
    }
    return f"http://localhost:8000/integrations/hubspot/oauth2callback?{urllib.parse.urlencode(params)}"

async def oauth2callback_hubspot(request: Request):
    code = request.query_params.get('code')
    encoded_state = request.query_params.get('state')
    if not code or not encoded_state:
        raise HTTPException(status_code=400, detail='Missing code or state.')

    state_data = _decode_state(encoded_state)
    original_state = state_data.get('state')
    user_id = state_data.get('user_id')
    org_id = state_data.get('org_id')

    saved_state = await get_value_redis(f'hubspot_state:{org_id}:{user_id}')
    if not saved_state or original_state != json.loads(saved_state).get('state'):
        raise HTTPException(status_code=400, detail='State does not match.')

    await delete_key_redis(f'hubspot_state:{org_id}:{user_id}')

    mock_credentials = {
        'access_token': 'mock_access_token',
        'refresh_token': 'mock_refresh_token',
        'expires_in': 1800,
        'hub_id': '12345678'
    }
    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(mock_credentials), expire=600)

    return HTMLResponse(content="""
    <html><script>window.close();</script></html>
    """)

async def get_hubspot_credentials(user_id, org_id):
    credentials = await get_value_redis(f'hubspot_credentials:{org_id}:{user_id}')
    if not credentials:
        raise HTTPException(status_code=400, detail='No credentials found.')
    credentials = json.loads(credentials)
    await delete_key_redis(f'hubspot_credentials:{org_id}:{user_id}')
    return credentials

async def get_items_hubspot(credentials):
    items = [
        IntegrationItem(id='1', type='contact', name='John Doe (Mock)', creation_time='2023-01-01T00:00:00Z', last_modified_time='2023-01-01T00:00:00Z', url='https://app.hubspot.com/contacts/12345678/record/0-1/1'),
        IntegrationItem(id='2', type='company', name='Acme Corp (Mock)', creation_time='2023-01-01T00:00:00Z', last_modified_time='2023-01-01T00:00:00Z', url='https://app.hubspot.com/contacts/12345678/record/0-2/2'),
        IntegrationItem(id='3', type='deal', name='Big Sale (Mock)', creation_time='2023-01-01T00:00:00Z', last_modified_time='2023-01-01T00:00:00Z', url='https://app.hubspot.com/contacts/12345678/record/0-3/3'),
    ]
    return items