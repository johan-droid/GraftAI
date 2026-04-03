import { auth } from "@/lib/auth-server";
import { toNextJsHandler } from "better-auth/next-js";

const handler = toNextJsHandler(auth);

export const GET = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_GET]: ${url.pathname}${url.search}`);

    try {
        const res = await handler.GET(req);

        if (res.status >= 400) {
            const errorText = await res.text();
            console.error(`[AUTH_GET_ERROR] Status: ${res.status}`, errorText);
        }

        return res;
    } catch (e) {
        console.error("[AUTH_GET_CRASH]:", e);

        return new Response(
            JSON.stringify({
                error: "Authentication service temporarily unavailable",
                message:
                    process.env.NODE_ENV === "development"
                        ? String(e)
                        : "Please try again later",
                status: 500,
            }),
            { status: 500, headers: { "Content-Type": "application/json" } }
        );
    }
};

export const POST = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_POST]: ${url.pathname}`);

    try {
        const requestToLog = req.clone();
        const bodyText = await requestToLog.text().catch(() => "");
        if (bodyText) console.log(`[AUTH_POST_BODY]: ${bodyText}`);

        const res = await handler.POST(req);

        if (res.status >= 400) {
            const errorText = await res.text();
            console.error(`[AUTH_POST_ERROR] Status: ${res.status}`, errorText);
        }

        return res;
    } catch (e) {
        console.error("[AUTH_POST_CRASH]:", e);

        return new Response(
            JSON.stringify({
                error: "Authentication service temporarily unavailable",
                message:
                    process.env.NODE_ENV === "development"
                        ? String(e)
                        : "Please try again later",
                status: 500,
            }),
            { status: 500, headers: { "Content-Type": "application/json" } }
        );
    }
};
