import type { Metadata } from "next";
import "./globals.css";
import "leaflet/dist/leaflet.css";
import "@copilotkit/react-core/v2/styles.css";
import "@copilotkit/react-ui/styles.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "YuuBot v.2.1.0",
  description: "CopilotKit earthquake dashboard powered by Snowflake data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
      </head>
      <body className="antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
