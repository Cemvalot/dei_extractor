# DEI Extractor - Production Deployment Guide

This guide covers deploying the DEI Extractor application using Docker Compose with three services: backend (FastAPI), frontend (Next.js), and proxy (Caddy).

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- A hostname that resolves to your server
- Basic understanding of Docker and networking

### 1. Generate Basic Auth Password Hash

First, generate a password hash for Caddy's basic authentication:

```bash
docker run --rm caddy:2 caddy hash-password --plaintext 'YourStrongPassword'
```

Copy the output hash (it will look like `$2a$14$...`).

### 2. Configure Caddy

Edit `ops/Caddyfile` and replace the placeholders:

```bash
cd ops
sed -i 's/YOUR_HOSTNAME_HERE/your-hostname.example.com/' Caddyfile
sed -i 's/<HASHED_PASSWORD>/$2a$14$your_actual_hash_here/' Caddyfile
```

### 3. Build and Deploy

```bash
cd ops
docker compose build
docker compose up -d
```

### 4. Access the Application

- Visit `https://your-hostname.example.com`
- Login with username `admin` and your chosen password
- Upload PDF files or ZIP archives for processing

## Architecture

The deployment consists of three services:

### Backend (FastAPI + Tesseract OCR)
- **Port**: 8000 (internal)
- **Features**:
  - PDF processing with OCR support
  - Greek language OCR (tesseract-ocr-ell)
  - Server-side upload validation
  - Safe ZIP extraction (prevents zip-slip attacks)
  - Automatic cleanup of temporary files

### Frontend (Next.js)
- **Port**: 3000 (internal)
- **Features**:
  - Modern React UI with TypeScript
  - File upload with drag & drop
  - Real-time progress updates
  - Multi-language support (English/Greek)

### Proxy (Caddy)
- **Port**: 443 (external HTTPS)
- **Features**:
  - HTTPS termination with internal certificates
  - Basic authentication
  - Security headers
  - Upload size limits (100MB)
  - Routes `/api/*` to backend, everything else to frontend

## Configuration

### Environment Variables

The following environment variables can be configured:

| Variable | Default | Description |
|----------|---------|-------------|
| `RETENTION_HOURS` | 24 | Hours to keep temporary run directories |
| `MAX_FILES` | 50 | Maximum number of files per upload |
| `MAX_UPLOAD_MB` | 100 | Maximum total upload size in MB |
| `LOG_LEVEL` | INFO | Logging level |

### Security Features

- **Upload Validation**: Server-side checks for file count, size, and allowed extensions
- **Safe ZIP Extraction**: Prevents zip-slip attacks with path validation
- **Automatic Cleanup**: Background thread removes old temporary directories
- **Security Headers**: Caddy provides comprehensive security headers
- **Basic Authentication**: Protects the entire application

## Monitoring and Troubleshooting

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f proxy
docker compose logs -f frontend
docker compose logs -f backend
```

### Health Checks

- Backend health: `https://your-hostname.example.com/api/healthz`
- Frontend: Access the main page

### Common Issues

1. **Certificate Issues**: Caddy uses internal certificates. For production, consider using Let's Encrypt or your own certificates.

2. **Upload Failures**: Check the upload limits and file types. Only PDF and ZIP files are allowed.

3. **Memory Issues**: The backend processes large PDFs. Ensure sufficient memory allocation.

4. **Storage Issues**: Temporary files are cleaned up automatically, but monitor disk space.

## Smoke Tests

After deployment, verify the following:

1. **Basic Access**: Visit `https://your-hostname.example.com` → basic auth → UI loads
2. **File Upload**: Upload a small PDF → process → download results
3. **ZIP Processing**: Upload a small ZIP of PDFs → process → download results
4. **Error Handling**: Try uploading invalid files → proper error messages

## Production Considerations

### Security
- Change the default password
- Consider using external certificates
- Review and adjust security headers as needed
- Monitor access logs

### Performance
- Adjust upload limits based on your needs
- Monitor memory usage during large file processing
- Consider scaling backend services if needed

### Backup
- The application is stateless (no persistent data)
- Temporary files are automatically cleaned up
- Consider backing up any custom configurations

## Maintenance

### Updates
```bash
cd ops
docker compose pull
docker compose build
docker compose up -d
```

### Cleanup
```bash
# Remove old images and containers
docker system prune -a

# View disk usage
docker system df
```

## Support

For issues or questions:
1. Check the logs first
2. Verify all prerequisites are met
3. Test with small files first
4. Review the configuration settings
