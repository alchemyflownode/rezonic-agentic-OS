import type { Metadata } from 'next';
import './globals.css';
import { OSSidebar } from '@/components/os/OSSidebar';
import { OSHeader } from '@/components/os/OSHeader';
import { OSStatusBar } from '@/components/os/OSStatusBar';

export const metadata: Metadata = {
  title: 'Phoenix OS',
  description: 'Sovereign AI Operating System',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>
        <div className="flex h-screen bg-[#0a0a0c] overflow-hidden">
          <OSSidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <OSHeader />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
            <OSStatusBar />
          </div>
        </div>
      </body>
    </html>
  );
}
