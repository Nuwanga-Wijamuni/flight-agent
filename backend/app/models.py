from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Search(BaseModel):
    origin: str = Field(pattern=r'^[A-Z]{3}$')
    destination: str = Field(pattern=r'^[A-Z]{3}$')
    departure_date: date
    adults: Literal[1] = 1
    cabin: Literal['economy', 'premium_economy', 'business', 'first'] = 'economy'
    budget_usd: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def check_trip(self):
        if self.origin == self.destination:
            raise ValueError('Choose different origin and destination airports.')
        if self.departure_date < datetime.now(timezone.utc).date():
            raise ValueError('Departure date must be today or later.')
        return self


class Leg(BaseModel):
    origin: str
    destination: str
    departure: str
    arrival: str
    airline: str
    flight_number: str


class Offer(BaseModel):
    id: str
    airline: str
    amount: Decimal
    currency: str
    stops: int
    duration: str
    legs: list[Leg]
    baggage: str
    conditions: str
    expires_at: datetime
    mode: Literal['demo', 'duffel_test']


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class QuoteRequest(BaseModel):
    offer_id: str = Field(min_length=1, max_length=120)


class BookingRequest(BaseModel):
    quote_id: str
    confirmed: bool
    idempotency_key: str = Field(min_length=16, max_length=100)


class Quote(BaseModel):
    id: str
    offer: Offer
    expires_at: datetime
