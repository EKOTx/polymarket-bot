import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Polymarket Intelligence",
  description: "Quantitative prediction-market analytics platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full dark">
      <body className="min-h-full flex flex-col bg-[#0d1117] text-[#e6edf3]">
        {children}
      </body>
    </html>
  );
}
