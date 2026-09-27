import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";
import type { ChatResponse } from "./types";

const health = {
  status: "ok",
  app: "AyuPramana",
  version: "0.1.0",
  llm: { provider: "groq", model: "m", configured: true },
  embedding_model: "e",
  corpus: { raw_files: 1, manifest_entries: 1, documents: 1, chunks: 5 },
};

const block = (jurisdiction: "india" | "international") => ({
  jurisdiction,
  markdown: `Widgets must be registered [S1].`,
  citations: [
    {
      marker: 1,
      chunk_id: "c1",
      doc_id: "widgets_act",
      doc_title: "Sample Widgets Act (fictional)",
      section_ref: jurisdiction === "india" ? "Section 3" : "Article 2",
      jurisdiction,
      version_date: "2099-01-01",
      version: "abc123",
      source_url: "https://example.test/widgets",
      file: "india/widgets.txt",
      page: 1,
      snippet: "3. Registration of widgets.—(1) Any person crafting a widget shall apply…",
    },
  ],
  confidence: 0.8,
  confidence_label: "high" as const,
  abstained: false,
  abstain_reason: null,
  mode: "generated" as const,
  escalation_suggested: false,
  signals: {},
});

function mockApi(chat: ChatResponse) {
  return vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
    const url = String(input);
    const body = url.includes("/api/chat") ? chat : health;
    return new Response(JSON.stringify(body));
  });
}

const chatBoth: ChatResponse = {
  query_id: 1,
  answers: { india: block("india"), international: block("international") },
  disclaimer: "This is information, not legal advice.",
  language: "en",
};

describe("App shell", () => {
  it("renders the brand, starter prompts and backend status", async () => {
    mockApi(chatBoth);
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("AyuPramana");
    expect(screen.getByText("Can I patent a classical Ayurvedic formulation?")).toBeInTheDocument();
    expect(await screen.findByText("Backend online")).toBeInTheDocument();
  });

  it("switches jurisdiction with the toggle", async () => {
    mockApi(chatBoth);
    render(<App />);
    const both = screen.getByRole("radio", { name: "Both" });
    await userEvent.click(both);
    expect(both).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "India" })).toHaveAttribute("aria-checked", "false");
  });

  it("shows separate India and International cards with citation chips that open the source", async () => {
    const fetchMock = mockApi(chatBoth);
    render(<App />);
    await userEvent.click(screen.getByRole("radio", { name: "Both" }));
    await userEvent.type(screen.getByRole("textbox"), "How are widgets registered?");
    await userEvent.click(screen.getByRole("button", { name: "Send" }));

    const india = await screen.findByRole("article", { name: "India" });
    const international = screen.getByRole("article", { name: "International" });
    expect(within(india).getByText("High confidence")).toBeInTheDocument();
    expect(within(international).getByText(/Article 2/)).toBeInTheDocument();
    expect(within(india).getByText("This is information, not legal advice.")).toBeInTheDocument();

    const request = JSON.parse(String(fetchMock.mock.calls.find((c) => String(c[0]).includes("/api/chat"))?.[1]?.body));
    expect(request.jurisdiction).toBe("both");

    await userEvent.click(within(india).getByText(/Section 3 ·/));
    const panel = screen.getByRole("dialog");
    expect(within(panel).getByText(/Any person crafting a widget/)).toBeInTheDocument();
    expect(within(panel).getByRole("link", { name: /Open official source/ })).toHaveAttribute(
      "href",
      "https://example.test/widgets",
    );
  });
});
