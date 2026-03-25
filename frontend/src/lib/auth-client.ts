'use client';

// Try importing everything from the main entry point if submodules fail
import { createAuthClient } from '@neondatabase/auth';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_BACKEND_URL ||
  "http://localhost:8000";

// Use the standard client which exposes sign-in/out and session operations
export const authClient = createAuthClient(API_BASE_URL);

export const signIn = authClient.signIn;
export const signOut = authClient.signOut;
export const getSession = authClient.getSession;

// fallback for hooks for derived providers; we do not rely on useSession from authClient directly
const authClientWithHooks = authClient as { useSession?: unknown };
export const useSession = typeof authClientWithHooks.useSession === 'function' ? (authClientWithHooks.useSession as () => unknown) : undefined;

