import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ApiError, apiClient } from "../api/client";
import type { UserSettingsUpdate } from "../api/types";
import { useTheme } from "../hooks/useTheme";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["user-settings"],
    queryFn: apiClient.getMySettings,
  });

  const [form, setForm] = useState({
    ollama_base_url: "",
    ollama_model: "",
    ignored_folders: "",
    ignored_extensions: "",
    max_file_size_bytes: "",
  });

  useEffect(() => {
    if (!data) return;
    setForm({
      ollama_base_url: data.overrides.ollama_base_url ?? data.effective.ollama_base_url,
      ollama_model: data.overrides.ollama_model ?? data.effective.ollama_model,
      ignored_folders: data.effective.ignored_folders,
      ignored_extensions: data.effective.ignored_extensions,
      max_file_size_bytes: String(data.effective.max_file_size_bytes),
    });
  }, [data]);

  const {
    data: ollamaHealth,
    isLoading: ollamaLoading,
    refetch: refetchOllamaHealth,
  } = useQuery({
    queryKey: ["ollama-health", "me"],
    queryFn: apiClient.getMyOllamaHealth,
    enabled: Boolean(data),
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: (payload: UserSettingsUpdate) => apiClient.updateMySettings(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["user-settings"] });
      await refetchOllamaHealth();
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const payload: UserSettingsUpdate = {
      ollama_base_url: form.ollama_base_url.trim() || null,
      ollama_model: form.ollama_model.trim() || null,
      ignored_folders: form.ignored_folders.trim() || null,
      ignored_extensions: form.ignored_extensions.trim() || null,
      max_file_size_bytes: form.max_file_size_bytes
        ? Number(form.max_file_size_bytes)
        : null,
    };
    saveMutation.mutate(payload);
  }

  return (
    <div>
      <h2 className="text-2xl font-bold">Settings</h2>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Configure your Ollama connection, model, and analysis file filters.
      </p>

      <div className="mt-8 max-w-2xl space-y-6">
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

        {isLoading && <p className="text-sm text-gray-500">Loading settings...</p>}

        {!isLoading && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="ollama_base_url" className="block text-sm font-medium">
                Ollama endpoint
              </label>
              <input
                id="ollama_base_url"
                type="url"
                value={form.ollama_base_url}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    ollama_base_url: event.target.value,
                  }))
                }
                placeholder="http://localhost:11434"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </div>

            <div>
              <label htmlFor="ollama_model" className="block text-sm font-medium">
                Ollama model
              </label>
              <input
                id="ollama_model"
                type="text"
                value={form.ollama_model}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    ollama_model: event.target.value,
                  }))
                }
                placeholder="qwen2.5"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </div>

            <div>
              <label htmlFor="ignored_folders" className="block text-sm font-medium">
                Ignored folders
              </label>
              <input
                id="ignored_folders"
                type="text"
                value={form.ignored_folders}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    ignored_folders: event.target.value,
                  }))
                }
                placeholder="node_modules,.git,dist"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
              <p className="mt-1 text-xs text-gray-500">Comma-separated folder names</p>
            </div>

            <div>
              <label htmlFor="ignored_extensions" className="block text-sm font-medium">
                Ignored extensions
              </label>
              <input
                id="ignored_extensions"
                type="text"
                value={form.ignored_extensions}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    ignored_extensions: event.target.value,
                  }))
                }
                placeholder=".min.js,.map,.png"
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
              <p className="mt-1 text-xs text-gray-500">Comma-separated file extensions</p>
            </div>

            <div>
              <label htmlFor="max_file_size_bytes" className="block text-sm font-medium">
                Max file size (bytes)
              </label>
              <input
                id="max_file_size_bytes"
                type="number"
                min={1024}
                max={10485760}
                value={form.max_file_size_bytes}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    max_file_size_bytes: event.target.value,
                  }))
                }
                className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-900"
              />
            </div>

            {saveMutation.isError && (
              <p className="text-sm text-red-600">
                {saveMutation.error instanceof ApiError
                  ? saveMutation.error.message
                  : "Failed to save settings."}
              </p>
            )}

            {saveMutation.isSuccess && (
              <p className="text-sm text-green-600 dark:text-green-400">
                Settings saved.
              </p>
            )}

            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {saveMutation.isPending ? "Saving..." : "Save settings"}
            </button>
          </form>
        )}

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
                <dt className="text-gray-500">Model</dt>
                <dd>{ollamaHealth.model}</dd>
              </div>
              {ollamaHealth.message && (
                <div>
                  <dt className="text-gray-500">Details</dt>
                  <dd>{ollamaHealth.message}</dd>
                </div>
              )}
              {ollamaHealth.models_available.length > 0 && (
                <div>
                  <dt className="text-gray-500">Available models</dt>
                  <dd>{ollamaHealth.models_available.join(", ")}</dd>
                </div>
              )}
            </dl>
          )}
        </div>
      </div>
    </div>
  );
}
