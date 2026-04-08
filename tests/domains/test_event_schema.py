"""测试 Event schema + validate_event"""
import pytest
from pydantic import ValidationError
from domains.events.schema import validate_event


class TestEventSchema:
    def test_valid_event_type_with_correct_payload(self):
        result = validate_event("auth.login", {
            "device_info": {"os": "win"},
            "ip_address": "127.0.0.1",
        })
        assert result["ip_address"] == "127.0.0.1"

    def test_unknown_event_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown event type"):
            validate_event("video.stream_start", {"foo": "bar"})

    def test_missing_required_field_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_event("ppt.generate", {"template": "basic"})

    def test_ppt_generate_validates_all_fields(self):
        result = validate_event("ppt.generate", {
            "student_count": 30,
            "template": "standard",
            "duration_seconds": 120,
        })
        assert result["student_count"] == 30
        assert result["duration_seconds"] == 120

    def test_app_error_validates(self):
        result = validate_event("app.error", {
            "error_type": "ValueError",
            "message": "test",
        })
        assert result["error_type"] == "ValueError"
