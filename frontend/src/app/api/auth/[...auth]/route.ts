import { NextResponse } from "next/server";

async function handleNotImplemented() {
  return NextResponse.json(
    { detail: "Better Auth routes are disabled. Use backend /auth APIs directly." },
    { status: 404 }
  );
}

export async function GET() {
  return handleNotImplemented();
}

export async function POST() {
  return handleNotImplemented();
}

export async function PUT() {
  return handleNotImplemented();
}

export async function DELETE() {
  return handleNotImplemented();
}
