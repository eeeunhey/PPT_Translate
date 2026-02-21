export async function onRequest(context) {
    // CORS preflight 처리
    if (context.request.method === 'OPTIONS') {
        return new Response(null, {
            status: 204,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
        });
    }

    const NAS_URL = 'https://ppt-translator.hyehey.synology.me';
    const { jobId } = context.params;

    try {
        const response = await fetch(`${NAS_URL}/api/status/${jobId}`);
        const data = await response.text();

        return new Response(data, {
            status: response.status,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    } catch (err) {
        return new Response(JSON.stringify({
            error: '서버 연결 실패',
            debug: err.message || String(err),
        }), {
            status: 502,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    }
}
