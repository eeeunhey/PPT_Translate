export async function onRequestPost(context) {
    const NAS_URL = 'https://hyehey.synology.me:5113';

    try {
        const response = await fetch(`${NAS_URL}/api/upload`, {
            method: 'POST',
            body: context.request.body,
            headers: {
                'Content-Type': context.request.headers.get('Content-Type'),
            },
        });

        const data = await response.text();

        return new Response(data, {
            status: response.status,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': 'https://ppt-translate.pages.dev',
            },
        });
    } catch (err) {
        return new Response(JSON.stringify({ success: false, error: '서버 연결 실패' }), {
            status: 502,
            headers: { 'Content-Type': 'application/json' },
        });
    }
}

// CORS preflight 처리
export async function onRequestOptions() {
    return new Response(null, {
        headers: {
            'Access-Control-Allow-Origin': 'https://ppt-translate.pages.dev',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '86400',
        },
    });
}
