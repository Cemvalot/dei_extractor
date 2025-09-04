'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useExtractorStore } from '@/store/useExtractorStore';
import { getTranslation, getCurrentLanguage } from '@/lib/i18n';
import { downloadZip, ApiError } from '@/lib/api';
import { Download, Calendar, Settings, FileText } from 'lucide-react';

export function HistoryList() {
  const { history, errorRun } = useExtractorStore();
  const language = getCurrentLanguage();

  const handleDownload = async (runId: string) => {
    try {
      await downloadZip(runId);
    } catch (error) {
      console.error('Download Error:', error);
      if (error instanceof ApiError) {
        errorRun(error.message);
      } else {
        errorRun(getTranslation('errorUnknown', language));
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString(language === 'gr' ? 'el-GR' : 'en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getOptionsSummary = (options: any) => {
    const parts = [];
    if (options.apply_filter) {
      parts.push(language === 'gr' ? 'Φίλτρο' : 'Filter');
    }
    if (options.verbose) {
      parts.push(language === 'gr' ? 'Λεπτομερή' : 'Verbose');
    }
    parts.push(options.language === 'gr' ? 'Ελληνικά' : 'English');
    return parts.join(' • ');
  };

  if (history.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{getTranslation('historyTitle', language)}</CardTitle>
          <CardDescription>
            {getTranslation('historyEmpty', language)}
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{getTranslation('historyTitle', language)}</CardTitle>
        <CardDescription>
          {getTranslation('historyEmpty', language)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {history.map((item, index) => (
            <div
              key={`${item.run_id}-${item.createdAt}-${index}`}
              className="flex items-center justify-between p-3 bg-muted/50 rounded-md"
            >
              <div className="flex items-center space-x-3 min-w-0 flex-1">
                <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center space-x-2 text-sm">
                    <Calendar className="h-3 w-3 text-muted-foreground" />
                    <span className="font-medium">
                      {formatDate(item.createdAt)}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-muted-foreground mt-1">
                    <Settings className="h-3 w-3" />
                    <span>{getOptionsSummary(item.options)}</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1 font-mono">
                    ID: {item.run_id}
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDownload(item.run_id)}
                className="flex-shrink-0"
              >
                <Download className="h-3 w-3 mr-1" />
                {getTranslation('historyDownload', language)}
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
