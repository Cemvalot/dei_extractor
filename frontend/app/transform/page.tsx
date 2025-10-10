'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { runTransform, runConsumptionsTransform, TransformOptions } from '@/lib/transformApi';
import { getTranslation, getCurrentLanguage } from '@/lib/i18n';
import Link from 'next/link';
import { ArrowLeft, FileText, BarChart3 } from 'lucide-react';

export default function TransformPage() {
  const [currentLanguage] = useState<'en' | 'gr'>(getCurrentLanguage());
  const [activeTab, setActiveTab] = useState<'phase1' | 'consumptions'>('phase1');

  // Phase-1 transform state
  const [xlsx, setXlsx] = useState<File | null>(null);
  const [classMap, setClassMap] = useState<File | null>(null);
  const [year, setYear] = useState<number>(new Date().getFullYear() >= 2023 ? 2023 : new Date().getFullYear());
  const [keepStr, setKeepStr] = useState<boolean>(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Consumptions transform state
  const [dataFile, setDataFile] = useState<File | null>(null);
  const [consumptionsBusy, setConsumptionsBusy] = useState(false);
  const [consumptionsError, setConsumptionsError] = useState<string | null>(null);

  const onRun = async () => {
    setError(null);
    if (!xlsx) { setError('Please select a Phase-1 .xlsx file'); return; }
    setBusy(true);
    try {
      const { blob, filename } = await runTransform(xlsx, { year, keepStrIds: keepStr, classMapFile: classMap });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || 'Transform failed');
    } finally {
      setBusy(false);
    }
  };

  const onRunConsumptions = async () => {
    setConsumptionsError(null);
    if (!dataFile) {
      setConsumptionsError(getTranslation('noDataFileSelected', currentLanguage));
      return;
    }
    setConsumptionsBusy(true);
    try {
      const { blob, filename } = await runConsumptionsTransform(dataFile);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setConsumptionsError(e?.message || getTranslation('transformError', currentLanguage));
    } finally {
      setConsumptionsBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href="/"
                className="flex items-center space-x-2 px-3 py-2 rounded-md hover:bg-accent transition-colors"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="text-sm font-medium">Back to Main</span>
              </Link>
              <h1 className="text-2xl font-bold">Transform (Phase-1 → Final)</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        {/* Tab Navigation */}
        <div className="flex space-x-1 bg-muted p-1 rounded-lg">
          <button
            onClick={() => setActiveTab('phase1')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'phase1'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>Phase-1 Transform</span>
          </button>
          <button
            onClick={() => setActiveTab('consumptions')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'consumptions'
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <BarChart3 className="h-4 w-4" />
            <span>{getTranslation('consumptionsTransform', currentLanguage)}</span>
          </button>
        </div>

        {/* Phase-1 Transform Tab */}
        {activeTab === 'phase1' && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>Upload Files</CardTitle>
                <CardDescription>Phase-1 Excel is required. Classification CSV is optional.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium">Phase-1 Excel (.xlsx)</label>
                  <input
                    type="file"
                    accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
                    onChange={(e) => setXlsx(e.target.files?.[0] || null)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium">Classification CSV (optional)</label>
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    onChange={(e) => setClassMap(e.target.files?.[0] || null)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Options</CardTitle>
                <CardDescription>Choose year and output preferences.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-4">
                  <label className="w-32 text-sm font-medium">Year</label>
                  <input type="number" className="border rounded px-2 py-1 w-40"
                    value={year} onChange={(e) => setYear(parseInt(e.target.value || '2023', 10))}/>
                </div>
                <div className="flex items-center gap-4">
                  <label className="w-32 text-sm font-medium">Keep string IDs</label>
                  <input type="checkbox" checked={keepStr} onChange={(e) => setKeepStr(e.target.checked)} />
                </div>
                {error && <p className="text-red-600 text-sm">{error}</p>}
                <Button onClick={onRun} disabled={!xlsx || busy}>
                  {busy ? 'Processing…' : 'Run Transform'}
                </Button>
              </CardContent>
            </Card>
          </>
        )}

        {/* Consumptions Transform Tab */}
        {activeTab === 'consumptions' && (
          <>
            <Card>
              <CardHeader>
                <CardTitle>{getTranslation('consumptionsTransform', currentLanguage)}</CardTitle>
                <CardDescription>{getTranslation('consumptionsTransformDescription', currentLanguage)}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium">{getTranslation('dataFileLabel', currentLanguage)}</label>
                  <input
                    type="file"
                    accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
                    onChange={(e) => setDataFile(e.target.files?.[0] || null)}
                  />
                  <p className="text-sm text-muted-foreground mt-1">
                    {getTranslation('dataFileAccepted', currentLanguage)}
                  </p>
                </div>
                {consumptionsError && <p className="text-red-600 text-sm">{consumptionsError}</p>}
                <Button onClick={onRunConsumptions} disabled={!dataFile || consumptionsBusy}>
                  {consumptionsBusy ? getTranslation('transformProcessing', currentLanguage) : getTranslation('transformButton', currentLanguage)}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Grouping Logic</CardTitle>
                <CardDescription>How data is grouped by consumption period and measurements are displayed</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <h4 className="font-medium mb-2">Data Organization:</h4>
                    <p className="text-sm text-muted-foreground">
                      <strong>Group by: ΠερίοδοςΚατανάλωσης_Αρχή</strong>
                    </p>
                    <p className="text-sm text-muted-foreground mt-2">
                      For each consumption period, show all accounts with their measurements
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg">
                      <h4 className="font-medium text-green-600 mb-2">Per Account</h4>
                      <p className="text-sm text-muted-foreground mb-2">Shows for each account:</p>
                      <ul className="text-sm space-y-1">
                        <li>• Προηγούμενη_Μέτρηση</li>
                        <li>• Τελευταία_Μέτρηση</li>
                        <li>• Συνολική_Κατανάλωση</li>
                        <li>• Account details & dates</li>
                      </ul>
                    </div>

                    <div className="p-4 border rounded-lg">
                      <h4 className="font-medium text-blue-600 mb-2">Period Summary</h4>
                      <p className="text-sm text-muted-foreground mb-2">Shows totals for each period:</p>
                      <ul className="text-sm space-y-1">
                        <li>• Total accounts count</li>
                        <li>• Sum of all measurements</li>
                        <li>• Period start/end dates</li>
                        <li>• Highlighted summary row</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
