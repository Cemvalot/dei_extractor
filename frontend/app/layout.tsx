import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Energy Data Transformation Engine (EDTE)',
  description:
    'Advanced system for automated extraction and structuring of data from energy bills and invoices.',
  keywords: ['energy', 'EDTE', 'bills', 'invoices', 'data transformation'],
  authors: [{ name: 'EDTE Team' }],
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
