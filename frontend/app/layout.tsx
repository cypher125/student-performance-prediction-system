import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Student Performance Prediction System",
  description: "AI-powered early warning for student academic performance, Department of Computer Science, YABATECH",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
