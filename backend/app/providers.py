from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
import httpx
from .config import settings
from .models import Search, Offer, Leg


def now():
    return datetime.now(timezone.utc)


def demo_offers(trip: Search):
    offers = []
    for index, (name, price, stops) in enumerate([('Demo Air', '245.00', 1), ('Demo Direct', '318.00', 0), ('Demo Premium', '425.00', 0)]):
        dep = datetime.combine(trip.departure_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=7 + index * 3)
        duration = 7 if stops else 4
        routes = [(trip.origin, 'DEMO'), ('DEMO', trip.destination)] if stops else [(trip.origin, trip.destination)]
        legs = [Leg(origin=a, destination=b, departure=(dep + timedelta(hours=i * 4)).isoformat(), arrival=(dep + timedelta(hours=i * 4 + (3 if stops else 4))).isoformat(), airline=name, flight_number=f'DM{100+index*10+i}') for i, (a, b) in enumerate(routes)]
        amount = Decimal(price) * (Decimal('2') if trip.cabin != 'economy' else Decimal('1'))
        offers.append(Offer(id=f'demo_{uuid4().hex}', airline=name, amount=amount, currency='USD', stops=stops, duration=f'PT{duration}H', legs=legs, baggage='Demo allowance: 1 cabin bag + 1 checked bag', conditions='Illustrative fare. No real airline, inventory, or ticket.', expires_at=now() + timedelta(minutes=15), mode='demo'))
    return offers


async def duffel(method, path, body=None):
    token = settings.duffel_access_token
    if not token.startswith('duffel_test_'):
        raise ValueError('Provide a Duffel test token. Live tokens are disabled in this project.')
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.request(method, 'https://api.duffel.com' + path, headers={'Authorization': f'Bearer {token}', 'Duffel-Version': 'v2', 'Accept': 'application/json'}, json={'data': body} if body else None)
    if not response.is_success:
        raise ValueError(f'Flight provider request failed (HTTP {response.status_code}). Try again or check your test credentials.')
    data = response.json()['data']
    if data.get('live_mode', False):
        raise ValueError('Live flight data is disabled in this project.')
    return data


def normalize(data):
    legs = []
    slices = data['slices']
    for flight in slices:
        for segment in flight['segments']:
            legs.append(Leg(origin=segment['origin']['iata_code'], destination=segment['destination']['iata_code'], departure=segment['departing_at'], arrival=segment['arriving_at'], airline=segment['operating_carrier']['name'], flight_number=segment['operating_carrier']['iata_code'] + segment['operating_carrier_flight_number']))
    return Offer(id=data['id'], airline=data['owner']['name'], amount=Decimal(data['total_amount']), currency=data['total_currency'], stops=sum(len(s['segments']) - 1 for s in slices), duration=slices[0]['duration'], legs=legs, baggage='Check the provider fare details; allowance varies by passenger and segment.', conditions='Sandbox fare. Review airline conditions before implementing real ticket issuance.', expires_at=data['expires_at'], mode='duffel_test')


async def search(trip):
    if settings.flight_provider == 'demo':
        offers = demo_offers(trip)
    else:
        data = await duffel('POST', '/air/offer_requests?return_offers=true', {'slices': [{'origin': trip.origin, 'destination': trip.destination, 'departure_date': trip.departure_date.isoformat()}], 'passengers': [{'type': 'adult'}], 'cabin_class': trip.cabin})
        offers = [normalize(item) for item in data.get('offers', [])]
    # A USD budget cannot safely filter an offer in another currency without an FX source.
    offers = [o for o in offers if trip.budget_usd is None or o.currency != 'USD' or o.amount <= trip.budget_usd]
    return sorted(offers, key=lambda o: (o.currency, o.amount))[:20]


async def refresh(offer):
    if offer.mode == 'demo':
        return offer
    return normalize(await duffel('GET', f'/air/offers/{offer.id}'))
