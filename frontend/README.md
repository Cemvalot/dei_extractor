# DEI Extractor Frontend

A modern, production-quality Next.js frontend for the DEI Extractor application. This frontend provides an intuitive interface for uploading PDF and ZIP files, processing them through the backend API, and downloading the extracted results.

## Features

- 🌍 **Bilingual Support**: Greek (default) and English with persistent language selection
- 📁 **Drag & Drop Upload**: Support for PDF and ZIP files with validation
- ⚙️ **Configurable Options**: Ekatharistikos filtering and verbose logging
- 📊 **Real-time Progress**: Server-Sent Events for live processing updates
- 📱 **Responsive Design**: Works seamlessly on desktop and mobile
- 🎨 **Modern UI**: Built with Tailwind CSS and shadcn/ui components
- 💾 **Local History**: Stores last 5 processing runs for quick re-download
- ♿ **Accessible**: Full keyboard navigation and screen reader support

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for UI components
- **Zustand** for state management
- **react-dropzone** for file uploads
- **lucide-react** for icons

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running (FastAPI)

### Installation

1. **Clone and navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   ```bash
   # For development
   export BACKEND_URL=http://localhost:8000
   export NEXT_PUBLIC_API_BASE_URL=$BACKEND_URL

   # Or create a .env.local file:
   echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Production Deployment

1. **Build the application:**
   ```bash
   npm run build
   ```

2. **Start the production server:**
   ```bash
   npm start
   ```

3. **Set production environment variable:**
   ```bash
   export NEXT_PUBLIC_API_BASE_URL=https://your-api-domain.com
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | `http://localhost:8000` | Yes |

## API Integration

The frontend communicates with the FastAPI backend through these endpoints:

- `POST /api/jobs/` - Upload files and start processing
- `POST /api/jobs/progress` - Server-Sent Events for progress updates
- `GET /api/jobs/download/{run_id}` - Download processed results

## File Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles and Tailwind imports
│   ├── layout.tsx           # Root layout with metadata and fonts
│   └── page.tsx             # Main application page
├── components/
│   ├── ui/                  # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── progress.tsx
│   │   ├── alert.tsx
│   │   ├── toast.tsx
│   │   ├── switch.tsx
│   │   └── select.tsx
│   ├── UploadZone.tsx       # File upload component
│   ├── OptionsForm.tsx      # Processing options form
│   ├── ProcessPanel.tsx     # Processing controls and progress
│   └── HistoryList.tsx      # Processing history
├── lib/
│   ├── api.ts              # API client functions
│   ├── i18n.ts             # Internationalization
│   ├── types.ts            # TypeScript type definitions
│   └── utils.ts            # Utility functions
├── store/
│   └── useExtractorStore.ts # Zustand state management
└── package.json
```

## Usage

### Basic Workflow

1. **Upload Files**: Drag and drop or select PDF/ZIP files
2. **Configure Options**: Set filtering and language preferences
3. **Process**: Click "Process Files" to start extraction
4. **Monitor Progress**: Watch real-time progress updates
5. **Download Results**: Get the processed ZIP file when complete

### File Limits

- **Maximum files**: 100 files per upload
- **Maximum file size**: 200MB per file
- **Maximum total size**: 200MB per upload
- **Supported formats**: PDF and ZIP files

### Language Support

- **Greek (Ελληνικά)**: Default language
- **English**: Full translation available
- Language preference is saved in localStorage

## Development

### Adding New Languages

1. **Update the translations object in `lib/i18n.ts`:**
   ```typescript
   export const translations = {
     gr: { /* Greek translations */ },
     en: { /* English translations */ },
     // Add new language
     fr: { /* French translations */ }
   } as const;
   ```

2. **Update the Language type in `lib/types.ts`:**
   ```typescript
   export type Language = 'gr' | 'en' | 'fr';
   ```

3. **Add language option to the select component in `OptionsForm.tsx`**

### Customizing Styles

The application uses Tailwind CSS with a custom design system. Key customization points:

- **Colors**: Defined in `tailwind.config.js` and `app/globals.css`
- **Components**: shadcn/ui components in `components/ui/`
- **Layout**: Responsive design with max-width containers

### State Management

The application uses Zustand for state management with persistence:

- **Files**: Uploaded file list
- **Options**: Processing configuration
- **Run State**: Current processing status and progress
- **History**: Last 5 processing runs

## Testing

### Unit Tests

```bash
npm test
```

### End-to-End Tests

```bash
npm run test:e2e
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

1. Check the [Issues](../../issues) page
2. Review the backend API documentation
3. Ensure your environment variables are correctly set

## Changelog

### v1.0.0
- Initial release
- Greek and English language support
- File upload with drag & drop
- Real-time progress tracking
- Processing history
- Responsive design
