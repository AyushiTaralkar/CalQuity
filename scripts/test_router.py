from app.agent.router import detect_intent, Intent


def test_order_status():
    assert detect_intent(
        "What is the status of ORD-1001?"
    ) == Intent.DATABASE


def test_policy_question():
    assert detect_intent(
        "What is the standard cancellation policy?"
    ) == Intent.RAG


def test_contract_question():
    assert detect_intent(
        "What are Northstar's cancellation terms?"
    ) == Intent.RAG


def test_combined_question():
    assert detect_intent(
        "Can Northstar cancel ORD-1001 without a fee?"
    ) == Intent.COMBINED