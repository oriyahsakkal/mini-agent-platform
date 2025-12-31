import pytest
from fastapi import HTTPException
from app.deps import get_tenant_id

def test_get_tenant_id_valid_key():
    assert get_tenant_id("key_tenant_a") == "tenant_a"

def test_get_tenant_id_invalid_key():
    with pytest.raises(HTTPException) as e:
        get_tenant_id("bad_key")
    assert e.value.status_code == 401
