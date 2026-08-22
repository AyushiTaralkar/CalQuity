"use client";

import { useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: {
    document: string;
    page?: number;
    authority?: string;
    score?: number;
  }[];
  confidence?: number;
};

export default function Home() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm ParcelPilot Support AI. I can help you investigate orders, tickets, policies and customer-specific contracts.",
    },
  ]);

  const [accountId, setAccountId] = useState("ACCT-001");

  const askQuestion = async () => {
    if (!question.trim() || loading) return;

    const userQuestion = question.trim();

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      console.log("Calling ParcelPilot API...");

const response = await fetch(
  "http://127.0.0.1:8000/api/v1/query",
  {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: userQuestion,
      account_id: accountId,
    }),
  }
);

console.log("API status:", response.status);
console.log("API ok:", response.ok);

if (!response.ok) {
  const errorText = await response.text();
  console.error("API response:", errorText);
  throw new Error(`HTTP ${response.status}: ${errorText}`);
}

const data = await response.json();

console.log("API response data:", data);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer || "No answer returned.",
          sources: data.sources || [],
          confidence: data.confidence,
        },
      ]);
    } catch (error) {
  console.error("ParcelPilot API error:", error);

  setMessages((prev) => [
    ...prev,
    {
      role: "assistant",
      content:
        error instanceof Error
          ? `API Error: ${error.message}`
          : "Unknown API error",
    },
  ]);
}finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f9fc] text-[#172033]">
      {/* NAVBAR */}
      <header className="h-[72px] border-b border-[#e6eaf0] bg-white flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#102a43] flex items-center justify-center text-white font-bold">
            P
          </div>

          <div>
            <div className="font-bold text-lg tracking-tight">
              ParcelPilot
            </div>
            <div className="text-[11px] text-gray-500">
              YOUR PARCEL. OUR PRIORITY.
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500">
            Support Center
          </div>

          <div className="h-9 w-9 rounded-full bg-[#dce8f5] flex items-center justify-center text-sm font-semibold text-[#102a43]">
            AT
          </div>
        </div>
      </header>

      <div className="flex min-h-[calc(100vh-72px)]">
        {/* SIDEBAR */}
        <aside className="w-[240px] border-r border-[#e6eaf0] bg-white p-5 hidden md:block">
          <div className="mb-8">
            <p className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold mb-3">
              Workspace
            </p>

            <div className="space-y-1">
              <SidebarItem
                icon="⌂"
                label="Overview"
                active
              />

              <SidebarItem
                icon="✦"
                label="AI Support"
              />

              <SidebarItem
                icon="□"
                label="Orders"
              />

              <SidebarItem
                icon="!"
                label="Tickets"
              />
            </div>
          </div>

          <div>
            <p className="text-[11px] uppercase tracking-wider text-gray-400 font-semibold mb-3">
              Account
            </p>

            <select
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
            >
              <option value="ACCT-001">Northstar Logistics</option>
              <option value="ACCT-002">LumenWorks</option>
            </select>
          </div>

          <div className="absolute bottom-6 left-5 right-5 w-[200px]">
            <div className="rounded-xl bg-[#f4f7fa] p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-xs font-semibold">
                  AI System Online
                </span>
              </div>

              <p className="text-[11px] text-gray-500">
                Connected to ParcelPilot support infrastructure.
              </p>
            </div>
          </div>
        </aside>

        {/* MAIN */}
        <main className="flex-1 flex flex-col">
          {/* PAGE HEADER */}
          <div className="px-8 pt-8 pb-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400 mb-1">
                  SUPPORT / AI ASSISTANT
                </p>

                <h1 className="text-2xl font-bold tracking-tight">
                  How can we help?
                </h1>

                <p className="text-sm text-gray-500 mt-1">
                  Ask about shipments, policies, contracts or support tickets.
                </p>
              </div>

              <div className="hidden lg:flex items-center gap-2 border border-gray-200 bg-white rounded-lg px-3 py-2">
                <span className="h-2 w-2 bg-green-500 rounded-full" />
                <span className="text-xs text-gray-600">
                  Account: {accountId}
                </span>
              </div>
            </div>
          </div>

          {/* CHAT AREA */}
          <div className="flex-1 px-8 pb-5 overflow-y-auto">
            <div className="max-w-4xl mx-auto space-y-5">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={
                    message.role === "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  {message.role === "assistant" ? (
                    <div className="max-w-[85%]">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-7 w-7 rounded-lg bg-[#102a43] text-white flex items-center justify-center text-xs font-bold">
                          P
                        </div>

                        <span className="text-xs font-semibold">
                          ParcelPilot AI
                        </span>

                        <span className="text-[10px] text-gray-400">
                          Support Agent
                        </span>
                      </div>

                      <div className="rounded-2xl rounded-tl-sm bg-white border border-gray-200 shadow-sm p-5">
                        <div className="text-sm leading-6 whitespace-pre-wrap">
                          {message.content}
                        </div>

                        {message.confidence !== undefined && (
                          <div className="mt-4 pt-3 border-t border-gray-100">
                            <div className="flex items-center justify-between">
                              <span className="text-[11px] text-gray-400">
                                Evidence confidence
                              </span>

                              <span className="text-[11px] font-semibold">
                                {Math.round(
                                  message.confidence * 100
                                )}
                                %
                              </span>
                            </div>

                            <div className="h-1.5 bg-gray-100 rounded-full mt-2 overflow-hidden">
                              <div
                                className="h-full bg-[#102a43] rounded-full"
                                style={{
                                  width: `${Math.min(
                                    message.confidence * 100,
                                    100
                                  )}%`,
                                }}
                              />
                            </div>
                          </div>
                        )}

                        {message.sources &&
                          message.sources.length > 0 && (
                            <div className="mt-4">
                              <p className="text-[10px] uppercase tracking-wider text-gray-400 font-semibold mb-2">
                                Sources
                              </p>

                              <div className="space-y-2">
                                {message.sources.map(
                                  (source, sourceIndex) => (
                                    <div
                                      key={sourceIndex}
                                      className="flex items-center justify-between rounded-lg bg-[#f7f9fc] border border-gray-100 px-3 py-2"
                                    >
                                      <div className="flex items-center gap-2">
                                        <span>📄</span>

                                        <div>
                                          <p className="text-xs font-medium">
                                            {source.document ||
                                              "Document"}
                                          </p>

                                          {source.page && (
                                            <p className="text-[10px] text-gray-400">
                                              Page {source.page}
                                            </p>
                                          )}
                                        </div>
                                      </div>

                                      {source.authority && (
                                        <span className="text-[10px] bg-white border border-gray-200 rounded px-2 py-1">
                                          {source.authority}
                                        </span>
                                      )}
                                    </div>
                                  )
                                )}
                              </div>
                            </div>
                          )}
                      </div>
                    </div>
                  ) : (
                    <div className="max-w-[75%]">
                      <div className="rounded-2xl rounded-tr-sm bg-[#102a43] text-white px-5 py-3">
                        <p className="text-sm leading-6">
                          {message.content}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="flex items-start gap-2">
                  <div className="h-7 w-7 rounded-lg bg-[#102a43] text-white flex items-center justify-center text-xs font-bold">
                    P
                  </div>

                  <div className="bg-white border border-gray-200 rounded-xl px-4 py-3">
                    <div className="flex gap-1">
                      <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" />
                      <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:100ms]" />
                      <span className="h-2 w-2 bg-gray-400 rounded-full animate-bounce [animation-delay:200ms]" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* INPUT */}
          <div className="px-8 pb-7">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white border border-gray-200 shadow-sm rounded-2xl p-2 flex items-end gap-2">
                <textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => {
                    if (
                      e.key === "Enter" &&
                      !e.shiftKey
                    ) {
                      e.preventDefault();
                      askQuestion();
                    }
                  }}
                  placeholder="Ask about an order, ticket, policy or contract..."
                  className="flex-1 resize-none outline-none px-3 py-3 text-sm min-h-[48px] max-h-[120px]"
                  rows={1}
                />

                <button
                  onClick={askQuestion}
                  disabled={loading || !question.trim()}
                  className="h-11 px-5 rounded-xl bg-[#102a43] text-white text-sm font-semibold hover:bg-[#173b5c] disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                  {loading ? "..." : "Ask"}
                </button>
              </div>

              <p className="text-center text-[10px] text-gray-400 mt-2">
                ParcelPilot AI uses operational data and authorized company
                documentation to generate grounded responses.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function SidebarItem({
  icon,
  label,
  active = false,
}: {
  icon: string;
  label: string;
  active?: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm cursor-pointer ${
        active
          ? "bg-[#eef3f8] text-[#102a43] font-semibold"
          : "text-gray-500 hover:bg-gray-50"
      }`}
    >
      <span className="w-5 text-center">{icon}</span>
      {label}
    </div>
  );
}