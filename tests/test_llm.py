from app.llm import mock_llm_complete

def test_mock_llm_deterministic():
    prompt = "hello"
    r1 = mock_llm_complete("gpt-4o", prompt)
    r2 = mock_llm_complete("gpt-4o", prompt)
    assert r1 == r2
