import { useAuth } from "../hooks/useAuth";

export function ProfilePage() {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div>
      <h2 className="text-2xl font-bold">Profile</h2>
      <p className="mt-2 text-gray-600 dark:text-gray-400">
        Manage your account information and preferences.
      </p>

      <div className="mt-8 max-w-lg space-y-6">
        <div className="rounded-xl border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900">
          <dl className="space-y-4 text-sm">
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">
                Full name
              </dt>
              <dd className="mt-1 text-gray-900 dark:text-gray-100">
                {user.full_name ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">
                Email
              </dt>
              <dd className="mt-1 text-gray-900 dark:text-gray-100">
                {user.email}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">
                Status
              </dt>
              <dd className="mt-1 text-gray-900 dark:text-gray-100">
                {user.is_active ? "Active" : "Inactive"}
              </dd>
            </div>
            <div>
              <dt className="font-medium text-gray-500 dark:text-gray-400">
                User ID
              </dt>
              <dd className="mt-1 font-mono text-xs text-gray-700 dark:text-gray-300">
                {user.id}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}
