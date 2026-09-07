from app import settings
from app.extensions import db
from app.models import SystemConfig
from app.security import decrypt, encrypt


def test_defaults_are_used_when_nothing_is_stored(app):
    assert settings.get("speech_provider") == "deepgram"
    assert settings.get_int("meeting_retention_days") == 30
    assert settings.get_bool("diarization_enabled") is True
    assert settings.get("llm_api_key") == ""


def test_secrets_are_encrypted_at_rest(app):
    settings.save({"llm_api_key": "sk-secret-value"})

    row = db.session.query(SystemConfig).filter_by(key="llm_api_key").first()
    assert row.value != "sk-secret-value"
    assert row.value.startswith("enc:")
    assert settings.get("llm_api_key") == "sk-secret-value"


def test_blank_secret_keeps_the_stored_value(app):
    settings.save({"llm_api_key": "sk-first"})
    settings.save({"llm_api_key": ""})
    assert settings.get("llm_api_key") == "sk-first"


def test_plain_values_round_trip(app):
    settings.save({"llm_model": "gpt-4o-mini", "meeting_retention_days": "7"})
    assert settings.get("llm_model") == "gpt-4o-mini"
    assert settings.get_int("meeting_retention_days") == 7


def test_unknown_keys_are_ignored(app):
    settings.save({"not_a_setting": "x"})
    assert db.session.query(SystemConfig).filter_by(key="not_a_setting").first() is None


def test_snapshot_covers_every_setting(app):
    settings.save({"llm_api_key": "sk-abc"})
    snapshot = settings.snapshot()
    assert set(snapshot) == {spec.key for spec in settings.SETTINGS}
    assert snapshot["llm_api_key"] == "sk-abc"
    assert snapshot["minutes_prompt"]


def test_encryption_helpers_round_trip():
    assert decrypt(encrypt("value")) == "value"
    assert decrypt("plain-legacy-value") == "plain-legacy-value"
    assert encrypt("") == ""


def test_admin_can_save_settings_from_the_screen(signed_in, app):
    response = signed_in.post(
        "/admin/settings",
        data={"group": "llm", "llm_base_url": "https://api.openai.com/v1",
              "llm_model": "gpt-4o-mini", "llm_api_key": "sk-from-form",
              "llm_temperature": "0.3", "llm_max_output_tokens": "2000",
              "llm_timeout_seconds": "120"},
    )
    assert response.status_code == 302
    with app.app_context():
        assert settings.get("llm_model") == "gpt-4o-mini"
        assert settings.get("llm_api_key") == "sk-from-form"


def test_a_saved_secret_can_be_removed_from_the_screen(signed_in, app):
    settings.save({"deepgram_api_key": "dg-secret"})
    assert settings.get("deepgram_api_key") == "dg-secret"

    signed_in.post(
        "/admin/settings",
        data={"group": "speech", "speech_provider": "deepgram", "deepgram_api_key": "",
              "deepgram_api_key__clear": "on"},
    )
    with app.app_context():
        assert settings.get("deepgram_api_key") == ""
