export async function onRequest() {
    const NAS_URL = 'https://ppt-translator.hyehey.synology.me';
    const results = {};

    // 1. 기본 연결 테스트 (GET /favicon.ico)
    try {
        const res = await fetch(`${NAS_URL}/favicon.ico`);
        results.favicon = { status: res.status, ok: true };
    } catch (err) {
        results.favicon = { ok: false, error: err.message };
    }

    // 2. GET /api/upload 테스트 (Flask가 405를 반환해야 정상 - POST만 허용)
    try {
        const res = await fetch(`${NAS_URL}/api/upload`);
        const body = await res.text();
        results.get_api_upload = { status: res.status, body: body.substring(0, 300) };
    } catch (err) {
        results.get_api_upload = { error: err.message };
    }

    // 3. POST /api/upload 테스트 (body 없이 - Flask가 400을 반환해야 정상)
    try {
        const res = await fetch(`${NAS_URL}/api/upload`, { method: 'POST' });
        const body = await res.text();
        results.post_api_upload = { status: res.status, body: body.substring(0, 300) };
    } catch (err) {
        results.post_api_upload = { error: err.message };
    }

    // 4. POST /upload 테스트 (/api 없이)
    try {
        const res = await fetch(`${NAS_URL}/upload`, { method: 'POST' });
        const body = await res.text();
        results.post_upload = { status: res.status, body: body.substring(0, 300) };
    } catch (err) {
        results.post_upload = { error: err.message };
    }

    // 5. GET / 테스트 (Flask 루트)
    try {
        const res = await fetch(`${NAS_URL}/`);
        results.root = { status: res.status, contentType: res.headers.get('content-type') };
    } catch (err) {
        results.root = { error: err.message };
    }

    return new Response(JSON.stringify({
        timestamp: new Date().toISOString(),
        nasUrl: NAS_URL,
        tests: results,
    }, null, 2), {
        headers: { 'Content-Type': 'application/json' },
    });
}
