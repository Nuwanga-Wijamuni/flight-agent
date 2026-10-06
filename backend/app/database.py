import json
from sqlalchemy import create_engine, text
from .config import settings

engine = create_engine(settings.database_url, connect_args={'check_same_thread': False} if settings.database_url.startswith('sqlite') else {})


def initialize():
    with engine.begin() as connection:
        for table in ('offers', 'quotes', 'bookings'):
            connection.execute(text(f'CREATE TABLE IF NOT EXISTS {table} (id VARCHAR(120) PRIMARY KEY, payload TEXT NOT NULL)'))
        connection.execute(text('CREATE TABLE IF NOT EXISTS booking_keys (id VARCHAR(100) PRIMARY KEY, quote_id VARCHAR(120) UNIQUE NOT NULL, booking_id VARCHAR(120) NOT NULL)'))


def save(table, identifier, payload):
    if table not in ('offers', 'quotes'):
        raise ValueError('Unsupported storage operation')
    with engine.begin() as connection:
        connection.execute(text(f'INSERT INTO {table} (id, payload) VALUES (:id, :payload) ON CONFLICT (id) DO UPDATE SET payload=excluded.payload'), {'id': identifier, 'payload': json.dumps(payload)})


def get(table, identifier):
    if table not in ('offers', 'quotes', 'bookings'):
        raise ValueError('Unsupported storage operation')
    with engine.connect() as connection:
        row = connection.execute(text(f'SELECT payload FROM {table} WHERE id=:id'), {'id': identifier}).first()
    return json.loads(row[0]) if row else None
