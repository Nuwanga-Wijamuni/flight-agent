import os
os.environ['DATABASE_URL'] = 'sqlite://'
os.environ['FLIGHT_PROVIDER'] = 'demo'
os.environ['GEMINI_API_KEY'] = ''

from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app import database as db
from app.main import app
from app.providers import duffel
from app.config import settings


@pytest.fixture
def client():
    previous = db.engine
    db.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    with TestClient(app) as client:
        yield client
    db.engine.dispose()
    db.engine = previous


def trip():
    return {'origin': 'CMB', 'destination': 'SIN', 'departure_date': (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat(), 'budget_usd': 400}


def test_search_quote_confirmation_and_duplicate_protection(client):
    result = client.post('/api/search', json=trip())
    assert result.status_code == 200
    offers = result.json()['offers']
    assert len(offers) == 2
    assert all(float(o['amount']) <= 400 and o['mode'] == 'demo' for o in offers)
    quote = client.post('/api/quotes', json={'offer_id': offers[0]['id']}).json()
    request = {'quote_id': quote['id'], 'confirmed': False, 'idempotency_key': str(uuid4())}
    original_key = request['idempotency_key']
    assert client.post('/api/bookings', json=request).status_code == 400
    request['confirmed'] = True
    booking = client.post('/api/bookings', json=request)
    assert booking.status_code == 200
    assert booking.json()['status'] == 'simulated'
    assert 'no airline ticket issued' in booking.json()['message']
    assert client.post('/api/bookings', json=request).json()['id'] == booking.json()['id']
    request['idempotency_key'] = str(uuid4())
    assert client.post('/api/bookings', json=request).json()['id'] == booking.json()['id']
    quote2 = client.post('/api/quotes', json={'offer_id': offers[1]['id']}).json()
    request['quote_id'] = quote2['id']
    request['idempotency_key'] = original_key
    assert client.post('/api/bookings', json=request).status_code == 409


def test_expired_quote_cannot_book(client):
    offers = client.post('/api/search', json=trip()).json()['offers']
    quote = client.post('/api/quotes', json={'offer_id': offers[0]['id']}).json()
    quote['expires_at'] = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    db.save('quotes', quote['id'], quote)
    response = client.post('/api/bookings', json={'quote_id': quote['id'], 'confirmed': True, 'idempotency_key': str(uuid4())})
    assert response.status_code == 409


def test_agent_search_and_clarification(client):
    day = trip()['departure_date']
    response = client.post('/api/chat', json={'message': f'From Colombo to Singapore on {day} under $400'})
    assert response.status_code == 200
    assert len(response.json()['offers']) == 2
    for message in ['Book a flight', f'From Colombo to Singapore on {day} return', f'From Colombo to Singapore on {day} for 2 adults']:
        response = client.post('/api/chat', json={'message': message})
        assert response.status_code == 200
        assert response.json()['trip'] is None
        assert response.json()['offers'] == []


def test_invalid_trip_rejected(client):
    data = trip()
    data['departure_date'] = '2000-01-01'
    assert client.post('/api/search', json=data).status_code == 422
    data = trip()
    data['destination'] = 'CMB'
    assert client.post('/api/search', json=data).status_code == 422
    assert client.post('/api/quotes', json={'offer_id': 'missing'}).status_code == 404


def test_live_provider_token_rejected_before_network(monkeypatch):
    import asyncio
    monkeypatch.setattr(settings, 'duffel_access_token', 'duffel_live_example')
    with pytest.raises(ValueError, match='Live tokens are disabled'):
        asyncio.run(duffel('POST', '/air/offer_requests'))
