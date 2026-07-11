import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { AuthProvider } from "./context/AuthContext";
import { LoginPage } from "./pages/Login";

describe("LoginPage", () => {
  it("renders login heading", async () => {
    render(
      <AuthProvider>
        <MemoryRouter>
          <LoginPage />
        </MemoryRouter>
      </AuthProvider>,
    );
    expect(await screen.findByRole("heading", { name: /login/i })).toBeInTheDocument();
  });
});
