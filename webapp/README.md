# DEI Extractor Web Application

A modern web interface for the DEI Extractor package, providing both Streamlit and FastAPI modes for processing Greek DEI electricity bill PDFs. **Now with full Greek language support!**

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- No local Python installation required (everything runs in containers)

### One-Command Setup
```bash
cd webapp
make quick-start
```

Then open http://localhost:8501 in your browser.

## 🌐 Two Interface Modes

### 1. Streamlit Mode (Default)
- **URL**: http://localhost:8501
- **Best for**: Non-technical users, quick setup
- **Features**:
  - Simple sidebar configuration
  - Real-time progress feedback
  - Data preview capabilities
  - Interactive file upload

### 2. FastAPI Mode
- **URL**: http://localhost:8000
- **Best for**: Technical users, API access
- **Features**:
  - RESTful API endpoints
  - Modern HTML/JS frontend
  - Drag-and-drop file upload
  - Programmatic access

## 🐳 Docker Deployment

### Quick Start
```bash
# Start in Streamlit mode (default)
make quick-start

# Or start in FastAPI mode
APP_MODE=fastapi make quick-start
```

### Manual Setup
```bash
# Build and start containers
make docker-build
make docker-up

# Stop containers
make docker-down
```

### Environment Configuration
Create a `.env` file in the `webapp` directory:
```bash
# App Mode: streamlit or fastapi
APP_MODE=streamlit

# Upload limits
UPLOAD_MAX_MB=200
MAX_FILES=500

# UI Language: en or gr
DEFAULT_LANGUAGE=gr

# Default options
DEFAULT_FILTER=false
DEFAULT_VERBOSE=false

# Server settings
STREAMLIT_PORT=8501
FASTAPI_PORT=8000
```

## 📁 Project Structure

```
webapp/
├── README.md                 # This file
├── Makefile                  # Development commands
├── requirements.txt          # Python dependencies
├── app_config.yaml          # Application configuration
├── docker-compose.yml       # Docker orchestration
├── Dockerfile               # Container definition
├── .env.example             # Environment template
├── streamlit_app.py         # Streamlit interface
└── server/                  # FastAPI backend
    ├── main.py              # FastAPI application
    ├── routers/             # API routes
    ├── services/            # Business logic
    ├── models/              # Data models
    ├── static/              # Frontend files
    └── tests/               # Test suite
```

## 🔧 Development

### Local Development (without Docker)

#### Prerequisites
```bash
# Activate the virtual environment (if using one)
source ../dei_env_new/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Starting the Backend (FastAPI)
```bash
# Option 1: Using Makefile (recommended)
make dev-fastapi

# Option 2: Direct command
cd .. && python -m uvicorn webapp.server.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:
- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Endpoints**: http://localhost:8000/api/jobs/

#### Starting the Frontend (Streamlit)
```bash
# Run Streamlit locally
make dev
```

The Streamlit interface will be available at http://localhost:8501

#### Starting the Next.js Frontend
```bash
# Navigate to the frontend directory
cd ../frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

The Next.js frontend will be available at http://localhost:3000

**Note**: The Next.js frontend is designed to work with the FastAPI backend. Make sure both are running:
1. Backend: `make dev-fastapi` (from webapp directory)
2. Frontend: `npm run dev` (from frontend directory)

#### Troubleshooting
- **Backend not starting**: Make sure you're in the correct directory and have activated the virtual environment
- **CORS errors**: The backend is configured to accept requests from `http://localhost:3000`
- **Port conflicts**: Backend uses port 8000, frontend uses port 3000
- **API not found**: Check that the backend is running and accessible at http://localhost:8000/docs

### Docker Development
```bash
# Build container
make docker-build

# Start development environment
make docker-up

# View logs
docker logs dei-extractor-webapp

# Stop environment
make docker-down
```

### Testing
```bash
# Run all tests
make test

# Run specific test
pytest server/tests/test_jobs_route.py -v
```

## 📊 Features

### File Upload
- ✅ **Multiple PDFs**: Upload several PDF files at once
- ✅ **ZIP Archives**: Upload a ZIP file containing PDFs
- ✅ **File Validation**: Only accepts `.pdf` and `.zip` files
- ✅ **Size Limits**: Configurable upload size (default: 200MB)
- ✅ **File Count**: Configurable max files (default: 500)

### Processing Options
- ✅ **Εκαθαριστικός Filter**: Keep only final settlement records
- ✅ **Verbose Logging**: Detailed processing information
- ✅ **Language Selection**: UI in Greek (default) or English
- ✅ **OCR Support**: Automatic text extraction from scanned PDFs

