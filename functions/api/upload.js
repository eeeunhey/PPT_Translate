export async function onRequestPost(context) {
    const NAS_URL = 'https://ppt-translator.hyehey.synology.me';

    try {
        // 요청 본문을 ArrayBuffer로 완전히 읽은 후 전달
        const body = await context.request.arrayBuffer();
        const contentType = context.request.headers.get('Content-Type');

        const response = await fetch(`${NAS_URL}/api/upload`, {
            method: 'POST',
            body: body,
            headers: {
                'Content-Type': contentType,
            },
        });

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
            success: false,
            error: '서버 연결 실패',
            debug: err.message || String(err),
            stack: err.stack || '',
        }), {
            status: 502,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    }
}

// CORS preflight
export async function onRequestOptions() {
    return new Response(null, {
        status: 204,
        headers: {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '86400',
        },
    });
}
