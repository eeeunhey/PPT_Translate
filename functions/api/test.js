export async function onRequest() {
    const NAS_URL = 'https://hyehey.synology.me:5113';
    let nasStatus = 'unknown';
    let nasError = null;

    try {
        const res = await fetch(`${NAS_URL}/favicon.ico`);
        nasStatus = `reachable (HTTP ${res.status})`;
    } catch (err) {
        nasStatus = 'unreachable';
        nasError = err.message || String(err);
    }

    return new Response(JSON.stringify({
        functions: 'working',
        timestamp: new Date().toISOString(),
        nas: nasStatus,
        nasError: nasError,
    }, null, 2), {
        headers: { 'Content-Type': 'application/json' },
    });
}
