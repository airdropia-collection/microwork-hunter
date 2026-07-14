"""Tests for the smart task filter."""
import os

import pytest

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


# ---------------------------------------------------------------------- #
# Social-media tasks — blocked by default
# ---------------------------------------------------------------------- #

def test_facebook_like_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Like our Facebook page for $0.01"))
    assert not d.allowed
    assert "Social-media" in d.reason or "Blocklisted" in d.reason


def test_instagram_follow_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Follow us on Instagram and earn 50 points"))
    assert not d.allowed


def test_tiktok_watch_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Watch our TikTok video"))
    assert not d.allowed


def test_telegram_join_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Join our Telegram channel for bonus"))
    assert not d.allowed


def test_twitter_retweet_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Retweet our post on Twitter"))
    assert not d.allowed


def test_youtube_subscribe_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Subscribe to our YouTube channel"))
    assert not d.allowed


def test_reddit_upvote_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Upvote our Reddit post"))
    assert not d.allowed


def test_linkedin_connect_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Connect with us on LinkedIn"))
    assert not d.allowed


def test_discord_join_rejected_by_default():
    f = TaskFilter()
    d = f.classify(_task(title="Join our Discord server"))
    assert not d.allowed


def test_generic_social_share_rejected():
    f = TaskFilter()
    d = f.classify(_task(title="Social share this post and earn"))
    assert not d.allowed


def test_fb_abbreviation_rejected():
    """`fb like` should also be caught (abbreviation)."""
    f = TaskFilter()
    d = f.classify(_task(title="Get $0.005 for fb like"))
    assert not d.allowed


def test_insta_abbreviation_rejected():
    """`insta follow` should also be caught (abbreviation)."""
    f = TaskFilter()
    d = f.classify(_task(title="Free credits for insta follow"))
    assert not d.allowed


# ---------------------------------------------------------------------- #
# Social-media tasks — allowed when ENABLE_SOCIAL_TASKS=true
# ---------------------------------------------------------------------- #

def test_facebook_like_allowed_when_social_enabled():
    f = TaskFilter(enable_social=True)
    d = f.classify(_task(title="Like our Facebook page for $0.01"))
    assert d.allowed


def test_instagram_follow_allowed_when_social_enabled():
    f = TaskFilter(enable_social=True)
    d = f.classify(_task(title="Follow us on Instagram"))
    assert d.allowed


def test_telegram_join_allowed_when_social_enabled():
    f = TaskFilter(enable_social=True)
    d = f.classify(_task(title="Join our Telegram channel"))
    assert d.allowed


def test_social_enabled_still_blocks_app_install():
    """Even with social enabled, hard-blocklist tasks (app install etc.)
    should still be rejected."""
    f = TaskFilter(enable_social=True)
    d = f.classify(_task(title="Download and install our app"))
    assert not d.allowed


def test_social_enabled_still_blocks_phone_verification():
    f = TaskFilter(enable_social=True)
    d = f.classify(_task(title="Verify your phone number"))
    assert not d.allowed


def test_env_var_enables_social(monkeypatch):
    """ENABLE_SOCIAL_TASKS=true env var should enable social tasks."""
    monkeypatch.setenv("ENABLE_SOCIAL_TASKS", "true")
    f = TaskFilter()  # No explicit arg — should read from env
    d = f.classify(_task(title="Like our Facebook page"))
    assert d.allowed


def test_env_var_false_disables_social(monkeypatch):
    """ENABLE_SOCIAL_TASKS=false env var should disable social tasks."""
    monkeypatch.setenv("ENABLE_SOCIAL_TASKS", "false")
    f = TaskFilter()
    d = f.classify(_task(title="Like our Facebook page"))
    assert not d.allowed


def test_env_var_unset_defaults_to_disabled(monkeypatch):
    """No env var set should default to social disabled."""
    monkeypatch.delenv("ENABLE_SOCIAL_TASKS", raising=False)
    f = TaskFilter()
    d = f.classify(_task(title="Like our Facebook page"))
    assert not d.allowed


def test_ptc_ad_still_allowed_with_social_disabled():
    """Sanity check: PTC ads should still be allowed when social is off."""
    f = TaskFilter()
    d = f.classify(_task(title="View Ad: Crypto", type="ptc_ad"))
    assert d.allowed
