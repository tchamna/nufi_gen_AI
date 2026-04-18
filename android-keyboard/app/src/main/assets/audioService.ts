import { getAudioFilename } from '@/data/audioMapping';
import { audioMapping } from '@/data/audioMapping';

/**
 * Get a URL for an audio file using our API proxy
 * @param key The key (path) of the audio file in the S3 bucket
 * @returns A promise that resolves to the API URL
 */
export async function getAudioUrl(key: string): Promise<string> {
  try {
    // Extract the filename from the key (remove '.mp3' suffix if present)
    let filename = key;
    if (filename.endsWith('.mp3')) {
      filename = filename.slice(0, -4);
    }
    
    // Use our API route instead of direct S3 access to avoid CORS issues
    // The API route expects just the filename without extension
    return `/api/audio/${encodeURIComponent(filename)}`;
  } catch (error) {
    console.error('Error generating audio URL:', error);
    throw error;
  }
}

/**
 * Construct the S3 key for a word's audio file
 * @param word The word to get audio for
 * @returns The S3 key for the audio file or null if no mapping exists
 */
export function getAudioKeyForWord(word: string): string | null {
  const cleanedWord = word.toLowerCase().trim();
  
  // Check if we have a mapping for this word
  const audioFilename = getAudioFilename(cleanedWord);
  if (audioFilename) {
    // Audio files are in the root of the bucket
    return `${audioFilename}.mp3`;
  }
  
  // If no mapping exists, return null instead of a fallback
  // This ensures we don't try to access non-existent files
  return null;
}

/**
 * Check if audio exists for a word using our API proxy
 * @param word The word to check audio for
 * @returns A promise that resolves to true if audio exists, false otherwise
 */
export async function checkAudioExists(word: string): Promise<boolean> {
  try {
    const cleanedWord = word.toLowerCase().trim();
    
    // Use our API route with HEAD request to check if audio exists
    const response = await fetch(`/api/audio/${encodeURIComponent(cleanedWord)}`, {
      method: 'HEAD',
    });
    
    return response.ok; // If status is 200, the audio exists
  } catch (error) {
    // For errors, log them but assume the audio doesn't exist
    console.error('Error checking if audio exists:', error);
    return false;
  }
}

// We now use the mapping system in data/audioMapping.ts instead of a hardcoded list

// Cache for audio existence to reduce API calls
const audioExistsCache = new Map<string, boolean>();

// Track currently playing audio
let currentAudio: HTMLAudioElement | null = null;

function normalizeExactAudioWord(word: string): string {
  return word
    .normalize('NFC')
    .toLowerCase()
    .trim()
    .replace(/[\u2018\u2019]/g, "'");
}

function getExactAudioFilename(word: string): string | null {
  const cleanedWord = normalizeExactAudioWord(word);
  return audioMapping[cleanedWord] || null;
}

/**
 * Check if audio exists for a word, using cache when possible
 * @param word The word to check audio for
 * @returns A promise that resolves to true if audio exists, false otherwise
 */
export async function checkAudioExistsCached(word: string): Promise<boolean> {
  const cleanedWord = normalizeExactAudioWord(word);
  
  // Check cache first
  if (audioExistsCache.has(cleanedWord)) {
    return audioExistsCache.get(cleanedWord) || false;
  }
  
  if (getExactAudioFilename(cleanedWord)) {
    audioExistsCache.set(cleanedWord, true);
    return true;
  }
  
  audioExistsCache.set(cleanedWord, false);
  return false;
}

// Audio element cache to avoid creating new elements
currentAudio = null;

// Function to safely clean up audio resources
function cleanupAudio() {
  if (currentAudio) {
    // Remove all event listeners to prevent memory leaks
    currentAudio.onplay = null;
    currentAudio.onerror = null;
    currentAudio.onended = null;
    currentAudio.onstalled = null;
    currentAudio.onwaiting = null;
    currentAudio.oncanplay = null;
    currentAudio.onloadstart = null;
    
    // Pause and clean up
    currentAudio.pause();
    currentAudio.removeAttribute('src');
    currentAudio.load();
    
    // For modern browsers, this helps with garbage collection
    if ('remove' in HTMLMediaElement.prototype) {
      (currentAudio as any).remove();
    }
    
    currentAudio = null;
  }
}

// Function to log audio state for debugging
function logAudioState(audio: HTMLAudioElement, word: string, eventName: string) {
  console.log(`🔊 [${eventName}] State for "${word}":`, {
    readyState: audio.readyState,
    networkState: audio.networkState,
    error: audio.error,
    src: audio.currentSrc,
    currentTime: audio.currentTime,
    duration: audio.duration,
    paused: audio.paused,
    ended: audio.ended,
    seeking: audio.seeking,
  });
}

/**
 * Play audio for a word
 * @param word The word to play audio for
 * @returns A promise that resolves when the audio starts playing
 */
