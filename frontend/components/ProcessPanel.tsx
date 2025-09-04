'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useExtractorStore } from '@/store/useExtractorStore';
import { getTranslation, getCurrentLanguage } from '@/lib/i18n';
import { processFilesWithProgress, downloadZip, ApiError } from '@/lib/api';
import { Play, Download, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';

export function ProcessPanel() {
  const { files, options, run, startRun, updateProgress, addLog, completeRun, errorRun, resetRun, addToHistory } = useExtractorStore();
  const [showLogs, setShowLogs] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const language = getCurrentLanguage();

  // Clean up event source on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleProcess = async () => {
    if (files.length === 0) {
      errorRun(getTranslation('errorNoFiles', language));
      return;
    }

    setIsProcessing(true);
    resetRun();

    let currentRunId = '';

    try {
      // Start processing with progress updates
      const response = await processFilesWithProgress(
        files,
        options,
        (event) => {
          // Set run ID from the first event if available
          if (event.run_id && !currentRunId) {
            currentRunId = event.run_id;
            startRun(event.run_id);
          }

          updateProgress(event.progress, event.stage, event.message);

          // Add to logs if verbose
          if (options.verbose && event.message) {
            addLog(`[${event.stage || 'Progress'}] ${event.message}`);
          }

          // Check if complete
          if (event.progress >= 100) {
            completeRun();
            setIsProcessing(false);

            // Add to history
            const fallbackId = `run_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            addToHistory({
              run_id: currentRunId || event.run_id || fallbackId,
              createdAt: new Date().toISOString(),
              options: { ...options }
            });
          }
        },
        (error) => {
          console.error('Process Error:', error);
          errorRun(error.message);
          setIsProcessing(false);
        }
      );
    } catch (error) {
      console.error('Process Error:', error);
      if (error instanceof ApiError) {
        errorRun(error.message);
      } else {
        errorRun(getTranslation('errorUnknown', language));
      }
      setIsProcessing(false);
    }
  };

  const handleDownload = async () => {
    if (!run.id) return;

    try {
      await downloadZip(run.id);
    } catch (error) {
      console.error('Download Error:', error);
      if (error instanceof ApiError) {
        errorRun(error.message);
      } else {
        errorRun(getTranslation('errorUnknown', language));
      }
    }
  };

  const handleRetry = () => {
    resetRun();
    setIsProcessing(false);
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  };

  const canProcess = files.length > 0 && !isProcessing && run.status !== 'running';
  const canDownload = run.status === 'done' && run.id;
  const hasError = run.status === 'error';

  return (
    <Card>
      <CardHeader>
        <CardTitle>{getTranslation('processTitle', language)}</CardTitle>
        <CardDescription>
          {run.status === 'idle' && getTranslation('processButton', language)}
          {run.status === 'running' && getTranslation('processing', language)}
          {run.status === 'done' && getTranslation('done', language)}
          {run.status === 'error' && getTranslation('retry', language)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Process Button */}
        <div className="flex gap-2">
          <Button
            onClick={handleProcess}
            disabled={!canProcess}
            size="lg"
            className="flex-1"
          >
            <Play className="h-4 w-4 mr-2" />
            {getTranslation('processButton', language)}
          </Button>

          {canDownload && (
            <Button
              onClick={handleDownload}
              variant="outline"
              size="lg"
            >
              <Download className="h-4 w-4 mr-2" />
              {getTranslation('download', language)}
            </Button>
          )}

          {hasError && (
            <Button
              onClick={handleRetry}
              variant="outline"
              size="lg"
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              {getTranslation('retry', language)}
            </Button>
          )}
        </div>

        {/* Progress */}
        {run.status === 'running' && (
          <div className="space-y-3">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>{getTranslation('progressTitle', language)}</span>
                <span>{run.progress}%</span>
              </div>
              <Progress value={run.progress} className="h-2" />
            </div>

            {run.stage && (
              <div className="text-sm">
                <span className="font-medium">{getTranslation('stage', language)}: </span>
                <span>{run.stage}</span>
              </div>
            )}

            {run.message && (
              <div className="text-sm text-muted-foreground">
                <span className="font-medium">{getTranslation('message', language)}: </span>
                <span>{run.message}</span>
              </div>
            )}
          </div>
        )}

        {/* Logs */}
        {options.verbose && run.logs.length > 0 && (
          <div className="space-y-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLogs(!showLogs)}
              className="w-full justify-between"
            >
              <span>{getTranslation('logs', language)}</span>
              {showLogs ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {showLogs && (
              <div className="bg-muted/50 rounded-md p-3 max-h-48 overflow-y-auto">
                <pre className="text-xs font-mono whitespace-pre-wrap">
                  {run.logs.join('\n')}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {hasError && run.message && (
          <Alert variant="destructive">
            <AlertDescription>
              {run.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Success Message */}
        {run.status === 'done' && run.id && (
          <Alert>
            <AlertDescription>
              {getTranslation('done', language)} - Run ID: {run.id}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
