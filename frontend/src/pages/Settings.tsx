import { useQuery } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import { useTheme } from "../hooks/useTheme";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();

  const { data: ollamaHealth, isLoading: ollamaLoading } = useQuery({
    queryKey: ["ollama-health"],
    queryFn: apiClient.getOllamaHealth,
    retry: false,
  });

  return (
    <div>
      <h2 className="text-2xl font-bold">Settings</h2>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Configure Ollama endpoint, model, file limits, and ignored paths.
      </p>
      <div className="mt-8 max-w-lg space-y-6">
        <div>
          <label
            htmlFor="theme"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value as "light" | "dark")}
            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
          <h3 className="font-semibold">Ollama connection</h3>
          {ollamaLoading && (
            <p className="mt-2 text-sm text-gray-500">Checking Ollama...</p>
          )}
          {!ollamaLoading && ollamaHealth && (
            <dl className="mt-3 space-y-2 text-sm">
              <div>
                <dt className="text-gray-500">Status</dt>
                <dd
                  className={
                    ollamaHealth.status === "available"
                      ? "text-green-600 dark:text-green-400"
                      : "text-amber-600 dark:text-amber-400"
                  }
                >
                  {ollamaHealth.status}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Endpoint</dt>
                <dd className="font-mono text-xs">{ollamaHealth.base_url}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Configured model</dt>
                <dd>{ollamaHealth.model}</dd>
              </div>
              {ollamaHealth.models_available.length > 0 && (
                <div>
                  <dt className="text-gray-500">Available models</dt>
                  <dd>{ollamaHealth.models_available.join(", ")}</dd>
                </div>
              )}
            </dl>
          )}
          <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
            Configure Ollama via environment variables: OLLAMA_BASE_URL,
            OLLAMA_MODEL, AI_MAX_FILES, AI_MAX_CHARS_PER_FILE.
          </p>
        </div>
      </div>
    </div>
  );
}
