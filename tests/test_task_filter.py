"""Tests for the smart task filter."""
from src.utils.task_filter import TaskFilter


def _task(title="", description="", type="", platform="sproutgigs", requirements=None, tags=None):
    return {
        "id": "test",
        "platform": platform,
        "type": type,
        "title": title,
        "description": description,
        "requirements": requirements or [],
        "tags": tags or [],
    }


# ---------------------------------------------------------------------- #
# Allowlist cases — should be allowed
# ---------------------------------------------------------------------- #

def test_ptc_ad_allowed():
    f = TaskFilter()
    d = f.classify(_task(title="View Ad: Crypto Exchange", type="ptc_ad"))
    assert d.allowed
    assert d.confidence > 0.5


def test_video_watch_allowed():
    f = TaskFilter()
    d = f.classify(_task(title="Watch: Funny cats compilation", type="video"))
    assert d.allowed


def test_survey_allowed():
    f = TaskFilter()
    d = f.classify(_task(
        title="Survey: Consumer preferences",
        type="survey",
        requirements=["honest_answers"],
    ))
    assert d.allowed


def test_daily_bonus_allowed():
    f = TaskFilter()
    d = f.classify(_task(title="Daily bonus claim", type="challenge"))
    assert d.allowed


def test_content_engagement_allowed():
    f = TaskFilter()
    d = f.classify(_task(
        title="Like and follow our page",
        type="content",
        requirements=["view_content", "interact"],
    ))
    assert d.allowed


# ---------------------------------------------------------------------- #
# Blocklist cases — should be rejected
# ---------------------------------------------------------------------- #

def test_app_install_rejected():
    f = TaskFilter()
    d = f.classify(_task(title="Download and install our mobile app"))
    assert not d.allowed
    assert "Blocklisted" in d.reason


def test_app_install_variant_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Get bonus",
        description="Install the app from Google Play and open it",
    ))
    assert not d.allowed


def test_phone_verification_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Verify your phone number to unlock reward",
    ))
    assert not d.allowed


def test_sms_otp_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Earn $5",
        description="Enter SMS verification code received on your cell phone",
    ))
    assert not d.allowed


def test_gmail_signup_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Sign up on third-party site with your gmail account",
    ))
    assert not d.allowed


def test_email_verification_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        description="Click the email verification link sent to your inbox",
    ))
    assert not d.allowed


def test_credit_card_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Free trial",
        description="Enter credit card number to start your subscription",
    ))
    assert not d.allowed


def test_kyc_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="KYC verification required",
        description="Upload your ID card and a selfie",
    ))
    assert not d.allowed


def test_address_form_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Enter your mailing address for shipping",
    ))
    assert not d.allowed


def test_refer_friend_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Refer a friend and earn $10",
    ))
    assert not d.allowed


def test_purchase_required_rejected():
    f = TaskFilter()
    d = f.classify(_task(
        title="Purchase required to unlock reward",
    ))
    assert not d.allowed


# ---------------------------------------------------------------------- #
# Edge cases
# ---------------------------------------------------------------------- #

def test_empty_task_allowed_low_confidence():
    f = TaskFilter()
    d = f.classify(_task(title="Generic task"))
    assert d.allowed
    assert d.confidence == 0.5  # baseline, no allowlist match


def test_filter_many_splits_correctly():
    f = TaskFilter()
    tasks = [
        _task(title="Watch video", type="video"),  # allowed
        _task(title="Download app"),  # rejected
        _task(title="PTC ad", type="ptc_ad"),  # allowed
        _task(title="Verify phone"),  # rejected
    ]
    allowed, rejected = f.filter_many(tasks)
    assert len(allowed) == 2
    assert len(rejected) == 2
    # Verify metadata was added
    assert "_filter" in allowed[0]
    assert "_filter" in rejected[0]
    assert allowed[0]["_filter"]["allowed"] is True
    assert rejected[0]["_filter"]["allowed"] is False


def test_tags_are_searched():
    f = TaskFilter()
    d = f.classify(_task(
        title="Easy task",
        tags=["app_install", "mobile"],
    ))
    assert not d.allowed


def test_requirements_are_searched():
    f = TaskFilter()
    d = f.classify(_task(
        title="Simple form",
        requirements=["phone_number_verification"],
    ))
    assert not d.allowed


def test_decision_to_dict_roundtrip():
    f = TaskFilter()
    d = f.classify(_task(title="Watch ad", type="ptc_ad"))
    out = d.to_dict()
    assert "allowed" in out
    assert "reason" in out
    assert "confidence" in out
