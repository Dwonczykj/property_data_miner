import pytest
from file_appender import JsonFileReader

def test_can_read_json_file():
    reader = JsonFileReader('ASDA').openStream()
    data = reader.read()
    reader.closeStream()
    assert data is not None