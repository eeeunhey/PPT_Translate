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
    const { filename } = context.params;

    try {
        const response = await fetch(`${NAS_URL}/download/${encodeURIComponent(filename)}`);

        if (!response.ok) {
            return new Response(JSON.stringify({ error: '파일을 찾을 수 없습니다.' }), {
                status: response.status,
                headers: {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                },
            });
        }

        return new Response(response.body, {
            status: 200,
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'Content-Disposition': `attachment; filename="${filename}"`,
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

