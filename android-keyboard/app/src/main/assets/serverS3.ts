import { S3Client } from '@aws-sdk/client-s3';

const DEFAULT_REGION = 'us-east-1';
const DEFAULT_DICTIONARY_BUCKET = 'dictionnaire-nufi-audio';
const DEFAULT_PHRASEBOOK_BUCKET = 'phrasebook-audio-files';
const DEFAULT_DICTIONARY_IMAGE_BUCKET = 'resulam-images';
const DEFAULT_DICTIONARY_IMAGE_PREFIX = 'dictionary-images/';

export function createServerS3Client() {
  const region = process.env.AWS_REGION?.trim() || DEFAULT_REGION;
  const accessKeyId = process.env.AWS_ACCESS_KEY_ID?.trim();
  const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY?.trim();

  if (accessKeyId && secretAccessKey) {
    return new S3Client({
      region,
      credentials: {
        accessKeyId,
        secretAccessKey,
      },
    });
  }

  if (process.env.NODE_ENV === 'production') {
    console.warn(
      '[serverS3] AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are not set. S3 (dictionary images, audio) will fail on hosts without instance credentials (e.g. Azure App Service). Set these variables to match your IAM user or role.'
    );
  }

  return new S3Client({ region });
}

export function getAwsRegion() {
  return process.env.AWS_REGION?.trim() || DEFAULT_REGION;
}

export function getDictionaryAudioBucket() {
  return process.env.S3_BUCKET_NAME?.trim() || DEFAULT_DICTIONARY_BUCKET;
}

export function getPhrasebookAudioBucket() {
  return process.env.PHRASEBOOK_AUDIO_BUCKET_NAME?.trim() || DEFAULT_PHRASEBOOK_BUCKET;
}

export function getDictionaryImageBucket() {
  return process.env.DICTIONARY_IMAGE_BUCKET_NAME?.trim() || DEFAULT_DICTIONARY_IMAGE_BUCKET;
}

export function getDictionaryImagePrefix() {
  const raw = (process.env.DICTIONARY_IMAGE_PREFIX ?? DEFAULT_DICTIONARY_IMAGE_PREFIX).trim();
  return raw.endsWith('/') ? raw : `${raw}/`;
}
