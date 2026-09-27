import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import App from "./App";

const health = {
  status: "ok",
  app: "AyuPramana",
  version: "0.1.0",
  llm: { provider: "groq", model: "m", configured: true },
  embedding_model: "e",
  corpus: { raw_files: 0 },
};

function mockFetch() {
  vi.spyOn(globalThis, "fetch").mockImplementation(async () => new Response(JSON.stringify(health)));
}

describe("App shell", () => {
  it("renders the brand, starter prompts and backend status", async () => {
    mockFetch();
    render(<App />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("AyuPramana");
    expect(screen.getByText("Can I patent a classical Ayurvedic formulation?")).toBeInTheDocument();
    expect(await screen.findByText("Backend online")).toBeInTheDocument();
  });

  it("switches jurisdiction with the toggle", async () => {
    mockFetch();
    render(<App />);
    const both = screen.getByRole("radio", { name: "Both" });
    expect(both).toHaveAttribute("aria-checked", "false");
    await userEvent.click(both);
    expect(both).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "India" })).toHaveAttribute("aria-checked", "false");
  });
});
