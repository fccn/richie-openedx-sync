"""
Tests for the richie_openedx_sync.utils module.
"""

from unittest.mock import patch
from richie_openedx_sync.utils import transform_language


class TestTransformLanguage:
    """Test cases for the transform_language function."""

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_with_mapping_found(self, mock_get_value):
        """Test transform_language when a mapping is found."""
        mock_get_value.return_value = {"pt_PT": "pt"}

        result = transform_language("my_org", "pt_PT")

        assert result == "pt"
        mock_get_value.assert_called_once()

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_without_mapping(self, mock_get_value):
        """Test transform_language when no mapping is found for the language."""
        mock_get_value.return_value = {"pt_PT": "pt"}

        result = transform_language("my_org", "es")

        assert result == "es"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_empty_mapping(self, mock_get_value):
        """Test transform_language with an empty language mapping."""
        mock_get_value.return_value = {}

        result = transform_language("my_org", "pt_PT")

        assert result == "pt"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_multiple_mappings(self, mock_get_value):
        """Test transform_language with multiple language mappings."""
        mock_get_value.return_value = {"pt": "pt_PT", "fr_CA": "fr"}

        result_pt = transform_language("my_org", "pt")
        result_fr_ca = transform_language("my_org", "fr_CA")
        result_es = transform_language("my_org", "es")

        assert result_pt == "pt_PT"
        assert result_fr_ca == "fr"
        assert result_es == "es"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_different_orgs(self, mock_get_value):
        """Test transform_language with different organizations."""
        def get_value_side_effect(org, key, default):
            if org == "org1":
                return {"pt_PT": "pt"}
            elif org == "org2":
                return {"fr": "fr_FR"}
            return {}

        mock_get_value.side_effect = get_value_side_effect

        result_org1 = transform_language("org1", "pt_PT")
        result_org2 = transform_language("org2", "fr")

        assert result_org1 == "pt"
        assert result_org2 == "fr_FR"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_with_string_mapping(self, mock_get_value):
        """
        Test transform_language when mapping is returned as a Python-style string
        representation and converted by dict().
        """
        mock_get_value.return_value = "{'pt_PT': 'pt', 'fr_CA': 'fr'}"

        result = transform_language("my_org", "pt_PT")

        assert result == "pt"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_with_json_string_mapping(self, mock_get_value):
        """
        Test transform_language when mapping is returned as a JSON string representation.
        """
        mock_get_value.return_value = '{"pt_PT": "pt", "fr_CA": "fr"}'

        result = transform_language("my_org", "pt_PT")

        assert result == "pt"

    @patch("richie_openedx_sync.utils.configuration_helpers.get_value_for_org")
    def test_transform_language_with_no_mapping_uses_default(self, mock_get_value):
        """
        Test transform_language falls back to DEFAULT_LANGUAGE_MAPPING when no mapping is configured.
        """
        mock_get_value.return_value = None

        result = transform_language("my_org", "pt_PT")

        assert result == "pt"
