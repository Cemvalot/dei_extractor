#!/usr/bin/env python3
"""
Comprehensive test suite for DEI Extractor functionality.

This module contains extensive tests for all major features of the DEI Extractor,
including PDF processing, data extraction, validation, and output generation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd

from dei_extractor.core.extractor import DEIExtractorEnhanced

# Sample PDF content for testing
SAMPLE_PDF_CONTENT = """
ΦΟΠ Τιμολόγιο
Ημέρα 100 90 10 5
0987654321 123456789 02/01/2024 01.02.2024-28.02.2024  John Doe  Athens
"""


class TestDEIExtractorComprehensive:
    """Comprehensive test suite for DEIExtractorEnhanced class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.extractor = DEIExtractorEnhanced()

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_extract_text_from_pdf_success(self) -> None:
        """Test successful PDF text extraction."""
        # Mock PDF content
        mock_content = "Sample PDF content"

        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [MagicMock(extract_text=lambda: mock_content)]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

            result = self.extractor.extract_text_from_pdf("test.pdf")
            assert result == mock_content

    def test_extract_text_from_pdf_empty(self) -> None:
        """Test PDF text extraction with empty content."""
        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [MagicMock(extract_text=lambda: "")]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

            result = self.extractor.extract_text_from_pdf("test.pdf")
            assert result == ""

    def test_extract_text_from_pdf_multiple_pages(self) -> None:
        """Test PDF text extraction with multiple pages."""
        page_contents = ["Page 1 content", "Page 2 content", "Page 3 content"]

        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [
                MagicMock(extract_text=lambda: content) for content in page_contents
            ]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

            result = self.extractor.extract_text_from_pdf("test.pdf")
            expected = "\n".join(page_contents)
            assert result == expected

    def test_extract_text_from_pdf_with_ocr(self) -> None:
        """Test PDF text extraction with OCR fallback."""
        # Mock OCR content
        ocr_content = "OCR extracted content"

        with patch("pdfplumber.open") as mock_pdfplumber:
            mock_pdf = MagicMock()
            mock_pdf.pages = [MagicMock(extract_text=lambda: "")]
            mock_pdfplumber.return_value.__enter__.return_value = mock_pdf

            with patch("pytesseract.image_to_string") as mock_ocr:
                mock_ocr.return_value = ocr_content

                result = self.extractor.extract_text_from_pdf("test.pdf")
                assert result == ocr_content

    def test_parse_dei_records_single(self) -> None:
        """Test parsing single DEI record."""
        sample_text = """
        ΦΟΠ Τιμολόγιο
        Ημέρα 100 90 10 5
        """

        records = self.extractor.parse_dei_records(sample_text)
        assert len(records) == 1

    def test_parse_dei_records_multiple(self) -> None:
        """Test parsing multiple DEI records."""
        sample_text = """
        ΦΟΠ Τιμολόγιο
        Ημέρα 100 90 10 5

        0987654321 123456789 02/01/2024 01.02.2024-28.02.2024  Jane Smith  Thessaloniki
        ΦΟΠ Τιμολόγιο
        Ημέρα 150 120 20 10
        """

        records = self.extractor.parse_dei_records(sample_text)
        assert len(records) == 2

    def test_parse_dei_records_invalid_format(self) -> None:
        """Test parsing DEI records with invalid format."""
        sample_text = "Invalid format text"

        records = self.extractor.parse_dei_records(sample_text)
        assert len(records) == 0

    def test_parse_dei_records_missing_row3(self) -> None:
        """Test parsing DEI records with missing ROW3 pattern."""
        sample_text = """
        ΦΟΠ Τιμολόγιο
        """

        records = self.extractor.parse_dei_records(sample_text)
        assert len(records) == 0  # Should not match without ROW3

    def test_validate_record_valid(self) -> None:
        """Test basic record validation."""
        valid_record = {
            "ΑρΠαροχής": "1234567890",
            "ΑρΛογαριασμού": "987654321",
            "ΗμΈκδοσης": "01/01/2024",
            "Όνομα": "John Doe",
            "Διεύθυνση": "Athens",
            "Κατανάλωση": 100,
        }

        is_valid = self.extractor.validate_record(valid_record)
        assert is_valid is True

    def test_validate_record_invalid_missing_fields(self) -> None:
        """Test record validation with missing required fields."""
        invalid_record = {
            "Όνομα": "John Doe",
            "Διεύθυνση": "Athens",
            # Missing required fields
        }

        is_valid = self.extractor.validate_record(invalid_record)
        assert is_valid is False

    def test_validate_record_invalid_data_types(self) -> None:
        """Test record validation with invalid data types."""
        invalid_record = {
            "ΑρΠαροχής": "1234567890",
            "ΑρΛογαριασμού": "987654321",
            "ΗμΈκδοσης": "01/01/2024",
            "Όνομα": "John Doe",
            "Διεύθυνση": "Athens",
            "Κατανάλωση": "invalid",  # Should be numeric
        }

        is_valid = self.extractor.validate_record(invalid_record)
        assert is_valid is False

    def test_process_pdf_file_success(self) -> None:
        """Test successful PDF file processing."""
        pdf_path = self.test_dir / "test.pdf"

        with patch.object(self.extractor, "extract_text_from_pdf") as mock_extract:
            mock_extract.return_value = SAMPLE_PDF_CONTENT

            with patch.object(self.extractor, "parse_dei_records") as mock_parse:
                mock_parse.return_value = [{"test": "data"}]

                result = self.extractor.process_pdf_file(str(pdf_path))
                assert result is True

    def test_process_pdf_file_failure(self) -> None:
        """Test PDF file processing failure."""
        pdf_path = self.test_dir / "nonexistent.pdf"

        result = self.extractor.process_pdf_file(str(pdf_path))
        assert result is False

    def test_save_results_csv(self) -> None:
        """Test saving results to CSV file."""
        records = [
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
        ]

        csv_path = self.test_dir / "results.csv"
        self.extractor.save_results_csv(records, str(csv_path))

        assert csv_path.exists()
        df = pd.read_csv(csv_path)
        assert len(df) == 2

    def test_save_results_excel(self) -> None:
        """Test saving results to Excel file."""
        records = [
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
        ]

        excel_path = self.test_dir / "results.xlsx"
        self.extractor.save_results_excel(records, str(excel_path))

        assert excel_path.exists()
        df = pd.read_excel(excel_path)
        assert len(df) == 2

    def test_extract_from_directory_success(self) -> None:
        """Test successful directory extraction."""
        # Create test PDF files
        pdf1 = self.test_dir / "test1.pdf"
        pdf2 = self.test_dir / "test2.pdf"

        with patch.object(self.extractor, "process_pdf_file") as mock_process:
            mock_process.return_value = True

            result = self.extractor.extract_from_directory(str(self.test_dir))
            assert result is True

    def test_extract_from_directory_failure(self) -> None:
        """Test directory extraction with processing failure."""
        # Create test PDF file
        pdf1 = self.test_dir / "test1.pdf"

        with patch.object(self.extractor, "process_pdf_file") as mock_process:
            mock_process.return_value = False

            result = self.extractor.extract_from_directory(str(self.test_dir))
            assert result is False

    def test_get_statistics(self) -> None:
        """Test getting processing statistics."""
        self.extractor.records = [{"test": "data1"}, {"test": "data2"}]
        self.extractor.needs_review = [{"test": "data3"}]
        self.extractor.warnings = ["Warning 1", "Warning 2"]

        stats = self.extractor.get_statistics()

        assert stats["total_records"] == 2
        assert stats["needs_review"] == 1
        assert stats["warnings"] == 2

    def test_clear_results(self) -> None:
        """Test clearing all results."""
        self.extractor.records = [{"test": "data1"}, {"test": "data2"}]
        self.extractor.needs_review = [{"test": "data"}]
        self.extractor.warnings = ["warning"]

        self.extractor.clear_results()

        assert len(self.extractor.records) == 0
        assert len(self.extractor.needs_review) == 0
        assert len(self.extractor.warnings) == 0

    def test_export_to_dataframe(self) -> None:
        """Test exporting results to DataFrame."""
        self.extractor.records = [
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
        ]

        df = self.extractor.export_to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_export_to_dataframe_empty(self) -> None:
        """Test exporting empty results to DataFrame."""
        self.extractor.records = []

        df = self.extractor.export_to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_validate_pdf_file_valid(self) -> None:
        """Test validating valid PDF file."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("pathlib.Path.is_file") as mock_is_file:
                mock_is_file.return_value = True

                with patch("builtins.open", mock_open(read_data=b"%PDF")):
                    result = self.extractor.validate_pdf_file("test.pdf")
                    assert result is True

    def test_validate_pdf_file_invalid(self) -> None:
        """Test validating invalid PDF file."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = self.extractor.validate_pdf_file("test.pdf")
            assert result is False

    def test_extract_additional_fields_success(self) -> None:
        """Test extracting additional fields successfully."""
        text = """
        ΚΑΤΑΣΤΗΜΑ ΕΞΥΠΗΡΕΤΗΣΗΣ: Athens Store
        ΠΑΡΑΣΤ: 12345
        """

        fields = self.extractor.extract_additional_fields(text)

        assert "ΚατάστημαΕξυπηρέτησης" in fields
        assert "Παραστατικό" in fields

    def test_extract_additional_fields_not_found(self) -> None:
        """Test extracting additional fields when not found."""
        text = "No additional fields here"

        fields = self.extractor.extract_additional_fields(text)

        assert "ΚατάστημαΕξυπηρέτησης" not in fields
        assert "Παραστατικό" not in fields

    def test_is_header_or_footer_header(self) -> None:
        """Test header/footer detection with header text."""
        header_text = "ΔΗΜΟΣΙΑ ΕΠΙΧΕΙΡΗΣΗ ΗΛΕΚΤΡΙΣΜΟΥ"

        result = self.extractor.is_header_or_footer(header_text)
        assert result is True

    def test_is_header_or_footer_regular(self) -> None:
        """Test header/footer detection with regular text."""
        regular_text = "This is regular invoice content"

        result = self.extractor.is_header_or_footer(regular_text)
        assert result is False

    def test_is_financial_line_financial(self) -> None:
        """Test financial line detection with financial text."""
        financial_text = "ΦΠΑ 24%"

        result = self.extractor.is_financial_line(financial_text)
        assert result is True

    def test_is_financial_line_regular(self) -> None:
        """Test financial line detection with regular text."""
        regular_text = "This is regular invoice content"

        result = self.extractor.is_financial_line(regular_text)
        assert result is False

    def test_parse_date_valid(self) -> None:
        """Test parsing valid date."""
        date_str = "01/01/2024"

        parsed_date = self.extractor.parse_date(date_str)
        assert parsed_date == "01/01/2024"

    def test_parse_date_invalid(self) -> None:
        """Test parsing invalid date."""
        date_str = "invalid-date"

        parsed_date = self.extractor.parse_date(date_str)
        assert parsed_date == "invalid-date"

    def test_parse_date_empty(self) -> None:
        """Test parsing empty date."""
        date_str = ""

        parsed_date = self.extractor.parse_date(date_str)
        assert parsed_date == ""

    def test_extract_numeric_value_valid(self) -> None:
        """Test extracting valid numeric value."""
        text = "Κατανάλωση: 100 kWh"

        value = self.extractor.extract_numeric_value(text)
        assert value == 100

    def test_extract_numeric_value_invalid(self) -> None:
        """Test extracting invalid numeric value."""
        text = "Κατανάλωση: invalid kWh"

        value = self.extractor.extract_numeric_value(text)
        assert value is None

    def test_extract_numeric_value_not_found(self) -> None:
        """Test extracting numeric value when not found."""
        text = "No numeric value here"

        value = self.extractor.extract_numeric_value(text)
        assert value is None

    def test_validate_afm_valid(self) -> None:
        """Test validating valid AFM."""
        valid_afm = "123456789"

        result = self.extractor.validate_afm(valid_afm)
        assert result is True

    def test_validate_afm_invalid(self) -> None:
        """Test validating invalid AFM."""
        invalid_afm = "12345"  # Too short

        result = self.extractor.validate_afm(invalid_afm)
        assert result is False

    def test_deduplicate_records_with_duplicates(self) -> None:
        """Test deduplicating records with duplicates."""
        records = [
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},  # Duplicate
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
        ]

        deduplicated = self.extractor.deduplicate_records(records)
        assert len(deduplicated) == 2

    def test_deduplicate_records_no_duplicates(self) -> None:
        """Test deduplicating records without duplicates."""
        records = [
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
        ]

        deduplicated = self.extractor.deduplicate_records(records)
        assert len(deduplicated) == 2

    def test_deduplicate_records_empty(self) -> None:
        """Test deduplicating empty records."""
        records = []

        deduplicated = self.extractor.deduplicate_records(records)
        assert len(deduplicated) == 0

    def test_sort_records_by_ar_parochis(self) -> None:
        """Test sorting records by ΑρΠαροχής."""
        records = [
            {"ΑρΠαροχής": "0987654321", "Όνομα": "Jane Smith"},
            {"ΑρΠαροχής": "1234567890", "Όνομα": "John Doe"},
        ]

        sorted_records = self.extractor.sort_records(records)
        assert sorted_records[0]["ΑρΠαροχής"] == "1234567890"

    def test_sort_records_missing_key(self) -> None:
        """Test sorting records with missing sort key."""
        records = [
            {"Όνομα": "Jane Smith"},
            {"Όνομα": "John Doe"},
        ]

        sorted_records = self.extractor.sort_records(records)
        assert len(sorted_records) == 2

    def test_sort_records_empty(self) -> None:
        """Test sorting empty records."""
        records = []

        sorted_records = self.extractor.sort_records(records)
        assert len(sorted_records) == 0

    def test_apply_filters_ekatharistikos_only(self) -> None:
        """Test applying filters with ekatharistikos only."""
        records = [
            {"Εκαθαριστικός": "True", "Κατανάλωση": 100},
            {"Εκαθαριστικός": "True", "Κατανάλωση": 300},
            {"Εκαθαριστικός": "False", "Κατανάλωση": 200},
        ]

        filtered = self.extractor.apply_filters(records, ekatharistikos_only=True)
        assert len(filtered) == 2

    def test_apply_filters_all_records(self) -> None:
        """Test applying filters to include all records."""
        records = [
            {"Εκαθαριστικός": "True", "Κατανάλωση": 100},
            {"Εκαθαριστικός": "False", "Κατανάλωση": 200},
        ]

        filtered = self.extractor.apply_filters(records, ekatharistikos_only=False)
        assert len(filtered) == 2

    def test_apply_filters_empty(self) -> None:
        """Test applying filters to empty records."""
        records = []

        filtered = self.extractor.apply_filters(records, ekatharistikos_only=True)
        assert len(filtered) == 0

    def test_generate_report_with_data(self) -> None:
        """Test generating report with data."""
        self.extractor.records = [{"test": "data1"}, {"test": "data2"}]
        self.extractor.needs_review = [{"test": "data3"}]
        self.extractor.warnings = ["Warning 1"]

        report = self.extractor.generate_report()

        assert "total_records" in report
        assert "needs_review" in report
        assert "warnings" in report

    def test_generate_report_empty(self) -> None:
        """Test generating report with empty data."""
        report = self.extractor.generate_report()

        assert "total_records" in report
        assert report["total_records"] == 0

    def test_export_report_to_file(self) -> None:
        """Test exporting report to file."""
        report = {"total_records": 2, "needs_review": 1, "warnings": 1}
        report_path = self.test_dir / "report.json"

        self.extractor.export_report_to_file(report, str(report_path))

        assert report_path.exists()

    def test_validate_config_valid(self) -> None:
        """Test validating valid configuration."""
        config = {
            "log_level": "INFO",
            "output_dir": str(self.test_dir),
            "confidence_threshold": 0.9,
        }

        result = self.extractor.validate_config(config)
        assert result is True

    def test_validate_config_invalid_missing_keys(self) -> None:
        """Test validating configuration with missing keys."""
        config = {
            "log_level": "INFO",
            # Missing output_dir
        }

        result = self.extractor.validate_config(config)
        assert result is False

    def test_validate_config_invalid_values(self) -> None:
        """Test validating configuration with invalid values."""
        config = {
            # Missing output_dir
        }

        result = self.extractor.validate_config(config)
        assert result is False

    def test_get_processing_stats(self) -> None:
        """Test getting processing statistics."""
        self.extractor.records = [{"test": "data1"}, {"test": "data2"}]
        self.extractor.needs_review = [{"test": "data3"}]
        self.extractor.warnings = ["Warning 1", "Warning 2"]

        stats = self.extractor.get_processing_stats()

        assert "total_processed" in stats
        assert "successful_extractions" in stats
        assert "failed_extractions" in stats

    def test_reset_processing_stats(self) -> None:
        """Test resetting processing statistics."""
        self.extractor.records = [{"test": "data1"}, {"test": "data2"}]
        self.extractor.needs_review = [{"test": "data"}]
        self.extractor.warnings = ["warning"]

        self.extractor.reset_processing_stats()

        assert len(self.extractor.records) == 0
        assert len(self.extractor.needs_review) == 0
        assert len(self.extractor.warnings) == 0

    def test_validate_file_path_valid(self) -> None:
        """Test validating valid file path."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("pathlib.Path.is_file") as mock_is_file:
                mock_is_file.return_value = True

                result = self.extractor.validate_file_path("test.pdf")
                assert result is True

    def test_validate_file_path_invalid(self) -> None:
        """Test validating invalid file path."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = self.extractor.validate_file_path("test.pdf")
            assert result is False

    def test_validate_directory_path_valid(self) -> None:
        """Test validating valid directory path."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            with patch("pathlib.Path.is_dir") as mock_is_dir:
                mock_is_dir.return_value = True

                result = self.extractor.validate_directory_path("test_dir")
                assert result is True

    def test_validate_directory_path_invalid(self) -> None:
        """Test validating invalid directory path."""
        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            result = self.extractor.validate_directory_path("test_dir")
            assert result is False

    def test_clean_filename_valid(self) -> None:
        """Test cleaning valid filename."""
        filename = "test_file.pdf"

        cleaned = self.extractor.clean_filename(filename)
        assert cleaned == "test_file.pdf"

    def test_clean_filename_with_spaces(self) -> None:
        """Test cleaning filename with spaces."""
        filename = "test file with spaces.pdf"

        cleaned = self.extractor.clean_filename(filename)
        assert cleaned == "test_file_with_spaces.pdf"

    def test_clean_filename_with_special_chars(self) -> None:
        """Test cleaning filename with special characters."""
        filename = "test@file#with$special%chars.pdf"

        cleaned = self.extractor.clean_filename(filename)
        assert cleaned == "test_file_with_special_chars.pdf"

    def test_validate_email_valid(self) -> None:
        """Test validating valid email."""
        email = "test@example.com"

        result = self.extractor.validate_email(email)
        assert result is True

    def test_validate_email_invalid(self) -> None:
        """Test validating invalid email."""
        email = "invalid-email"

        result = self.extractor.validate_email(email)
        assert result is False

    def test_validate_phone_valid(self) -> None:
        """Test validating valid phone number."""
        phone = "+30 210 1234567"

        result = self.extractor.validate_phone(phone)
        assert result is True

    def test_validate_phone_invalid(self) -> None:
        """Test validating invalid phone number."""
        phone = "invalid-phone"

        result = self.extractor.validate_phone(phone)
        assert result is False

    def test_extract_contact_info_success(self) -> None:
        """Test extracting contact information successfully."""
        text = """
        Email: test@example.com
        Phone: +30 210 1234567
        """

        contact_info = self.extractor.extract_contact_info(text)

        assert "email" in contact_info
        assert "phone" in contact_info

    def test_extract_contact_info_not_found(self) -> None:
        """Test extracting contact information when not found."""
        text = "No contact information here"

        contact_info = self.extractor.extract_contact_info(text)

        assert "email" not in contact_info
        assert "phone" not in contact_info

    def test_validate_postal_code_valid(self) -> None:
        """Test validating valid postal code."""
        postal_code = "12345"

        result = self.extractor.validate_postal_code(postal_code)
        assert result is True

    def test_validate_postal_code_invalid(self) -> None:
        """Test validating invalid postal code."""
        postal_code = "123"  # Too short

        result = self.extractor.validate_postal_code(postal_code)
        assert result is False

    def test_extract_address_components_success(self) -> None:
        """Test extracting address components."""
        address = "123 Main St, Athens, 12345, Greece"

        components = self.extractor.extract_address_components(address)

        assert "street" in components
        assert "city" in components
        assert "postal_code" in components
        assert "country" in components

    def test_extract_address_components_incomplete(self) -> None:
        """Test extracting incomplete address components."""
        address = "123 Main St, Athens"

        components = self.extractor.extract_address_components(address)

        assert "street" in components
        assert "city" in components

    def test_validate_consumption_valid(self) -> None:
        """Test validating valid consumption value."""
        consumption = 100

        result = self.extractor.validate_consumption(consumption)
        assert result is True

    def test_validate_consumption_invalid(self) -> None:
        """Test validating invalid consumption value."""
        consumption = -10  # Negative value

        result = self.extractor.validate_consumption(consumption)
        assert result is False

    def test_validate_amount_valid(self) -> None:
        """Test validating valid amount."""
        amount = 100.50

        result = self.extractor.validate_amount(amount)
        assert result is True

    def test_validate_amount_invalid(self) -> None:
        """Test validating invalid amount."""
        amount = -50.25  # Negative amount

        result = self.extractor.validate_amount(amount)
        assert result is False

    def test_extract_financial_data_success(self) -> None:
        """Test extracting financial data successfully."""
        text = """
        Κατανάλωση: 100 kWh
        Ποσό: 150.50 €
        ΦΠΑ: 24%
        """

        financial_data = self.extractor.extract_financial_data(text)

        assert "consumption" in financial_data
        assert "amount" in financial_data
        assert "vat_rate" in financial_data

    def test_extract_financial_data_not_found(self) -> None:
        """Test extracting financial data when not found."""
        text = "No financial data here"

        financial_data = self.extractor.extract_financial_data(text)

        assert "consumption" not in financial_data
        assert "amount" not in financial_data

    def test_validate_invoice_number_valid(self) -> None:
        """Test validating valid invoice number."""
        invoice_number = "INV-2024-001"

        result = self.extractor.validate_invoice_number(invoice_number)
        assert result is True

    def test_validate_invoice_number_invalid(self) -> None:
        """Test validating invalid invoice number."""
        invoice_number = ""  # Empty

        result = self.extractor.validate_invoice_number(invoice_number)
        assert result is False

    def test_extract_invoice_metadata_success(self) -> None:
        """Test extracting invoice metadata successfully."""
        text = """
        Invoice Number: INV-2024-001
        Issue Date: 01/01/2024
        Due Date: 31/01/2024
        """

        metadata = self.extractor.extract_invoice_metadata(text)

        assert "invoice_number" in metadata
        assert "issue_date" in metadata
        assert "due_date" in metadata

    def test_extract_invoice_metadata_not_found(self) -> None:
        """Test extracting invoice metadata when not found."""
        text = "No metadata here"

        metadata = self.extractor.extract_invoice_metadata(text)

        assert "invoice_number" not in metadata
        assert "issue_date" not in metadata

    def test_validate_period_valid(self) -> None:
        """Test validating valid period."""
        period = "01.01.2024-31.01.2024"

        result = self.extractor.validate_period(period)
        assert result is True

    def test_validate_period_invalid(self) -> None:
        """Test validating invalid period."""
        period = "invalid-period"

        result = self.extractor.validate_period(period)
        assert result is False

    def test_extract_period_components_success(self) -> None:
        """Test extracting period components."""
        period = "01.01.2024-31.01.2024"

        components = self.extractor.extract_period_components(period)

        assert "start_date" in components
        assert "end_date" in components

    def test_extract_period_components_invalid(self) -> None:
        """Test extracting period components from invalid period."""
        period = "invalid-period"

        components = self.extractor.extract_period_components(period)

        assert "start_date" not in components
        assert "end_date" not in components
