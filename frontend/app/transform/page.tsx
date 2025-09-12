'use client';

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { runTransform, TransformOptions } from '@/lib/transformApi';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function TransformPage() {
  const [xlsx, setXlsx] = useState<File | null>(null);
  const [classMap, setClassMap] = useState<File | null>(null);
  const [year, setYear] = useState<number>(new Date().getFullYear() >= 2023 ? 2023 : new Date().getFullYear());
  const [keepStr, setKeepStr] = useState<boolean>(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          <Button onClick={onRun} disabled={!xlsx || busy}>{busy ? 'Processing…' : 'Run Transform'}</Button>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}
