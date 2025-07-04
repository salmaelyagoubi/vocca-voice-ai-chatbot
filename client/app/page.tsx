"use client";

import { DailyTransport } from "@daily-co/realtime-ai-daily";
import { TooltipProvider } from "@radix-ui/react-tooltip";
import { useEffect, useRef, useState } from "react";
import { LLMHelper, RTVIClient } from "realtime-ai";
import { RTVIClientAudio, RTVIClientProvider } from "realtime-ai-react";

import App from "@/components/App";
import { AppProvider } from "@/components/context";
import Header from "@/components/Header";
import {
  BOT_READY_TIMEOUT,
  defaultConfig,
  defaultServices,
} from "@/rtvi.config";

export default function Home() {
  const [voiceClientInitialized, setVoiceClientInitialized] = useState(false);
  const voiceClientRef = useRef<RTVIClient | null>(null);

  useEffect(() => {
    if (voiceClientRef.current) return;

    const voiceClient = new RTVIClient({
      transport: new DailyTransport(),
      params: {
        baseUrl: process.env.NEXT_PUBLIC_BASE_URL || "/api",
        requestData: {
          services: defaultServices,
          config: defaultConfig,
        },
      },
      timeout: BOT_READY_TIMEOUT,
    });

    const llmHelper = new LLMHelper({});
    voiceClient.registerHelper("llm", llmHelper);

    voiceClientRef.current = voiceClient;
    setVoiceClientInitialized(true);
  }, []);

  return (
    <RTVIClientProvider client={voiceClientRef.current!}>
      <AppProvider>
        <TooltipProvider>
          <main>
            <Header />
            <div id="app">
              {voiceClientInitialized ? (
                <App />
              ) : (
                <div className="flex justify-center items-center h-screen">
                  <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-blue-500 border-solid"></div>
                </div>
              )}
            </div>
          </main>
          <aside id="tray" />
        </TooltipProvider>
      </AppProvider>
      <RTVIClientAudio />
    </RTVIClientProvider>
  );
}
