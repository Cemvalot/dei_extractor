"""Tests for the language service."""

from pathlib import Path

import pytest
from server.services.language_service import LanguageService


class TestLanguageService:
    """Test cases for LanguageService."""

    def test_default_language_is_greek(self):
        """Test that the default language is Greek."""
        service = LanguageService()
        assert service.get_text("title") == "DEI Extractor Web App"
        assert (
            service.get_text("subtitle")
            == "Ανέβασμα αρχείων PDF ή ZIP για εξαγωγή δεδομένων DEI"
        )

    def test_english_translations(self):
        """Test English translations."""
        service = LanguageService()
        assert service.get_text("title", "en") == "DEI Extractor Web App"
        assert (
            service.get_text("subtitle", "en")
            == "Upload PDF files or ZIP archives to extract DEI data"
        )

    def test_greek_translations(self):
        """Test Greek translations."""
        service = LanguageService()
        assert service.get_text("title", "gr") == "DEI Extractor Web App"
        assert (
            service.get_text("subtitle", "gr")
            == "Ανέβασμα αρχείων PDF ή ZIP για εξαγωγή δεδομένων DEI"
        )

    def test_format_text_with_parameters(self):
        """Test text formatting with parameters."""
        service = LanguageService()
        formatted = service.format_text(
            "file_size_exceeds", "gr", size="150.5", limit="200"
        )
        assert "150.5" in formatted
        assert "200" in formatted

    def test_get_all_texts(self):
        """Test getting all texts for a language."""
        service = LanguageService()
        texts = service.get_all_texts("gr")
        assert isinstance(texts, dict)
        assert "title" in texts
        assert "subtitle" in texts
        assert len(texts) > 10  # Should have many translations

    def test_invalid_language_falls_back_to_greek(self):
        """Test that invalid language codes fall back to Greek."""
        service = LanguageService()
        # Should return Greek text even for invalid language
        result = service.get_text("title", "invalid")
        assert result == "DEI Extractor Web App"

    def test_missing_key_returns_key(self):
        """Test that missing translation keys return the key itself."""
        service = LanguageService()
        result = service.get_text("nonexistent_key", "gr")
        assert result == "nonexistent_key"
