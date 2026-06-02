import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.API_INTERNAL_URL || 'http://api:8000';

async function proxy(req: NextRequest): Promise<NextResponse> {
  const targetUrl = `${API_BASE}${req.nextUrl.pathname}${req.nextUrl.search}`;

  const headers: Record<string, string> = {};
  const cookie = req.headers.get('cookie');
  if (cookie) headers['cookie'] = cookie;
  const auth = req.headers.get('authorization');
  if (auth) headers['authorization'] = auth;
  const ct = req.headers.get('content-type');
  if (ct) headers['content-type'] = ct;

  const isBody = !['GET', 'HEAD'].includes(req.method);
  const body = isBody ? await req.arrayBuffer() : null;

  let response: Response;
  try {
    response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: body ?? undefined,
      redirect: 'follow',
    });
  } catch (e) {
    return NextResponse.json({ detail: 'Upstream unavailable' }, { status: 502 });
  }

  const resHeaders = new Headers();
  const setCookie = response.headers.get('set-cookie');
  if (setCookie) resHeaders.set('set-cookie', setCookie);
  const contentType = response.headers.get('content-type');
  if (contentType) resHeaders.set('content-type', contentType);
  const contentDisposition = response.headers.get('content-disposition');
  if (contentDisposition) resHeaders.set('content-disposition', contentDisposition);

  return new NextResponse(response.body, {
    status: response.status,
    headers: resHeaders,
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
