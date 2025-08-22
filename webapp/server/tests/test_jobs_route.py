"""Tests for the FastAPI jobs route."""

# Add the parent directory to the path
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from webapp.server.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "ocr_available" in data


def test_process_files_no_files():
    """Test processing with no files uploaded."""
    response = client.post("/api/jobs/")
    assert response.status_code == 400
    assert "No files uploaded" in response.json()["detail"]


def test_process_files_invalid_file_type():
    """Test processing with invalid file type."""
    # Create a dummy text file
    files = [("files", ("test.txt", b"dummy content", "text/plain"))]
    data = {"apply_filter": "false", "verbose": "false", "language": "en"}

    response = client.post("/api/jobs/", files=files, data=data)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


@patch("webapp.server.routers.jobs.StorageService")
@patch("webapp.server.routers.jobs.ExtractorService")
@patch("webapp.server.routers.jobs.ZippingService")
def test_process_files_success(mock_zipping, mock_extractor, mock_storage):
    """Test successful file processing."""
    # Mock the services
    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance

    mock_extractor_instance = MagicMock()
    mock_extractor.return_value = mock_extractor_instance

    mock_zipping_instance = MagicMock()
    mock_zipping.return_value = mock_zipping_instance

    # Mock the run directory
    mock_run_dir = MagicMock()
    mock_input_dir = MagicMock()
    mock_output_dir = MagicMock()
    mock_run_dir.__truediv__.side_effect = (
        lambda x: mock_input_dir if x == "input" else mock_output_dir
    )
    mock_storage_instance.create_run_directory.return_value = mock_run_dir

    # Mock file validation
    mock_extractor_instance.validate_input_directory.return_value = (True, "Valid")

    # Mock extractor run
    mock_extractor_instance.run_extractor.return_value = (True, "Success", [])

    # Mock output files
    mock_storage_instance.get_output_files.return_value = []

    # Create a dummy PDF file
    files = [("files", ("test.pdf", b"%PDF-1.4 dummy content", "application/pdf"))]
    data = {"apply_filter": "false", "verbose": "false", "language": "en"}

    response = client.post("/api/jobs/", files=files, data=data)

    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "Processing completed successfully" in data["message"]


@patch("webapp.server.routers.jobs.StorageService")
@patch("webapp.server.routers.jobs.ExtractorService")
@patch("webapp.server.routers.jobs.ZippingService")
def test_process_and_download_success(mock_zipping, mock_extractor, mock_storage):
    """Test successful file processing with download."""
    # Mock the services
    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance

    mock_extractor_instance = MagicMock()
    mock_extractor.return_value = mock_extractor_instance

    mock_zipping_instance = MagicMock()
    mock_zipping.return_value = mock_zipping_instance

    # Mock the run directory
    mock_run_dir = MagicMock()
    mock_input_dir = MagicMock()
    mock_output_dir = MagicMock()
    mock_run_dir.__truediv__.side_effect = (
        lambda x: mock_input_dir if x == "input" else mock_output_dir
    )
    mock_storage_instance.create_run_directory.return_value = mock_run_dir

    # Mock file validation
    mock_extractor_instance.validate_input_directory.return_value = (True, "Valid")

    # Mock extractor run
    mock_extractor_instance.run_extractor.return_value = (True, "Success", [])

    # Mock ZIP creation
    mock_zipping_instance.create_zip_from_directory.return_value = b"dummy zip content"
    mock_zipping_instance.get_zip_filename.return_value = "test_results.zip"

    # Create a dummy PDF file
    files = [("files", ("test.pdf", b"%PDF-1.4 dummy content", "application/pdf"))]
    data = {"apply_filter": "false", "verbose": "false", "language": "en"}

    response = client.post("/api/jobs/download", files=files, data=data)

    # Verify the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "attachment" in response.headers["content-disposition"]


def test_download_results_not_found():
    """Test downloading results that don't exist."""
    response = client.get("/api/jobs/download/nonexistent")
    assert response.status_code == 404
    assert "Results not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
