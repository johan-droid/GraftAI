import { NextResponse } from "next/server";

/**
 * Health check endpoint for the frontend application.
 * This provides a local health check that doesn't depend on the backend.
 */
export async function GET() {
    const healthStatus = {
        status: "ok",
        service: "graft-ai-frontend",
        timestamp: new Date().toISOString(),
        checks: {
            server: true,
            environment: process.env.NODE_ENV || "development",
        }
    };

    return NextResponse.json(healthStatus);
}
