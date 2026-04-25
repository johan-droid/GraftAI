/**
 * useSWR-style data hooks with Neon Postgres via API routes.
 * Handles loading, error, revalidation, and optimistic updates.
 */

import { useState, useEffect, useCallback, useRef } from "react";

// ── Generic Fetcher ────────────────────────────────────────────────────────
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  // SECURITY FIX: Never use localStorage for tokens - vulnerable to XSS
  // Use httpOnly cookies via credentials:include or session-based auth
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> ?? {})
  };

  // Cookies are automatically sent with credentials:include
  // No need to manually add Authorization header from localStorage
  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Sends httpOnly cookies automatically
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({})) as { detail?: string };
    throw new ApiError(res.status, data.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── useQuery ───────────────────────────────────────────────────────────────
export function useQuery<T>(
  url: string | null,
  options?: { initialData?: T; revalidateInterval?: number }
) {
  const [data, setData] = useState<T | undefined>(options?.initialData);
  const [error, setError] = useState<ApiError | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(url !== null);
  const abortRef = useRef<AbortController | null>(null);

  const load = useCallback(async () => {
    if (!url) return;
    abortRef.current?.abort();
    abortRef.current = new AbortController();
    setIsLoading(true);
    setError(null);
    try {
      const result = await fetcher<T>(url, { signal: abortRef.current.signal });
      setData(result);
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setError(err instanceof ApiError ? err : new ApiError(500, (err as Error).message));
      }
    } finally {
      setIsLoading(false);
    }
  }, [url]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!options?.revalidateInterval) return;
    const id = setInterval(load, options.revalidateInterval);
    return () => clearInterval(id);
  }, [load, options?.revalidateInterval]);

  return { data, error, isLoading, refetch: load, setData };
}

// ── useMutation ───────────────────────────────────────────────────────────
export function useMutation<TData, TVars = unknown>(
  mutationFn: (vars: TVars) => Promise<TData>,
  options?: {
    onSuccess?: (data: TData, vars: TVars) => void;
    onError?: (error: ApiError) => void;
  }
) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [data, setData] = useState<TData | null>(null);

  const optionsRef = useRef(options);
  optionsRef.current = options;

  const mutate = useCallback(async (vars: TVars): Promise<TData | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await mutationFn(vars);
      setData(result);
      optionsRef.current?.onSuccess?.(result, vars);
      return result;
    } catch (err) {
      const apiErr = err instanceof ApiError ? err : new ApiError(500, (err as Error).message);
      setError(apiErr);
      optionsRef.current?.onError?.(apiErr);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [mutationFn]);

  return { mutate, isLoading, error, data };
}

// ── Optimistic List Hook ────────────────────────────────────────────────
export function useOptimisticList<T extends { id: number | string }>(initial: T[]) {
  const [items, setItems] = useState<T[]>(initial);

  const add = useCallback((item: T, rollbackFn?: () => void) => {
    setItems(prev => [...prev, item]);
    return () => {
      setItems(prev => prev.filter(i => i.id !== item.id));
      rollbackFn?.();
    };
  }, []);

  const update = useCallback((id: T["id"], patch: Partial<T>) => {
    let old: T | undefined;
    setItems(prev => {
      old = prev.find(i => i.id === id);
      return prev.map(i => i.id === id ? { ...i, ...patch } : i);
    });
    return () => {
      if (old) setItems(prev => prev.map(i => i.id === id ? old! : i));
    };
  }, []);

  const remove = useCallback((id: T["id"] ) => {
    let removed: T | undefined;
    setItems(prev => {
      removed = prev.find(i => i.id === id);
      return prev.filter(i => i.id !== id);
    });
    return () => {
      if (removed) setItems(prev => [...prev, removed!]);
    };
  }, []);

  return { items, setItems, add, update, remove };
}

// ── Debounce ────────────────────────────────────────────────────────────
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

// ── Local Storage ───────────────────────────────────────────────────────
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === "undefined") return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) as T : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback((value: T | ((val: T) => T)) => {
    setStoredValue(prev => {
      const next = typeof value === "function" ? (value as (val: T) => T)(prev) : value;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(key, JSON.stringify(next));
      }
      return next;
    });
  }, [key]);

  return [storedValue, setValue] as const;
}
