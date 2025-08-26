"""Language service for handling translations in the web app."""

from pathlib import Path
from typing import Any, Dict

import yaml


class LanguageService:
    """Service for handling language translations and UI text."""

    def __init__(self, config_path: str = None):
        """Initialize the language service.

        Args:
            config_path: Path to the app configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "app_config.yaml"

        self.config_path = Path(config_path)
        self._translations = self._load_translations()

    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translations from the configuration file."""
        if not self.config_path.exists():
            return self._get_default_translations()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("ui_text", self._get_default_translations())
        except Exception as e:
            print(f"Warning: Could not load translations from {self.config_path}: {e}")
            return self._get_default_translations()

    def _get_default_translations(self) -> Dict[str, Dict[str, str]]:
        """Get default translations if config file is not available."""
        return {
            "en": {
                "title": "DEI Extractor Web App",
                "subtitle": "Upload PDF files or ZIP archives to extract DEI data",
                "upload_label": "Upload PDF files or ZIP archive",
                "upload_help": "Upload multiple PDF files or a single ZIP archive containing PDFs",
                "filter_label": "Keep only Εκαθαριστικός",
                "filter_help": "Apply filtering to keep only Εκαθαριστικός records",
                "verbose_label": "Verbose logs",
                "verbose_help": "Enable verbose logging during processing",
                "language_label": "Language",
                "language_help": "UI language (extraction remains Greek-capable)",
                "process_button": "Process Files",
                "download_button": "Download Results",
                "browse_files": "Browse Files",
                "drop_files_here": "Drop files here or click to browse",
                "supports_files": "Supports PDF files and ZIP archives",
                "selected_files": "Selected Files:",
                "processing_options": "Processing Options",
                "progress_processing": "Processing files...",
                "progress_complete": "Processing completed successfully!",
                "progress_preparing": "Preparing files...",
                "progress_validating": "Validating input...",
                "progress_creating_output": "Creating output files...",
                "progress_creating_zip": "Creating ZIP file...",
                "uploaded_files": "Uploaded files:",
                "total_rows": "Total rows:",
                "download_results_zip": "Download Results (ZIP)",
                "processing_complete": "Processing Complete",
                "no_files_uploaded": "No files uploaded",
                "no_valid_files": "No valid files found. Please upload PDF or ZIP files.",
                "file_size_exceeds": "Total file size ({size}MB) exceeds limit ({limit}MB)",
                "error_processing": "Error during processing",
                "validation_failed": "Validation failed",
                "processing_failed": "Processing failed",
                "output_preview": "Output Preview",
                "output_preview_not_available": "Output preview not available",
                "warnings_during_processing": "Warnings during processing:",
                "footer_text": "DEI Extractor Web App | Built with Streamlit",
                "footer_security": "Files are processed temporarily and not stored on the server",
                "health_check": "Health check endpoint",
                "api_description": "Web API for extracting DEI data from PDF files",
                "no_files_selected": "No files selected",
                "processing_failed_api": "Processing failed",
                "download_failed": "Download failed",
                "drag_drop_zone": "Drag and drop zone",
                "file_validation": "File validation",
                "file_size_format": "File size format",
                "progress_tracking": "Progress tracking",
                "error_handling": "Error handling",
                "success_messages": "Success messages",
            },
            "gr": {
                "title": "DEI Extractor Web App",
                "subtitle": "Ανέβασμα αρχείων PDF ή ZIP για εξαγωγή δεδομένων DEI",
                "upload_label": "Ανέβασμα αρχείων PDF ή ZIP",
                "upload_help": "Ανέβασμα πολλαπλών αρχείων PDF ή ενός αρχείου ZIP που περιέχει PDF",
                "filter_label": "Διατήρηση μόνο Εκαθαριστικός",
                "filter_help": "Εφαρμογή φιλτραρίσματος για διατήρηση μόνο εγγραφών Εκαθαριστικός",
                "verbose_label": "Λεπτομερείς καταγραφές",
                "verbose_help": "Ενεργοποίηση λεπτομερών καταγραφών κατά την επεξεργασία",
                "language_label": "Γλώσσα",
                "language_help": "Γλώσσα διεπαφής (η εξαγωγή παραμένει σε ελληνική)",
                "process_button": "Επεξεργασία Αρχείων",
                "download_button": "Λήψη Αποτελεσμάτων",
                "browse_files": "Επιλογή Αρχείων",
                "drop_files_here": "Αφήστε αρχεία εδώ ή κάντε κλικ για περιήγηση",
                "supports_files": "Υποστηρίζει αρχεία PDF και ZIP",
                "selected_files": "Επιλεγμένα Αρχεία:",
                "processing_options": "Επιλογές Επεξεργασίας",
                "progress_processing": "Επεξεργασία αρχείων...",
                "progress_complete": "Η επεξεργασία ολοκληρώθηκε επιτυχώς!",
                "progress_preparing": "Προετοιμασία αρχείων...",
                "progress_validating": "Επικύρωση εισόδου...",
                "progress_creating_output": "Δημιουργία αρχείων εξόδου...",
                "progress_creating_zip": "Δημιουργία αρχείου ZIP...",
                "uploaded_files": "Ανεβασμένα αρχεία:",
                "total_rows": "Συνολικές γραμμές:",
                "download_results_zip": "Λήψη Αποτελεσμάτων (ZIP)",
                "processing_complete": "Η Επεξεργασία Ολοκληρώθηκε",
                "no_files_uploaded": "Δεν ανέβηκαν αρχεία",
                "no_valid_files": "Δεν βρέθηκαν έγκυρα αρχεία. Παρακαλώ ανεβάστε αρχεία PDF ή ZIP.",
                "file_size_exceeds": "Το συνολικό μέγεθος αρχείων ({size}MB) υπερβαίνει το όριο ({limit}MB)",
                "error_processing": "Σφάλμα κατά την επεξεργασία",
                "validation_failed": "Η επικύρωση απέτυχε",
                "processing_failed": "Η επεξεργασία απέτυχε",
                "output_preview": "Προεπισκόπηση Εξόδου",
                "output_preview_not_available": "Η προεπισκόπηση εξόδου δεν είναι διαθέσιμη",
                "warnings_during_processing": "Προειδοποιήσεις κατά την επεξεργασία:",
                "footer_text": "DEI Extractor Web App | Χτισμένο με Streamlit",
                "footer_security": "Τα αρχεία επεξεργάζονται προσωρινά και δεν αποθηκεύονται στον διακομιστή",
                "health_check": "Τελεστής ελέγχου υγείας",
                "api_description": "Web API για εξαγωγή δεδομένων DEI από αρχεία PDF",
                "no_files_selected": "Δεν επιλέχθηκαν αρχεία",
                "processing_failed_api": "Η επεξεργασία απέτυχε",
                "download_failed": "Η λήψη απέτυχε",
                "drag_drop_zone": "Ζώνη μεταφοράς και απόθεσης",
                "file_validation": "Επικύρωση αρχείων",
                "file_size_format": "Μορφή μεγέθους αρχείου",
                "progress_tracking": "Παρακολούθηση προόδου",
                "error_handling": "Χειρισμός σφαλμάτων",
                "success_messages": "Μηνύματα επιτυχίας",
            },
        }

    def get_text(self, key: str, language: str = "gr") -> str:
        """Get translated text for a given key and language.

        Args:
            key: Translation key
            language: Language code ('en' or 'gr')

        Returns:
            Translated text or the key if translation not found
        """
        if language not in self._translations:
            language = "gr"  # Default to Greek

        return self._translations.get(language, {}).get(key, key)

    def get_all_texts(self, language: str = "gr") -> Dict[str, str]:
        """Get all translations for a given language.

        Args:
            language: Language code ('en' or 'gr')

        Returns:
            Dictionary of all translations for the language
        """
        if language not in self._translations:
            language = "gr"  # Default to Greek

        return self._translations.get(language, {})

    def format_text(self, key: str, language: str = "gr", **kwargs) -> str:
        """Get translated text and format it with provided parameters.

        Args:
            key: Translation key
            language: Language code ('en' or 'gr')
            **kwargs: Parameters to format into the text

        Returns:
            Formatted translated text
        """
        text = self.get_text(key, language)
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
