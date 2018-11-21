import pytest
import os
from fireapi import FireDb

user = os.environ.get('ORA_USER') or "fire"
password = os.environ.get('ORA_PASSWORD') or "fire"
host = os.environ.get('ORA_HOST') or "localhost"
port = os.environ.get('ORA_PORT') or "1521"
db = os.environ.get('ORA_db') or "xe"


@pytest.fixture(scope="session")
def firedb():
    return FireDb(f"{user}:{password}@{host}:{port}/{db}")
