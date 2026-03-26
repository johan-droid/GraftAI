const { betterAuth } = require("better-auth");
const { Pool } = require("pg");
require("dotenv").config({ path: "./frontend/.env.local" });

async function testAuth() {
    console.log("Initializing Better Auth...");
    const auth = betterAuth({
        database: new Pool({
            connectionString: process.env.DATABASE_URL,
            ssl: { rejectUnauthorized: false }
        }),
        emailAndPassword: { enabled: true },
        user: { modelName: "users" }
    });

    try {
        console.log("Fetching users count...");
        // This is a internal way to test DB connectivity through Better Auth's adapter
        const db = auth.database;
        const users = await db.findMany({ model: "user" });
        console.log(`Found ${users.length} users.`);
        
        console.log("Testing a mock sign-in (this should fail but show us where)...");
        // We can't easily call the internal handler here without a request object,
        // but we can try to use the adapter to insert a dummy session.
        const session = await db.create({
            model: "session",
            data: {
                id: "test-session-id",
                userId: "test-user-id",
                token: "test-token",
                expiresAt: new Date(Date.now() + 3600),
                userAgent: "test",
                ipAddress: "127.0.0.1",
                createdAt: new Date(),
                updatedAt: new Date()
            }
        });
        console.log("Mock session created:", session);
    } catch (err) {
        console.error("DETECTED ERROR:", err);
    }
}

testAuth();
