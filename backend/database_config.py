"""Environment-only database selection. No connection or schema mutation here."""
import os
from sqlalchemy.engine import make_url

def database_url(value,sqlite_default):
    if not value or not value.strip():return sqlite_default
    try:
        url=make_url(value.strip())
        if url.drivername in ('postgres','postgresql'):url=url.set(drivername='postgresql+psycopg')
        if url.get_backend_name() not in ('postgresql','sqlite'):raise ValueError()
        return url.render_as_string(hide_password=False)
    except Exception:
        raise ValueError('Invalid DATABASE_URL. Use a SQLite URL or a PostgreSQL URL; percent-encode password special characters.') from None

def engine_options(uri):
    url=make_url(uri)
    if url.get_backend_name()=='postgresql':
        return {
            'pool_pre_ping':True,
            'pool_size':int(os.getenv('DB_POOL_SIZE','6')),
            'max_overflow':int(os.getenv('DB_MAX_OVERFLOW','6')),
            'pool_timeout':int(os.getenv('DB_POOL_TIMEOUT','15')),
            'pool_recycle':int(os.getenv('DB_POOL_RECYCLE','600')),
            'connect_args':{
                'connect_timeout':10,
                'keepalives':1,
                'keepalives_idle':30,
                'keepalives_interval':10,
                'keepalives_count':5,
            },
        }
    return {'pool_pre_ping':True}