export async function playAudioForWord(word: string): Promise<boolean> {
  if (!word) {
    console.log('🔇 No word provided for audio playback');
    return false;
  }
  
  try {
    // Clean the word to match our mapping
    const cleanedWord = normalizeExactAudioWord(word);
    
    // Clean up any existing audio first
    cleanupAudio();
    
    console.log(`🔊 Attempting to play audio for "${cleanedWord}"`);
    
    // First check if we have a mapping for this word
    const audioFilename = getExactAudioFilename(cleanedWord);
    if (!audioFilename) {
      console.log(`🔇 No audio mapping found for "${cleanedWord}"`);
      return false;
    }
    
    console.log(`🔊 Found audio mapping: "${cleanedWord}" -> "${audioFilename}"`);
    
    // Use our API proxy instead of direct S3 URL to handle CORS and authentication
    const audioUrl = `/api/audio/${encodeURIComponent(cleanedWord)}`;
    console.log(`🔊 Using API URL: ${audioUrl}`);
    
    // Create a new audio element
    const audio = new Audio();
    currentAudio = audio;
    
    // Set up event handlers with proper cleanup
    const handleError = (event: Event | string) => {
      // Don't log errors if we've already cleaned up
      if (!currentAudio) return;
      
      const errorMessage = event instanceof Error ? event.message : 
                         typeof event === 'string' ? event : 
                         (event as any).message || 'Unknown error';
      
      console.error(`🔊 Error playing audio for "${cleanedWord}":`, errorMessage);
      console.error(`🔊 Audio URL that failed: ${audioUrl}`);
      
      // Add more detailed error information for debugging
      try {
        const audioElement = currentAudio as any;
        const networkState = audioElement.networkState;
        const readyState = audioElement.readyState;
        const networkStateText = [
          'NETWORK_EMPTY', 'NETWORK_IDLE', 'NETWORK_LOADING', 'NETWORK_NO_SOURCE'
        ][networkState] || 'UNKNOWN';
        const readyStateText = [
          'HAVE_NOTHING', 'HAVE_METADATA', 'HAVE_CURRENT_DATA', 'HAVE_FUTURE_DATA', 'HAVE_ENOUGH_DATA'
        ][readyState] || 'UNKNOWN';
        
        console.error(`🔊 Audio element state - NetworkState: ${networkStateText} (${networkState}), ReadyState: ${readyStateText} (${readyState})`);
        console.error(`🔊 Environment: ${typeof window !== 'undefined' ? 'Browser' : 'Server'}, Production: ${process.env.NODE_ENV === 'production'}`);
      } catch (e) {
        console.error('Error getting detailed audio state:', e);
      }
      
      logAudioState(audio, cleanedWord, 'ERROR');
      cleanupAudio();
    };
    
    const handleEnded = () => {
      console.log(`🔊 Finished playing audio for "${cleanedWord}"`);
      cleanupAudio();
    };
    
    // Type assertion to handle the error event
    audio.onerror = handleError as (event: Event | string) => void;
    audio.onended = handleEnded;
    
    // Additional debugging events
    audio.onloadstart = () => {
      console.log(`🔊 Audio loading started for "${cleanedWord}"`);
      logAudioState(audio, cleanedWord, 'LOAD_START');
    };
    
    audio.oncanplay = () => {
      console.log(`🔊 Audio can play for "${cleanedWord}"`);
      logAudioState(audio, cleanedWord, 'CAN_PLAY');
    };
    
    audio.onstalled = () => {
      console.error(`🔊 Playback stalled for "${cleanedWord}"`);
      logAudioState(audio, cleanedWord, 'STALLED');
    };
    
    audio.onwaiting = () => {
      console.log(`🔊 Waiting for audio data for "${cleanedWord}"`);
      logAudioState(audio, cleanedWord, 'WAITING');
    };
    
    // Set the source and start playback
    try {
      // First, ensure the URL is valid
      if (!audioUrl || audioUrl === '/true' || audioUrl.includes('undefined')) {
        throw new Error(`Invalid audio URL: ${audioUrl}`);
      }
      
      // Set the source and preload metadata
      audio.preload = 'metadata';
      audio.src = audioUrl;
      
      // Load the audio first to catch any loading errors
      await new Promise<void>((resolve, reject) => {
        const onCanPlay = () => {
          audio.removeEventListener('canplay', onCanPlay);
          audio.removeEventListener('error', onError);
          resolve();
        };
        
        const onError = (e: Event) => {
          audio.removeEventListener('canplay', onCanPlay);
          audio.removeEventListener('error', onError);
          reject(new Error(`Failed to load audio: ${(e as any).message || 'Unknown error'}`));
        };
        
        audio.addEventListener('canplay', onCanPlay, { once: true });
        audio.addEventListener('error', onError, { once: true });
      });
      
      console.log(`🔊 Starting playback for "${cleanedWord}"`);
      await audio.play();
      console.log(`🔊 Playback started for "${cleanedWord}"`);
      return true;
    } catch (error) {
      console.error(`🔊 Playback failed for "${cleanedWord}":`, error);
      cleanupAudio();
      return false;
    }
  } catch (error) {
    console.error(`🔊 Error in playAudioForWord for "${word}":`, error);
    cleanupAudio();
    return false;
  }
}

// Clean up audio when the page unloads
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', cleanupAudio);
  window.addEventListener('pagehide', cleanupAudio);
}
