import type { Metadata } from 'next';
import './globals.css';
import { SimulationProvider } from '@/lib/store';
import { Geist } from "next/font/google";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

export const metadata: Metadata = {
  title: 'IoT SecureNet — SOC Dashboard',
  description: 'Real-Time IoT Security Monitoring Platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={cn("dark", "font-sans", geist.variable)}>
      <body className="antialiased h-screen overflow-hidden bg-cyber-bg text-cyber-text">
        <SimulationProvider>
          {children}
        </SimulationProvider>
      </body>
    </html>
  );
}
