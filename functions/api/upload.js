export async function onRequest(context) {
    // CORS preflight 처리
    if (context.request.method === 'OPTIONS') {
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

    // POST 이외 메서드 거부
    if (context.request.method !== 'POST') {
        return new Response(JSON.stringify({ error: 'Method not allowed' }), {
            status: 405,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    }

    const NAS_URL = 'https://ppt-translator.hyehey.synology.me';

    try {
        // 요청 본문을 ArrayBuffer로 완전히 읽은 후 전달
        const body = await context.request.arrayBuffer();
        const contentType = context.request.headers.get('Content-Type');

        // 30초 타임아웃 (비동기 처리이므로 업로드만 하면 즉시 응답)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const response = await fetch(`${NAS_URL}/upload`, {
            method: 'POST',
            body: body,
            headers: {
                'Content-Type': contentType,
            },
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        const data = await response.text();

        return new Response(data, {
            status: response.status,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    } catch (err) {
        const isTimeout = err.name === 'AbortError';

        return new Response(JSON.stringify({
            success: false,
            error: isTimeout
                ? '파일 업로드 시간이 초과되었습니다. 파일 크기를 확인해주세요.'
                : '서버 연결 실패',
            debug: err.message || String(err),
        }), {
            status: isTimeout ? 504 : 502,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    }
}
