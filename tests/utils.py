def assert_input_properties_error(exc_info, expected_property_path, expected_reason):
    if not hasattr(exc_info.value, "errors"):
        assert exc_info.value.property_path == expected_property_path
        assert exc_info.value.reason == expected_reason
    else:
        assert "Invalid arguments" in str(exc_info.value)
        errors = exc_info.value.errors
        assert errors is not None
        assert len(errors) == 1
        assert errors[0]["property_path"] == expected_property_path
        assert expected_reason in errors[0]["reason"]
