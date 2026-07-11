import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ApiError, apiClient } from "../../api/client";

export function CloneRepositoryForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const cloneMutation = useMutation({
    mutationFn: apiClient.cloneRepository,
    onSuccess: (repository) => {
      void queryClient.invalidateQueries({ queryKey: ["repositories"] });
      setUrl("");
      setBranch("");
      setError(null);
      navigate(`/repositories/${repository.id}`);
    },
    onError: (err) => {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to clone repository.");
      }
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    cloneMutation.mutate({
      url: url.trim(),
      branch: branch.trim() || undefined,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900"
    >
      <h3 className="text-lg font-semibold">Add GitHub Repository</h3>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
        Paste a public GitHub URL or use owner/repository format.
      </p>

      {error && (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="mt-4 grid gap-4 md:grid-cols-[2fr_1fr_auto]">
        <div>
          <label
            htmlFor="repo-url"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Repository URL
          </label>
          <input
            id="repo-url"
            type="text"
            required
            placeholder="https://github.com/owner/repo or owner/repo"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-950"
          />
        </div>
        <div>
          <label
            htmlFor="repo-branch"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Branch (optional)
          </label>
          <input
            id="repo-branch"
            type="text"
            placeholder="main"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            className="mt-1 block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm dark:border-gray-700 dark:bg-gray-950"
          />
        </div>
        <div className="flex items-end">
          <button
            type="submit"
            disabled={cloneMutation.isPending}
            className="w-full rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50 md:w-auto"
          >
            {cloneMutation.isPending ? "Cloning..." : "Clone repository"}
          </button>
        </div>
      </div>
    </form>
  );
}
