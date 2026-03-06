import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "California National Park Visitation Planner",
  description: "Scaffold for the California National Park Visitation Planner frontend",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
