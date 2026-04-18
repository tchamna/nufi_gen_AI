import { NextRequest, NextResponse } from 'next/server';
import { GetObjectCommand, HeadObjectCommand } from '@aws-sdk/client-s3';
import { getAudioFilename } from '@/data/audioMapping';
import { createBinaryProtectionHeaders, getRequestProtection } from '@/lib/security/protection';
import { createServerS3Client, getDictionaryAudioBucket } from '@/lib/serverS3';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

const bucketName = getDictionaryAudioBucket();
const s3Client = createServerS3Client();

function resolveAudioFilename(rawWord: string) {
  let decodedWord = rawWord;

  try {
    decodedWord = decodeURIComponent(rawWord);
  } catch {
    decodedWord = rawWord;
  }

  // Normalize to NFC so NFD-encoded diacritics (à = a + combining-grave) match
  // the NFC keys stored in audioMapping (à = U+00E0).
  decodedWord = decodedWord.normalize('NFC');

  // Exact-word special cases for 'bà' encoding quirks only
  // (substring includes() was too broad — e.g. 'mbàk' also contains 'bà')
  if (
    decodedWord === 'bÃ ' ||
    decodedWord === 'b\u00e0' ||
    decodedWord === 'ba\u0300'
  ) {
    return 'ba1';
  }

  return getAudioFilename(decodedWord);
}

function withCors(headers?: Headers) {
  const responseHeaders = headers ? new Headers(headers) : new Headers();

  for (const [key, value] of Object.entries(corsHeaders)) {
    responseHeaders.set(key, value);
  }

  return responseHeaders;
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: corsHeaders,
  });
}

export const GET = async (request: NextRequest, { params }: { params: Promise<{ word: string }> }) => {
  const guarded = await getRequestProtection(request, 'audio', {
    requireAuth: true,
    allowAnonymousPreview: false,
  });

  if (guarded.response) {
    return guarded.response;
  }

  const { word } = await params;
  const audioFilename = resolveAudioFilename(word);

  if (!audioFilename) {
    return NextResponse.json(
      { error: 'Audio not found' },
      { status: 404, headers: withCors(createBinaryProtectionHeaders(guarded.context)) }
    );
  }

  const key = `${audioFilename}.mp3`;

  try {
    await s3Client.send(
      new HeadObjectCommand({
        Bucket: bucketName,
        Key: key,
      })
    );
  } catch (error: any) {
    const status = error?.name === 'NotFound' || error?.$metadata?.httpStatusCode === 404 ? 404 : 500;
    const message = status === 404 ? 'Audio file not found' : 'Error checking audio file';

    return NextResponse.json(
      { error: message },
      { status, headers: withCors(createBinaryProtectionHeaders(guarded.context)) }
    );
  }

  try {
    const { Body } = await s3Client.send(
      new GetObjectCommand({
        Bucket: bucketName,
        Key: key,
      })
    );

    if (!Body) {
      return NextResponse.json(
        { error: 'Empty audio file' },
        { status: 500, headers: withCors(createBinaryProtectionHeaders(guarded.context)) }
      );
    }

    const chunks: Uint8Array[] = [];
    for await (const chunk of Body as AsyncIterable<Uint8Array>) {
      chunks.push(chunk);
    }

    const buffer = Buffer.concat(chunks);
    const headers = withCors(createBinaryProtectionHeaders(guarded.context));
    headers.set('Content-Type', 'audio/mpeg');
    headers.set('Content-Length', buffer.length.toString());
    headers.set('Cache-Control', 'private, max-age=3600');
    headers.set('Accept-Ranges', 'bytes');

    return new NextResponse(buffer, {
      status: 200,
      headers,
    });
  } catch (error: any) {
    return NextResponse.json(
      {
        error: 'Error retrieving audio file from storage',
        details: {
          errorType: error?.name ?? 'unknown',
          errorCode: error?.$metadata?.httpStatusCode ?? 'unknown',
        },
      },
      { status: 500, headers: withCors(createBinaryProtectionHeaders(guarded.context)) }
    );
  }
};

export const HEAD = async (request: NextRequest, { params }: { params: Promise<{ word: string }> }) => {
  const guarded = await getRequestProtection(request, 'audio', {
    requireAuth: true,
    allowAnonymousPreview: false,
  });

  if (guarded.response) {
    return guarded.response;
  }

  const { word } = await params;
  const audioFilename = resolveAudioFilename(word);

  if (!audioFilename) {
    return new NextResponse(null, {
      status: 404,
      headers: withCors(createBinaryProtectionHeaders(guarded.context)),
    });
  }

  try {
    await s3Client.send(
      new HeadObjectCommand({
        Bucket: bucketName,
        Key: `${audioFilename}.mp3`,
      })
    );

    const headers = withCors(createBinaryProtectionHeaders(guarded.context));
    headers.set('Content-Type', 'audio/mpeg');
    headers.set('Cache-Control', 'private, max-age=3600');

    return new NextResponse(null, {
      status: 200,
      headers,
    });
  } catch {
    return new NextResponse(null, {
      status: 404,
      headers: withCors(createBinaryProtectionHeaders(guarded.context)),
    });
  }
};
