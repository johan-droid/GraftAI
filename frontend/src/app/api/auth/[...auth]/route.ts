import { auth } from "@/lib/auth-server";
import { toNextJsHandler } from "better-auth/next-js";

const handler = toNextJsHandler(auth);

export const GET = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_GET]: ${url.pathname}${url.search}`);
    try {
        const res = await handler.GET(req);
        if (res.status >= 400) {
            console.error(`[AUTH_GET_ERROR] Status: ${res.status} | URL: ${url.pathname}`);
        }
        return res;
    } catch (e) {
        console.error("[AUTH_GET_CRASH]:", e instanceof Error ? {
            message: e.message,
            stack: e.stack,
            cause: e.cause
        } : e);
        // Expose error details temporarily to debug production
        return new Response(JSON.stringify({
            error: "Authentication server error",
            details: String(e),
            stack: e instanceof Error ? e.stack?.split("\n").slice(0, 3) : null,
            requestPath: url.pathname,
            requestQuery: url.search
        }), { status: 500, headers: { "Content-Type": "application/json" } });
    }
};

export const POST = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_POST]: ${url.pathname}`);
    try {
        const bodyText = await req.text().catch(() => "");
        if (bodyText) console.log(`[AUTH_POST_BODY]: ${bodyText}`);

        const res = await handler.POST(req);
        if (res.status >= 400) {
            console.error(`[AUTH_POST_ERROR] Status: ${res.status} | URL: ${url.pathname}`);
        }
        return res;
    } catch (e) {
        console.error("[AUTH_POST_CRASH]:", e instanceof Error ? {
            message: e.message,
            stack: e.stack,
            cause: e.cause
        } : e);
        // Expose error details temporarily to debug production
        return new Response(JSON.stringify({
            error: "Authentication server error",
            details: String(e),
            stack: e instanceof Error ? e.stack?.split("\n").slice(0, 3) : null,
            requestPath: url.pathname,
            requestBody: bodyText
        }), { status: 500, headers: { "Content-Type": "application/json" } });
    }
};
