import { useTheme } from "../hooks/useTheme";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();

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
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Additional settings (Ollama endpoint, model, file size limits) will be
          available in a future release.
        </p>
      </div>
    </div>
  );
}
