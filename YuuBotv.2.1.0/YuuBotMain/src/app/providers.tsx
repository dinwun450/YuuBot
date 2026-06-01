"use client";

import { CopilotKit } from "@copilotkit/react-core/v2";

export function Providers({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      inspectorDefaultAnchor={{ horizontal: "right", vertical: "top" }}
      useSingleEndpoint={false}
    >
      {children}
    </CopilotKit>
  );
}