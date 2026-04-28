import type { Metadata } from "next";
import { Fira_Code, Inter } from "next/font/google";
import { Navbar } from "@/components/navbar";
import "./globals.css";

const inter = Inter({
  variable: "--font-primary",
  subsets: ["latin"],
});

const firaCode = Fira_Code({
  variable: "--font-code",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AirIQ Smart City AQI Monitor",
  description: "Breathe Smarter, Travel Cleaner",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${firaCode.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[#050808] text-zinc-100">
        <Navbar />
        <main className="mx-auto flex w-full max-w-7xl flex-1 px-4 py-6 sm:px-6">{children}</main>
      </body>
    </html>
  );
}
