"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // Our backend expects a standard JSON payload for registration
      await apiClient.fetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          full_name: fullName,
          email: email,
          password: password,
        }),
      });

      // Show success and redirect to login
      alert("Registration successful! Please log in.");
      router.push("/login");
      
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to register. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <form onSubmit={handleRegister} className="w-full max-w-md bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">Create an Account</h2>
        
        {error && <div className="mb-4 text-red-500 text-sm text-center font-medium bg-red-50 p-2 rounded border border-red-100">{error}</div>}
        
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1 text-gray-700">Full Name</label>
          <input 
            type="text" 
            required
            placeholder="John Doe"
            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800"
            value={fullName} 
            onChange={(e) => setFullName(e.target.value)}
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1 text-gray-700">Email Address</label>
          <input 
            type="email" 
            required
            placeholder="example@mail.com"
            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800"
            value={email} 
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        
        <div className="mb-6">
          <label className="block text-sm font-medium mb-1 text-gray-700">Password</label>
          <input 
            type="password" 
            required
            minLength={6}
            placeholder="At least 6 characters"
            className="w-full border p-2 rounded focus:ring-2 focus:ring-blue-500 outline-none text-gray-800"
            value={password} 
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        
        <button 
          type="submit" 
          disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded font-semibold hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Creating account..." : "Register"}
        </button>

        <div className="mt-4 text-center text-sm text-gray-600">
          Already have an account?{" "}
          <Link href="/login" className="text-blue-600 font-medium hover:underline">
            Log in here
          </Link>
        </div>
      </form>
    </div>
  );
}
