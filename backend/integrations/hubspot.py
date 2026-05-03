import json
import os
import secrets
import base64
import urllib.parse

import asyncio
import httpx
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse

from integrations.integration_item import IntegrationItem
from redis_client import add_key_value_redis, delete_key_redis, get_value_redis

CLIENT_ID = os.getenv('HUBSPOT_CLIENT_ID', 'XXX')
CLIENT_SECRET = os.getenv('HUBSPOT_CLIENT_SECRET', 'XXX')
REDIRECT_URI = os.getenv('HUBSPOT_REDIRECT_URI', 'http://localhost:8000/integrations/hubspot/oauth2callback')
SCOPES = 'oauth crm.objects.contacts.read crm.objects.companies.read crm.objects.deals.read'


def _encode_state(state_data: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(state_data).encode('utf-8')).decode('utf-8')


def _decode_state(encoded_state: str) -> dict:
    padding = '=' * (-len(encoded_state) % 4)
    return json.loads(base64.urlsafe_b64decode(f'{encoded_state}{padding}').decode('utf-8'))


def _build_authorization_url(encoded_state: str) -> str:
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'state': encoded_state,
    }
    return f"https://app.hubspot.com/oauth/authorize?{urllib.parse.urlencode(params)}"


async def authorize_hubspot(user_id, org_id):
    state_data = {
        'state': secrets.token_urlsafe(32),
        'user_id': user_id,
        'org_id': org_id,
    }
    encoded_state = _encode_state(state_data)
    await add_key_value_redis(f'hubspot_state:{org_id}:{user_id}', json.dumps(state_data), expire=600)
    return _build_authorization_url(encoded_state)


async def oauth2callback_hubspot(request: Request):
    if request.query_params.get('error'):
        raise HTTPException(status_code=400, detail=request.query_params.get('error_description') or request.query_params.get('error'))

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

    async with httpx.AsyncClient(timeout=30.0) as client:
        response, _ = await asyncio.gather(
            client.post(
                'https://api.hubapi.com/oauth/v1/token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': CLIENT_ID,
                    'client_secret': CLIENT_SECRET,
                    'redirect_uri': REDIRECT_URI,
                    'code': code,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
            ),
            delete_key_redis(f'hubspot_state:{org_id}:{user_id}'),
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=response.text)

    await add_key_value_redis(f'hubspot_credentials:{org_id}:{user_id}', json.dumps(response.json()), expire=600)

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


def _hubspot_item_url(portal_id: str | None, item_type: str, item_id: str) -> str | None:
    if not portal_id:
        return None
    if item_type == 'contact':
        return f'https://app.hubspot.com/contacts/{portal_id}/record/0-1/{item_id}'
    if item_type == 'company':
        return f'https://app.hubspot.com/contacts/{portal_id}/record/0-2/{item_id}'
    if item_type == 'deal':
        return f'https://app.hubspot.com/contacts/{portal_id}/record/0-3/{item_id}'
    return None


def create_integration_item_metadata_object(response_json, item_type: str, portal_id: str | None) -> IntegrationItem:
    properties = response_json.get('properties', {})
    created_at = response_json.get('createdAt')
    updated_at = response_json.get('updatedAt')
    item_id = str(response_json.get('id'))

    if item_type == 'contact':
        name = properties.get('firstname', '') + ' ' + properties.get('lastname', '')
        name = name.strip() or properties.get('email') or f'Contact {item_id}'
    elif item_type == 'company':
        name = properties.get('name') or properties.get('domain') or f'Company {item_id}'
    elif item_type == 'deal':
        name = properties.get('dealname') or f'Deal {item_id}'
    else:
        name = f'{item_type} {item_id}'

    return IntegrationItem(
        id=item_id,
        type=item_type,
        name=name,
        creation_time=created_at,
        last_modified_time=updated_at,
        url=_hubspot_item_url(portal_id, item_type, item_id),
    )


async def _fetch_hubspot_objects(access_token: str, object_type: str, property_list: list[str]) -> list[dict]:
    url = f'https://api.hubapi.com/crm/v3/objects/{object_type}'
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'limit': 100, 'properties': ','.join(property_list)}
    all_results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            response = await client.get(url, headers=headers, params=params)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f'Failed to fetch HubSpot {object_type}: {response.text}')

            data = response.json()
            all_results.extend(data.get('results', []))

            next_after = data.get('paging', {}).get('next', {}).get('after')
            if not next_after:
                break
            params['after'] = next_after

    return all_results


async def _refresh_hubspot_access_token(credentials: dict) -> dict:
    refresh_token = credentials.get('refresh_token')
    if not refresh_token:
        raise HTTPException(status_code=400, detail='Access token expired and no refresh token is available.')

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            'https://api.hubapi.com/oauth/v1/token',
            data={
                'grant_type': 'refresh_token',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': refresh_token,
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail=f'Unable to refresh HubSpot token: {response.text}')

    refreshed = response.json()
    refreshed['refresh_token'] = refreshed.get('refresh_token', refresh_token)
    refreshed['hub_id'] = refreshed.get('hub_id', credentials.get('hub_id'))
    return refreshed


async def get_items_hubspot(credentials):
    parsed = json.loads(credentials)
    access_token = parsed.get('access_token')
    if not access_token:
        raise HTTPException(status_code=400, detail='Missing access token.')

    try:
        contacts, companies, deals = await asyncio.gather(
            _fetch_hubspot_objects(access_token, 'contacts', ['firstname', 'lastname', 'email']),
            _fetch_hubspot_objects(access_token, 'companies', ['name', 'domain']),
            _fetch_hubspot_objects(access_token, 'deals', ['dealname']),
        )
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
        parsed = await _refresh_hubspot_access_token(parsed)
        access_token = parsed.get('access_token')
        contacts, companies, deals = await asyncio.gather(
            _fetch_hubspot_objects(access_token, 'contacts', ['firstname', 'lastname', 'email']),
            _fetch_hubspot_objects(access_token, 'companies', ['name', 'domain']),
            _fetch_hubspot_objects(access_token, 'deals', ['dealname']),
        )

    portal_id = str(parsed.get('hub_id')) if parsed.get('hub_id') is not None else None
    items = [
        *[create_integration_item_metadata_object(item, 'contact', portal_id) for item in contacts],
        *[create_integration_item_metadata_object(item, 'company', portal_id) for item in companies],
        *[create_integration_item_metadata_object(item, 'deal', portal_id) for item in deals],
    ]

    print(f'list_of_integration_item_metadata: {items}')
    return items