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

        // 5분 타임아웃 설정 (번역은 시간이 오래 걸릴 수 있음)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5분

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
        // AbortError = 타임아웃
        const isTimeout = err.name === 'AbortError';
        const errorMessage = isTimeout
            ? '번역 처리 시간이 초과되었습니다. 파일 크기를 줄이거나 슬라이드 수를 줄여서 다시 시도해주세요.'
            : '서버 연결 실패';

        return new Response(JSON.stringify({
            success: false,
            error: errorMessage,
            debug: err.message || String(err),
            errorType: isTimeout ? 'TIMEOUT' : 'CONNECTION_ERROR',
        }), {
            status: isTimeout ? 504 : 502,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
        });
    }
}
