'use client';

import React, { useState, useEffect } from 'react';
import { UploadZone } from '@/components/UploadZone';
import { OptionsForm } from '@/components/OptionsForm';
import { ProcessPanel } from '@/components/ProcessPanel';
import { HistoryList } from '@/components/HistoryList';
import { useExtractorStore } from '@/store/useExtractorStore';
import { getTranslation, getCurrentLanguage, setLanguage } from '@/lib/i18n';
import { Language } from '@/lib/types';
import { Globe, FileText } from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  const { setLanguage: setStoreLanguage } = useExtractorStore();
  const [currentLanguage, setCurrentLanguage] = useState<Language>('gr');
  const [isClient, setIsClient] = useState(false);

  // Initialize language from localStorage
  useEffect(() => {
    setIsClient(true);
    const savedLanguage = getCurrentLanguage();
    setCurrentLanguage(savedLanguage);
    setStoreLanguage(savedLanguage);
  }, [setStoreLanguage]);

  const handleLanguageToggle = () => {
    const newLanguage: Language = currentLanguage === 'gr' ? 'en' : 'gr';
    setCurrentLanguage(newLanguage);
    setLanguage(newLanguage);
    setStoreLanguage(newLanguage);
  };

  // Prevent hydration mismatch by using consistent initial state
  const displayLanguage = isClient ? currentLanguage : 'gr';

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">
                {getTranslation('appName', displayLanguage)}
              </h1>
              <p className="text-sm text-muted-foreground">
                {getTranslation('appSubtitle', displayLanguage)}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/transform"
                className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
              >
                <FileText className="h-4 w-4" />
                <span className="text-sm font-medium">Transform</span>
              </Link>
              <button
                onClick={handleLanguageToggle}
                className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
                aria-label="Toggle language"
              >
                <Globe className="h-4 w-4" />
                <span className="text-sm font-medium">
                  {getTranslation('languageSwitch', displayLanguage)}
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Upload Section */}
          <UploadZone />

          {/* Options Section */}
          <OptionsForm />

          {/* Process Section */}
          <ProcessPanel />

          {/* History Section */}
          <HistoryList />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 mt-16">
        <div className="container mx-auto px-4 py-6">
          <div className="text-center">
            <p className="text-sm text-muted-foreground">
              {getTranslation('privacyNote', displayLanguage)}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
