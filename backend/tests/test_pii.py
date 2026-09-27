from app.guardrails.pii import scrub


def test_email_phone_aadhaar_pan_are_masked() -> None:
    text = (
        "Mail me at vaidya.test@example.com or call +91 98765 43210 / 09876543210. "
        "Aadhaar 2345 6789 0123, PAN ABCDE1234F, account 123456789012345."
    )
    result = scrub(text)
    assert "example.com" not in result.text
    assert "98765" not in result.text and "9876543210" not in result.text
    assert "2345 6789 0123" not in result.text
    assert "ABCDE1234F" not in result.text
    assert "123456789012345" not in result.text
    assert result.found["EMAIL"] == 1
    assert result.found["PHONE"] == 2
    assert result.found["AADHAAR"] == 1
    assert result.found["PAN"] == 1


def test_ordinary_question_is_untouched() -> None:
    question = "Can I patent a formulation from a classical text written in 1920 with 3 herbs?"
    result = scrub(question)
    assert result.text == question
    assert not result.had_pii