### Output & Results
- ✅ **CSV Files**: `ολα.csv` (all records)
- ✅ **Excel Files**: `ολα.xlsx` (all records)
- ✅ **Filtered Outputs**: `filtered.csv` and `filtered.xlsx`
- ✅ **Processing Logs**: `run_log.txt` with warnings and errors
- ✅ **ZIP Download**: All results packaged in a single ZIP file

### Security & Privacy
- ✅ **Temporary Processing**: No files persisted after job completion
- ✅ **Automatic Cleanup**: Temporary directories removed after processing
- ✅ **File Type Validation**: Only accepts PDF and ZIP files
- ✅ **Size Limits**: Prevents oversized uploads

## 🔍 API Reference (FastAPI Mode)

### Endpoints

#### `GET /healthz`
Health check endpoint.
```bash
curl http://localhost:8000/healthz
# Returns: {"status": "ok"}
```

#### `POST /api/jobs/`
Process uploaded files and return job status.
```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "filter=true" \
  -F "verbose=true" \
  -F "lang=en"
```

#### `POST /api/jobs/download`
Process files and return ZIP download.
```bash
curl -X POST http://localhost:8000/api/jobs/download \
  -F "files=@document.pdf" \
  -F "filter=false" \
  -o results.zip
```

### Request Parameters
- `files`: PDF or ZIP files (multipart form data)
- `filter`: Boolean, apply Εκαθαριστικός filtering
- `verbose`: Boolean, enable verbose logging
- `lang`: String, UI language ("en" or "gr")

## 🚨 Troubleshooting

### Common Issues

#### 1. Docker Build Failures
```bash
# Clear Docker cache
docker system prune -a

# Rebuild with no cache
make docker-build
```

#### 2. OCR Not Working
```bash
# Check if Tesseract is installed in container
docker exec dei-extractor-webapp tesseract --version

# Verify Greek language pack
docker exec dei-extractor-webapp tesseract --list-langs
```

#### 3. Large File Uploads Failing
```bash
# Increase upload limit in .env
UPLOAD_MAX_MB=500

# Restart containers
make docker-down
make docker-up
```

#### 4. Processing Timeouts
- Large PDFs may take longer to process
- Consider splitting large files
- Check available system resources

#### 5. Port Already in Use
```bash
# Check what's using the ports
lsof -i :8501
lsof -i :8000

# Kill processes or change ports in .env
STREAMLIT_PORT=8502
FASTAPI_PORT=8001
```

### Getting Help

#### Check Logs
```bash
# View container logs
docker logs dei-extractor-webapp

# Follow logs in real-time
docker logs -f dei-extractor-webapp
```

#### Test Connectivity
```bash
# Test Streamlit
curl http://localhost:8501

# Test FastAPI health
curl http://localhost:8000/healthz
```

#### Manual Testing
```bash
# Copy test PDF
cp server/tests/fixtures/sample.pdf .

# Upload via web interface and verify processing
```

## 🔧 Configuration

### Application Settings (`app_config.yaml`)
```yaml
app:
  default_mode: "streamlit"
  upload_max_mb: 200
  max_files: 500
  default_language: "en"
  default_filter: false
  default_verbose: false

security:
  allowed_extensions: [".pdf", ".zip"]
  temp_dir_cleanup_interval: 3600

ui_text:
  en:
    title: "DEI Extractor Web App"
    # ... more UI text
  gr:
    title: "DEI Extractor Web App"
    # ... Greek UI text
```

### Environment Variables (`.env`)
```bash
# App Mode
APP_MODE=streamlit

# Upload Limits
UPLOAD_MAX_MB=200
MAX_FILES=500

# UI Settings
DEFAULT_LANGUAGE=en
DEFAULT_FILTER=false
DEFAULT_VERBOSE=false

# Server Ports
STREAMLIT_PORT=8501
FASTAPI_PORT=8000
```

## 🧪 Testing

### Automated Tests
```bash
# Run all tests
make test

# Run with coverage
pytest server/tests/ --cov=server --cov-report=html

# Run specific test file
pytest server/tests/test_jobs_route.py -v
```

### Manual Testing
```bash
# Test file upload
curl -X POST http://localhost:8000/api/jobs/ \
  -F "files=@server/tests/fixtures/sample.pdf"

# Test health endpoint
curl http://localhost:8000/healthz

# Test web interface
open http://localhost:8501  # Streamlit
open http://localhost:8000  # FastAPI
```

## 📚 Documentation

- [Main Repository README](../README.md) - Overview of the entire project
- [Implementation Summary](IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [Docker Configuration](Dockerfile) - Container setup
- [API Documentation](server/) - FastAPI backend details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `make test`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Note**: This web application is designed for local use and development. For production deployment, consider additional security measures such as authentication, rate limiting, and HTTPS.
