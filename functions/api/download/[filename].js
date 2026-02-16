export async function onRequestGet(context) {
    const NAS_URL = 'https://hyehey.synology.me:5113';
    const { filename } = context.params;

    try {
        const response = await fetch(`${NAS_URL}/api/download/${encodeURIComponent(filename)}`);

        if (!response.ok) {
            return new Response(JSON.stringify({ error: '파일을 찾을 수 없습니다.' }), {
                status: response.status,
                headers: { 'Content-Type': 'application/json' },
            });
        }

        return new Response(response.body, {
            status: 200,
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'Content-Disposition': `attachment; filename="${filename}"`,
                'Access-Control-Allow-Origin': 'https://ppt-translate.pages.dev',
            },
        });
    } catch (err) {
        return new Response(JSON.stringify({ error: '서버 연결 실패' }), {
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
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        },
    });
}
