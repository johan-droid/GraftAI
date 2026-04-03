import { auth } from "@/lib/auth-server";
import { toNextJsHandler } from "better-auth/next-js";

const handler = toNextJsHandler(auth);

export const GET = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_GET]: ${url.pathname}${url.search}`);
    try {
        const res = await handler.GET(req);
        if (res.status >= 400) {
            console.error(`[AUTH_GET_ERROR] Status: ${res.status}`);
        }
        return res;
    } catch (e) {
        console.error("[AUTH_GET_CRASH]:", e);
        throw e;
    }
};

export const POST = async (req: Request) => {
    const url = new URL(req.url);
    console.log(`[AUTH_POST]: ${url.pathname}`);
    try {
        const res = await handler.POST(req);
        if (res.status >= 400) {
            console.error(`[AUTH_POST_ERROR] Status: ${res.status}`);
        }
        return res;
    } catch (e) {
        console.error("[AUTH_POST_CRASH]:", e);
        throw e;
    }
};
