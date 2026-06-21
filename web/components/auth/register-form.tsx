"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { registerUser, setAccessToken } from "../../lib/auth-api";

export function RegisterForm() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [workspaceName, setWorkspaceName] = useState("My Workspace");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await registerUser({
        email,
        password,
        display_name: displayName || undefined,
        workspace_name: workspaceName || undefined,
      });

      setAccessToken(response.access_token);

      if (response.default_workspace_id) {
        router.push(`/workspaces/${response.default_workspace_id}`);
      } else {
        router.push("/");
      }
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Registration failed.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-6">
      <form
        onSubmit={(event) => void submit(event)}
        className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl"
      >
        <h1 className="text-2xl font-bold text-slate-950">Create account</h1>
        <p className="mt-2 text-sm text-slate-500">
          Create your first workspace.
        </p>

        <label className="mt-6 block text-sm font-medium text-slate-700">
          Email
          <input
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            type="email"
            className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-2"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Display name
          <input
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-2"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Workspace name
          <input
            value={workspaceName}
            onChange={(event) => setWorkspaceName(event.target.value)}
            className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-2"
          />
        </label>

        <label className="mt-4 block text-sm font-medium text-slate-700">
          Password
          <input
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            type="password"
            className="mt-2 w-full rounded-lg border border-slate-300 px-4 py-2"
          />
        </label>

        {errorMessage && (
          <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errorMessage}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-6 w-full rounded-lg bg-slate-950 px-4 py-3 text-sm font-medium text-white disabled:opacity-50"
        >
          {isSubmitting ? "Creating..." : "Create account"}
        </button>
      </form>
    </main>
  );
}
