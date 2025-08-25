"""Streamlit application for DEI Extractor web app."""

import io
import logging
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

import pandas as pd
import streamlit as st

# Add the parent directory to the path to import dei_extractor
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.services.extractor_service import ExtractorService
from server.services.storage import StorageService
from server.services.zipping import ZippingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="DEI Extractor Web App",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    .upload-section {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #dee2e6;
        text-align: center;
        margin-bottom: 2rem;
    }
    .options-section {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin-bottom: 2rem;
    }
    .results-section {
        background-color: #d4edda;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #c3e6cb;
        margin-bottom: 2rem;
    }
    .error-section {
        background-color: #f8d7da;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #f5c6cb;
        margin-bottom: 2rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize services
@st.cache_resource
def get_services():
    """Initialize and cache services."""
    return {
        "storage": StorageService(),
        "extractor": ExtractorService(),
        "zipping": ZippingService(),
    }


def validate_files(uploaded_files: List) -> tuple[bool, str, List]:
    """Validate uploaded files."""
    if not uploaded_files:
        return False, "No files uploaded", []

    valid_files = []
    total_size = 0
    max_size_mb = 200  # TODO: Make configurable

    for file in uploaded_files:
        # Check file type
        if not file.name.lower().endswith((".pdf", ".zip")):
            continue

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        total_size += file_size
        valid_files.append(file)

    if not valid_files:
        return False, "No valid files found. Please upload PDF or ZIP files.", []

    if total_size > max_size_mb * 1024 * 1024:
        return (
            False,
            f"Total file size ({total_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)",
            [],
        )

    return True, f"Found {len(valid_files)} valid files", valid_files


def process_files(
    files: List, apply_filter: bool, verbose: bool, progress_bar, status_text
) -> tuple[bool, str, bytes, List]:
    """Process uploaded files and return results."""
    services = get_services()
    storage_service = services["storage"]
    extractor_service = services["extractor"]
    zipping_service = services["zipping"]

    # Create run directory
    run_dir = storage_service.create_run_directory()

    try:
        # Progress: 0-20% - File preparation
        progress_bar.progress(0)
        status_text.text("Preparing files...")

        pdf_files = []
        for i, file in enumerate(files):
            content = file.read()
            file_path = storage_service.save_uploaded_file(content, file.name, run_dir)

            # If it's a ZIP file, extract PDFs
            if file_path.suffix.lower() == ".zip":
                extracted_pdfs = storage_service.extract_zip_file(file_path, run_dir)
                pdf_files.extend(extracted_pdfs)
            else:
                pdf_files.append(file_path)

            # Update progress for file preparation
            progress = int(20 * (i + 1) / len(files))
            progress_bar.progress(progress / 100)
            status_text.text(f"Prepared {i+1}/{len(files)} files")

        # Progress: 20-30% - Validation
        progress_bar.progress(0.2)
        status_text.text("Validating input...")

        input_dir = run_dir / "input"
        is_valid, validation_msg = extractor_service.validate_input_directory(input_dir)

        if not is_valid:
            progress_bar.progress(1.0)
            status_text.text("Validation failed")
            return False, validation_msg, b"", []

        progress_bar.progress(0.3)
        status_text.text("Validation complete")

        # Progress: 30-90% - Processing
        def progress_callback(percentage: int, message: str):
            # Scale the percentage from 30-90 range
            scaled_percentage = 0.3 + (percentage / 100) * 0.6
            progress_bar.progress(scaled_percentage)
            status_text.text(message)

        output_dir = run_dir / "output"
        success, log_output, warnings = extractor_service.run_extractor(
            input_dir=input_dir,
            output_dir=output_dir,
            apply_filter=apply_filter,
            verbose=verbose,
            progress_callback=progress_callback,
        )

        if not success:
            progress_bar.progress(1.0)
            status_text.text("Processing failed")
            return False, "Processing failed", b"", warnings

        # Progress: 90-95% - Creating outputs
        progress_bar.progress(0.9)
        status_text.text("Creating output files...")

        log_content = (
            f"Processing completed\n\nLog output:\n{log_output}\n\nWarnings:\n"
            + "\n".join(warnings)
        )
        storage_service.create_run_log(run_dir, log_content)

        # Progress: 95-100% - Creating ZIP
        progress_bar.progress(0.95)
        status_text.text("Creating ZIP file...")

        zip_content = zipping_service.create_zip_from_directory(
            run_dir, include_log=True
        )

        progress_bar.progress(1.0)
        status_text.text("Processing completed successfully!")

        return True, "Processing completed successfully", zip_content, warnings

    except Exception as e:
        logger.error(f"Error processing files: {e}")
        progress_bar.progress(1.0)
        status_text.text("Error during processing")
        return False, f"Error during processing: {str(e)}", b"", [str(e)]
    finally:
        # Clean up run directory
        storage_service.cleanup_run_directory(run_dir)


def main():
    """Main Streamlit application."""

    # Header
    st.markdown(
        '<h1 class="main-header">DEI Extractor Web App</h1>', unsafe_allow_html=True
    )
    st.markdown(
        '<p style="text-align: center; color: #7f8c8d;">Upload PDF files or ZIP archives to extract DEI data</p>',
        unsafe_allow_html=True,
    )

    # Sidebar options
    st.sidebar.title("Processing Options")

    apply_filter = st.sidebar.checkbox(
        "Keep only Εκαθαριστικός",
        value=False,
        help="Apply filtering to keep only Εκαθαριστικός records",
    )

    verbose = st.sidebar.checkbox(
        "Verbose logs", value=False, help="Enable verbose logging during processing"
    )

    language = st.sidebar.selectbox(
        "Language",
        options=["en", "gr"],
        index=0,
        help="UI language (extraction remains Greek-capable)",
    )

    # File upload section
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📁 Upload Files")

    uploaded_files = st.file_uploader(
        "Choose PDF files or ZIP archives",
        type=["pdf", "zip"],
        accept_multiple_files=True,
        help="Upload multiple PDF files or a single ZIP archive containing PDFs",
    )

    if uploaded_files:
        st.write(f"**Uploaded {len(uploaded_files)} files:**")
        for file in uploaded_files:
            st.write(f"• {file.name} ({file.size / 1024:.1f} KB)")

    st.markdown("</div>", unsafe_allow_html=True)

    # Process button
    if uploaded_files:
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            # Validate files
            is_valid, validation_msg, valid_files = validate_files(uploaded_files)

            if not is_valid:
                st.error(validation_msg)
                return

            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Process files with progress tracking
            success, message, zip_content, warnings = process_files(
                valid_files, apply_filter, verbose, progress_bar, status_text
            )

            # Show results
            if success:
                st.markdown('<div class="results-section">', unsafe_allow_html=True)
                st.success("✅ " + message)

                if warnings:
                    st.warning("⚠️ Warnings during processing:")
                    for warning in warnings:
                        st.write(f"• {warning}")

                # Show output preview if available
                try:
                    # Try to read CSV files from the ZIP for preview
                    with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_file:
                        csv_files = [
                            f for f in zip_file.namelist() if f.endswith(".csv")
                        ]

                        if csv_files:
                            st.subheader("📊 Output Preview")

                            # Read the first CSV file for preview
                            with zip_file.open(csv_files[0]) as csv_file:
                                df = pd.read_csv(csv_file)
                                st.dataframe(df.head(), use_container_width=True)
                                st.write(f"**Total rows:** {len(df)}")
                except Exception as e:
                    st.info("Output preview not available")

                # Download button
                st.download_button(
                    label="📥 Download Results (ZIP)",
                    data=zip_content,
                    file_name="dei_extractor_results.zip",
                    mime="application/zip",
                    use_container_width=True,
                )

                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-section">', unsafe_allow_html=True)
                st.error("❌ " + message)
                st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #7f8c8d; font-size: 0.9rem;">
            <p>DEI Extractor Web App | Built with Streamlit</p>
            <p>Files are processed temporarily and not stored on the server</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
