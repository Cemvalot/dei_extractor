'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useExtractorStore } from '@/store/useExtractorStore';
import { getTranslation, getCurrentLanguage } from '@/lib/i18n';
import { Language } from '@/lib/types';

export function OptionsForm() {
  const { options, setOptions, setLanguage } = useExtractorStore();
  const language = getCurrentLanguage();

  const handleLanguageChange = (newLanguage: Language) => {
    setLanguage(newLanguage);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{getTranslation('optionsTitle', language)}</CardTitle>
        <CardDescription>
          {getTranslation('languageDesc', language)}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Language Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">
            {getTranslation('language', language)}
          </label>
          <Select
            value={options.language}
            onValueChange={handleLanguageChange}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gr">Ελληνικά</SelectItem>
              <SelectItem value="en">English</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-xs text-muted-foreground">
            {getTranslation('languageDesc', language)}
          </p>
        </div>

        {/* Apply Filter Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <label className="text-sm font-medium">
              {getTranslation('applyFilter', language)}
            </label>
            <p className="text-xs text-muted-foreground">
              {getTranslation('applyFilterDesc', language)}
            </p>
          </div>
          <Switch
            checked={options.apply_filter}
            onCheckedChange={(checked) => setOptions({ apply_filter: checked })}
            aria-label={getTranslation('applyFilter', language)}
          />
        </div>

        {/* Verbose Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <label className="text-sm font-medium">
              {getTranslation('verbose', language)}
            </label>
            <p className="text-xs text-muted-foreground">
              {getTranslation('verboseDesc', language)}
            </p>
          </div>
          <Switch
            checked={options.verbose}
            onCheckedChange={(checked) => setOptions({ verbose: checked })}
            aria-label={getTranslation('verbose', language)}
          />
        </div>
      </CardContent>
    </Card>
  );
}
