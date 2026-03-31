export const GET = async () => {
    console.log("TEST GET CALLED");
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
};

export const POST = async () => {
    console.log("TEST POST CALLED");
    return new Response(JSON.stringify({ ok: true }), { status: 200 });
};
