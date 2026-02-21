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

        // 바이너리 데이터를 완전히 읽은 후 전달 (스트리밍 대신 arrayBuffer 사용)
        // → PPT 파일 손상 방지
        const fileData = await response.arrayBuffer();

        return new Response(fileData, {
            status: 200,
            headers: {
                'Content-Type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                'Content-Disposition': `attachment; filename="${encodeURIComponent(filename)}"`,
                'Content-Length': fileData.byteLength.toString(),
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache',
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
