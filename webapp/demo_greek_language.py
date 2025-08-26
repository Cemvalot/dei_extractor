#!/usr/bin/env python3
"""
Demonstration script for the DEI Extractor Web App with Greek language support.

This script shows how the language service works and displays various UI elements
in both Greek and English.
"""

from server.services.language_service import LanguageService


def demo_language_service():
    """Demonstrate the language service functionality."""
    print("🌐 DEI Extractor Web App - Language Service Demo")
    print("=" * 60)

    # Initialize language service
    ls = LanguageService()

    # Test key UI elements in both languages
    ui_elements = [
        "title",
        "subtitle",
        "process_button",
        "download_button",
        "upload_label",
        "filter_label",
        "verbose_label",
        "language_label",
        "language_greek",
        "language_english",
        "processing_options",
        "progress_processing",
        "progress_complete",
    ]

    print("\n📋 UI Elements in Greek (Default):")
    print("-" * 40)
    for element in ui_elements:
        text = ls.get_text(element, "gr")
        print(f"{element:25}: {text}")

    print("\n📋 UI Elements in English:")
    print("-" * 40)
    for element in ui_elements:
        text = ls.get_text(element, "en")
        print(f"{element:25}: {text}")

    # Test text formatting
    print("\n🔧 Text Formatting Examples:")
    print("-" * 40)

    # File size error message
    formatted_gr = ls.format_text("file_size_exceeds", "gr", size="150.5", limit="200")
    formatted_en = ls.format_text("file_size_exceeds", "en", size="150.5", limit="200")

    print(f"Greek file size error:  {formatted_gr}")
    print(f"English file size error: {formatted_en}")

    # Test fallback behavior
    print("\n🔄 Fallback Behavior:")
    print("-" * 40)
    print(f"Invalid language: {ls.get_text('title', 'invalid')}")
    print(f"Missing key: {ls.get_text('nonexistent_key', 'gr')}")

    print("\n✅ Language service demo completed successfully!")
    print("\n🚀 To run the web app:")
    print("   Streamlit mode: streamlit run streamlit_app.py")
    print("   FastAPI mode:   uvicorn server.main:app --reload")


if __name__ == "__main__":
    demo_language_service()
