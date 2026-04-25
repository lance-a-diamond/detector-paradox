import HTML from '../public/index.html';

const CLOSED_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Study Closed</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    background: #f5f5f7;
    color: #1d1d1f;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 2rem;
  }
  .card {
    background: #fff;
    border-radius: 16px;
    padding: 3rem 2.5rem;
    max-width: 520px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  }
  h1 { font-size: 1.6rem; font-weight: 700; margin-bottom: 1rem; }
  p { color: #6e6e73; line-height: 1.7; margin-bottom: 0.75rem; }
  .icon { font-size: 2.5rem; margin-bottom: 1rem; }
</style>
</head>
<body>
<div class="card">
  <div class="icon">\u2705</div>
  <h1>Study Closed</h1>
  <p>This study has reached its target number of participants and is no longer accepting responses.</p>
  <p>Thank you for your interest in this research.</p>
</div>
</body>
</html>`;

const COUNT_KEY = 'meta:submission_count';

async function getCount(env) {
  const val = await env.STUDY_RESPONSES.get(COUNT_KEY);
  return val ? parseInt(val, 10) : 0;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const maxResp = parseInt(env.MAX_RESPONSES || '30', 10);

    // Serve survey page (or closed page)
    if ((url.pathname === '/' || url.pathname === '') && request.method === 'GET') {
      const count = await getCount(env);
      if (count >= maxResp) {
        return new Response(CLOSED_HTML, {
          headers: { 'Content-Type': 'text/html; charset=utf-8' },
        });
      }
      const configScript = `<script>window.PROLIFIC_COMPLETION_URL = ${JSON.stringify(env.PROLIFIC_COMPLETION_URL || '')};</script>`;
      const pageHtml = HTML.replace('<!--PROLIFIC_CONFIG-->', configScript);
      return new Response(pageHtml, {
        headers: {
          'Content-Type': 'text/html; charset=utf-8',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'X-Robots-Tag': 'noindex, nofollow, noarchive',
        },
      });
    }

    // Submit response
    if (url.pathname === '/api/submit' && request.method === 'POST') {
      try {
        // Check cap before accepting
        const count = await getCount(env);
        if (count >= maxResp) {
          return Response.json(
            { ok: false, error: 'Study has reached its maximum number of participants.' },
            { status: 403 },
          );
        }

        const data = await request.json();
        const key = 'response:' + Date.now() + ':' + crypto.randomUUID();
        const enriched = {
          ...data,
          _meta: {
            key,
            submittedAt: new Date().toISOString(),
            ip: request.headers.get('CF-Connecting-IP') || 'unknown',
            country: request.headers.get('CF-IPCountry') || 'unknown',
            ua: request.headers.get('User-Agent') || 'unknown',
            responseNumber: count + 1,
          },
        };
        await env.STUDY_RESPONSES.put(key, JSON.stringify(enriched));

        // Increment counter
        await env.STUDY_RESPONSES.put(COUNT_KEY, String(count + 1));

        return Response.json({ ok: true, key, responseNumber: count + 1 });
      } catch (e) {
        return Response.json({ ok: false, error: e.message }, { status: 400 });
      }
    }

    // Get results (password protected)
    if (url.pathname === '/api/results' && request.method === 'GET') {
      const pw = url.searchParams.get('pw');
      if (pw !== env.ADMIN_PW) {
        return new Response('Unauthorized', { status: 401 });
      }
      const allResults = [];
      let cursor = null;
      do {
        const list = await env.STUDY_RESPONSES.list({
          prefix: 'response:',
          cursor,
        });
        for (const item of list.keys) {
          const val = await env.STUDY_RESPONSES.get(item.name);
          if (val) allResults.push(JSON.parse(val));
        }
        cursor = list.list_complete ? null : list.cursor;
      } while (cursor);

      const count = await getCount(env);
      return Response.json({
        count: allResults.length,
        submissionCounter: count,
        maxResponses: maxResp,
        closed: count >= maxResp,
        responses: allResults,
      });
    }

    // Robots — no indexing
    if (url.pathname === '/robots.txt') {
      return new Response('User-agent: *\nDisallow: /', {
        headers: { 'Content-Type': 'text/plain' },
      });
    }

    if (url.pathname === '/favicon.ico') {
      return new Response(null, { status: 204 });
    }

    return new Response('Not Found', { status: 404 });
  },
};
