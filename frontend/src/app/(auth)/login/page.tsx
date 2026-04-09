"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // FastAPI's OAuth2 expects form-urlencoded data, not JSON
      const formData = new URLSearchParams();
      formData.append("username", email); // standard OAuth2 uses 'username' for email
      formData.append("password", password);

      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!response.ok) throw new Error("Invalid credentials");

      const data = await response.json();
      
      // Save the JWT token!
      localStorage.setItem("token", data.access_token);
      
      // Redirect to the dashboard
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="w-full max-w-md bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Login to GraftAI</h2>
        
        {error && <div className="mb-4 text-red-500 text-sm text-center font-medium bg-red-50 p-2 rounded border border-red-100">{error}</div>}
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1 text-gray-700">Email Address</label>
          <input 
            type="email" required
            placeholder="example@mail.com"
            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800"
            value={email} onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1 text-gray-700">Password</label>
          <input 
            type="password" required
            placeholder="••••••••"
            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800"
            value={password} onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        
        <button 
          type="submit" disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded font-semibold hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Logging in..." : "Login"}
        </button>

        <div className="mt-6 text-center text-sm text-gray-500">or continue with</div>

        <div className="mt-4 grid gap-3">
          <button
            type="button"
            onClick={() => (window.location.href = `${API_URL}/auth/google/login`)}
            className="w-full inline-flex items-center justify-center gap-2 rounded border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            Continue with Google
          </button>
          <button
            type="button"
            onClick={() => (window.location.href = `${API_URL}/auth/microsoft/login`)}
            className="w-full inline-flex items-center justify-center gap-2 rounded border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 transition"
          >
            Continue with Microsoft
          </button>
        </div>

        <div className="mt-4 text-center text-sm text-gray-600">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-blue-600 font-medium hover:underline">
            Register here
          </Link>
        </div>
      </form>
    </div>
  );
}