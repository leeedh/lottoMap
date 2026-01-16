import fs from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';

function getArg(name, defaultValue = undefined) {
  const prefix = `--${name}=`;
  const hit = process.argv.find((a) => a.startsWith(prefix));
  if (!hit) return defaultValue;
  return hit.slice(prefix.length);
}

function hasFlag(name) {
  return process.argv.includes(`--${name}`);
}

function getSetCookies(res) {
  // Node fetch (undici) on newer Node has headers.getSetCookie()
  if (typeof res.headers.getSetCookie === 'function') return res.headers.getSetCookie();
  const single = res.headers.get('set-cookie');
  if (!single) return [];
  // best-effort: split on comma that starts a new cookie (naive but ok for JSESSIONID-type)
  return single.split(/,(?=[^;]+=[^;]+)/g).map((s) => s.trim());
}

function buildCookieHeader(setCookies) {
  // "a=b; Path=/; HttpOnly" -> "a=b"
  return setCookies
    .map((c) => c.split(';')[0].trim())
    .filter(Boolean)
    .join('; ');
}

async function fetchJsonWithHomeCookie({ apiUrl, timeoutMs }) {
  const controller = new AbortController();
  const t = setTimeout(() => controller.abort(), timeoutMs);
  try {
    // 1) 홈을 먼저 호출해서 세션/쿠키 확보
    const homeRes = await fetch('https://dhlottery.co.kr/wnprchsplcsrch/home', {
      method: 'GET',
      redirect: 'follow',
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      },
      signal: controller.signal,
    });
    const homeSetCookies = getSetCookies(homeRes);
    const cookie = buildCookieHeader(homeSetCookies);

    // 2) 같은 세션 쿠키를 붙여 API 호출
    const apiRes = await fetch(apiUrl, {
      method: 'GET',
      redirect: 'follow',
      headers: {
        'User-Agent':
          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        Referer: 'https://dhlottery.co.kr/wnprchsplcsrch/home',
        'X-Requested-With': 'XMLHttpRequest',
        Accept: 'application/json, text/javascript, */*; q=0.01',
        ...(cookie ? { Cookie: cookie } : {}),
      },
      signal: controller.signal,
    });

    const text = await apiRes.text();
    let json = null;
    try {
      json = JSON.parse(text);
    } catch {
      // ignore
    }

    return {
      mode: 'node-fetch-with-cookie',
      home: {
        ok: homeRes.ok,
        status: homeRes.status,
        setCookieCount: homeSetCookies.length,
      },
      api: {
        ok: apiRes.ok,
        status: apiRes.status,
        contentType: apiRes.headers.get('content-type'),
        url: apiRes.url,
      },
      json,
      textPreview: text.slice(0, 500),
    };
  } finally {
    clearTimeout(t);
  }
}

async function fetchJsonViaPlaywright({ apiUrl, timeoutMs, headed }) {
  let chromium;
  try {
    ({ chromium } = await import('playwright'));
  } catch (e) {
    return {
      mode: 'playwright-missing',
      error:
        "Playwright가 설치되어 있지 않습니다. (선택) `pnpm add -D playwright` 후 다시 실행하거나, node-fetch 모드 결과를 확인하세요.",
      details: String(e?.message ?? e),
    };
  }

  const browser = await chromium.launch({ headless: !headed });
  const context = await browser.newContext({
    locale: 'ko-KR',
    userAgent:
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  try {
    await page.goto('https://dhlottery.co.kr/wnprchsplcsrch/home', {
      waitUntil: 'domcontentloaded',
      timeout: timeoutMs,
    });

    const result = await page.evaluate(async (url) => {
      const res = await fetch(url, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          Accept: 'application/json, text/javascript, */*; q=0.01',
        },
      });
      const text = await res.text();
      let json = null;
      try {
        json = JSON.parse(text);
      } catch {
        // ignore
      }
      return {
        ok: res.ok,
        status: res.status,
        contentType: res.headers.get('content-type'),
        url: res.url,
        json,
        textPreview: text.slice(0, 500),
      };
    }, apiUrl);

    return { mode: 'playwright', ...result };
  } finally {
    await page.close().catch(() => {});
    await context.close().catch(() => {});
    await browser.close().catch(() => {});
  }
}

async function main() {
  const round = getArg('round');
  const rank = getArg('rank', 'all'); // all | 1 | 2 | 21(bonus, pt720 only)
  const region = getArg('region', ''); // empty = 전국
  const out = getArg('out', '');
  const headed = hasFlag('headed');
  const timeoutMs = Number(getArg('timeoutMs', '60000'));
  const mode = getArg('mode', 'auto'); // auto | node | playwright

  if (!round) {
    console.error('Missing required arg: --round=#### (e.g. --round=1206)');
    process.exitCode = 2;
    return;
  }

  const apiUrl =
    `https://dhlottery.co.kr/wnprchsplcsrch/selectLtWnShp.do` +
    `?srchWnShpRnk=${encodeURIComponent(rank)}` +
    `&srchLtEpsd=${encodeURIComponent(round)}` +
    `&srchShpLctn=${encodeURIComponent(region)}`;

  let result;
  if (mode === 'node') {
    result = await fetchJsonWithHomeCookie({ apiUrl, timeoutMs });
  } else if (mode === 'playwright') {
    result = await fetchJsonViaPlaywright({ apiUrl, timeoutMs, headed });
  } else {
    // auto: 먼저 node 방식으로 시도 → 실패/비JSON이면 playwright 안내
    const nodeResult = await fetchJsonWithHomeCookie({ apiUrl, timeoutMs });
    const nodeLooksJson = !!nodeResult.json;
    const nodeOk = nodeResult?.api?.ok === true;
    result = nodeResult;

    if (!nodeOk || !nodeLooksJson) {
      result = {
        ...nodeResult,
        hint:
          'node-fetch-with-cookie로 JSON 응답이 안 나오면, 브라우저에서만 허용되는 차단(WAF)일 가능성이 큽니다. 이 경우 Playwright 모드로 재시도하세요: `pnpm add -D playwright` 후 `pnpm crawl:winning-stores -- --mode=playwright --round=...`',
      };
    }
  }

  if (!out) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  const outPath = path.isAbsolute(out) ? out : path.join(process.cwd(), out);
  await fs.mkdir(path.dirname(outPath), { recursive: true });
  await fs.writeFile(outPath, JSON.stringify(result, null, 2), 'utf8');
  console.log(`Saved: ${outPath}`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});


