'use client';

import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, File, FileText, Archive } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useExtractorStore } from '@/store/useExtractorStore';
import { getTranslation, getCurrentLanguage } from '@/lib/i18n';
import { formatFileSize, MAX_FILES, MAX_FILE_SIZE, MAX_TOTAL_SIZE, ALLOWED_TYPES } from '@/lib/api';

export function UploadZone() {
  const { files, addFiles, removeFile, clearFiles } = useExtractorStore();
  const language = getCurrentLanguage();

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const errors = rejectedFiles.map(({ file, errors }) => ({
        file: file.name,
        errors: errors.map((e: any) => e.message)
      }));
      console.error('File rejection errors:', errors);
      // You could show toast notifications here
    }

    // Add accepted files
    if (acceptedFiles.length > 0) {
      addFiles(acceptedFiles);
    }
  }, [addFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/zip': ['.zip']
    },
    maxFiles: MAX_FILES,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  const isOverSizeLimit = totalSize > MAX_TOTAL_SIZE;

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <FileText className="h-4 w-4 text-red-500" />;
    } else if (file.type === 'application/zip') {
      return <Archive className="h-4 w-4 text-blue-500" />;
    }
    return <File className="h-4 w-4 text-gray-500" />;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{getTranslation('uploadTitle', language)}</CardTitle>
        <CardDescription>
          {getTranslation('uploadSubtitle', language)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/25 hover:border-primary/50'
            }
            ${isOverSizeLimit ? 'border-destructive bg-destructive/5' : ''}
          `}
        >
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
          <p className="text-lg font-medium mb-2">
            {isDragActive
              ? getTranslation('uploadSubtitle', language)
              : getTranslation('uploadButton', language)
            }
          </p>
          <p className="text-sm text-muted-foreground">
            {getTranslation('uploadAccepted', language)} • {getTranslation('uploadMaxSize', language)} • {getTranslation('uploadMaxFiles', language)}
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                {files.length} {getTranslation('filesSelected', language)}
              </h4>
              <Button
                variant="outline"
                size="sm"
                onClick={clearFiles}
                className="text-destructive hover:text-destructive"
              >
                {getTranslation('clearAll', language)}
              </Button>
            </div>

            {isOverSizeLimit && (
              <div className="p-3 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-sm text-destructive font-medium">
                  {getTranslation('errorTotalSize', language)}
                </p>
                <p className="text-xs text-destructive/80 mt-1">
                  {getTranslation('totalSize', language)}: {formatFileSize(totalSize)}
                </p>
              </div>
            )}

            <div className="max-h-48 overflow-y-auto space-y-2">
              {files.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  className="flex items-center justify-between p-3 bg-muted/50 rounded-md"
                >
                  <div className="flex items-center space-x-3 min-w-0 flex-1">
                    {getFileIcon(file)}
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                  >
                    <X className="h-4 w-4" />
                    <span className="sr-only">{getTranslation('removeFile', language)}</span>
                  </Button>
                </div>
              ))}
            </div>

            <div className="text-xs text-muted-foreground">
              {getTranslation('totalSize', language)}: {formatFileSize(totalSize)}
            </div>
          </div>
        )}

        {files.length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-4">
            {getTranslation('noFilesSelected', language)}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
