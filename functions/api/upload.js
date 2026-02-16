export async function onRequestPost(context) {
    const NAS_URL = 'https://hyehey.synology.me:5113';

    try {
        const request = context.request;
        const contentType = request.headers.get('Content-Type');

        const response = await fetch(`${NAS_URL}/api/upload`, {
            method: 'POST',
            body: request.body,
            headers: {
                'Content-Type': contentType,
            },
        });

        const responseHeaders = new Headers();
        responseHeaders.set('Content-Type', 'application/json');
        responseHeaders.set('Access-Control-Allow-Origin', '*');

        const data = await response.text();

        return new Response(data, {
            status: response.status,
            headers: responseHeaders,
        });
    } catch (err) {
        // 디버깅용 상세 에러 반환
        return new Response(JSON.stringify({
            success: false,
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

// CORS preflight 처리
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
