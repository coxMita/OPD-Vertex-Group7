/**
 * Convert an uploaded WAV file to 16 kHz mono 16-bit PCM before sending it for
 * transcription. Whisper resamples to 16 kHz mono internally anyway, so this
 * loses nothing for speech but makes a 30 min CD-quality recording ~5x smaller
 * (≈300 MB → ≈58 MB).
 *
 * The file is read in chunks, so even very large recordings never have to be
 * decoded into memory all at once (unlike AudioContext.decodeAudioData).
 * Files that can't be parsed are returned unchanged and the backend handles them.
 */

export const SPEECH_SAMPLE_RATE = 16_000

const CHUNK_FRAMES = 1 << 20 // ~1M frames per read

interface WavFormat {
  audioFormat: number // 1 = integer PCM, 3 = IEEE float
  channels: number
  sampleRate: number
  bitsPerSample: number
  blockAlign: number
  dataOffset: number
  dataSize: number
}

const WAVE_FORMAT_PCM = 1
const WAVE_FORMAT_IEEE_FLOAT = 3
const WAVE_FORMAT_EXTENSIBLE = 0xfffe

async function readBytes(file: Blob, start: number, length: number): Promise<DataView> {
  const buf = await file.slice(start, start + length).arrayBuffer()
  return new DataView(buf)
}

function fourCC(view: DataView, offset: number): string {
  return String.fromCharCode(
    view.getUint8(offset),
    view.getUint8(offset + 1),
    view.getUint8(offset + 2),
    view.getUint8(offset + 3),
  )
}

/** Parse the RIFF header and return the format and the location of the PCM data. */
export async function parseWavHeader(file: Blob): Promise<WavFormat | null> {
  if (file.size < 44) return null
  const riff = await readBytes(file, 0, 12)
  if (fourCC(riff, 0) !== 'RIFF' || fourCC(riff, 8) !== 'WAVE') return null

  let fmt: Omit<WavFormat, 'dataOffset' | 'dataSize'> | null = null
  let offset = 12
  while (offset + 8 <= file.size) {
    const head = await readBytes(file, offset, 8)
    const id = fourCC(head, 0)
    const size = head.getUint32(4, true)
    const body = offset + 8

    if (id === 'fmt ') {
      const f = await readBytes(file, body, Math.min(size, 40))
      let audioFormat = f.getUint16(0, true)
      if (audioFormat === WAVE_FORMAT_EXTENSIBLE && size >= 26) {
        audioFormat = f.getUint16(24, true) // first two bytes of the sub-format GUID
      }
      fmt = {
        audioFormat,
        channels: f.getUint16(2, true),
        sampleRate: f.getUint32(4, true),
        blockAlign: f.getUint16(12, true),
        bitsPerSample: f.getUint16(14, true),
      }
    } else if (id === 'data') {
      if (!fmt) return null
      // Some recorders write 0 or 0xFFFFFFFF when they don't know the length
      const available = file.size - body
      const dataSize = size === 0 || size > available ? available : size
      return { ...fmt, dataOffset: body, dataSize }
    }

    offset = body + size + (size % 2) // chunks are padded to even sizes
  }
  return null
}

function sampleReader(fmt: WavFormat): ((view: DataView, pos: number) => number) | null {
  const { audioFormat, bitsPerSample } = fmt
  if (audioFormat === WAVE_FORMAT_PCM) {
    switch (bitsPerSample) {
      case 8:
        return (v, p) => (v.getUint8(p) - 128) / 128
      case 16:
        return (v, p) => v.getInt16(p, true) / 32768
      case 24:
        return (v, p) => {
          const n = v.getUint8(p) | (v.getUint8(p + 1) << 8) | (v.getInt8(p + 2) << 16)
          return n / 8388608
        }
      case 32:
        return (v, p) => v.getInt32(p, true) / 2147483648
    }
  } else if (audioFormat === WAVE_FORMAT_IEEE_FLOAT) {
    if (bitsPerSample === 32) return (v, p) => v.getFloat32(p, true)
    if (bitsPerSample === 64) return (v, p) => v.getFloat64(p, true)
  }
  return null
}

/** Build a 16-bit mono PCM WAV file from samples. */
export function encodeWav16(samples: Int16Array, sampleRate: number): ArrayBuffer {
  const dataSize = samples.length * 2
  const buf = new ArrayBuffer(44 + dataSize)
  const view = new DataView(buf)
  const writeStr = (o: number, s: string) => {
    for (let i = 0; i < s.length; i++) view.setUint8(o + i, s.charCodeAt(i))
  }
  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + dataSize, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, WAVE_FORMAT_PCM, true)
  view.setUint16(22, 1, true) // mono
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeStr(36, 'data')
  view.setUint32(40, dataSize, true)
  new Int16Array(buf, 44).set(samples)
  return buf
}

/**
 * Return a 16 kHz mono 16-bit version of `file`, or `file` itself if it is
 * already in that format (or can't be converted).
 */
export async function toSpeechWav(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<File> {
  const fmt = await parseWavHeader(file)
  if (!fmt) return file

  const read = sampleReader(fmt)
  const { channels, sampleRate, blockAlign } = fmt
  const alreadySpeech =
    fmt.audioFormat === WAVE_FORMAT_PCM &&
    channels === 1 &&
    sampleRate === SPEECH_SAMPLE_RATE &&
    fmt.bitsPerSample === 16
  // Only downsample; low-rate recordings are left for the backend to handle
  if (!read || alreadySpeech || channels < 1 || blockAlign < 1 || sampleRate < SPEECH_SAMPLE_RATE) {
    return file
  }

  const bytesPerSample = fmt.bitsPerSample / 8
  const totalFrames = Math.floor(fmt.dataSize / blockAlign)
  const ratio = sampleRate / SPEECH_SAMPLE_RATE
  const out = new Int16Array(Math.ceil(totalFrames / ratio) + 1)

  // Average all source frames that fall into each output sample (box filter):
  // cheap anti-aliasing that is plenty for speech recognition.
  let outIndex = 0
  let acc = 0
  let count = 0
  let boundary = ratio
  let frame = 0

  const emit = () => {
    const v = Math.max(-1, Math.min(1, acc / count))
    out[outIndex++] = Math.round(v * 0x7fff)
    acc = 0
    count = 0
    boundary = (outIndex + 1) * ratio
  }

  for (let start = 0; start < totalFrames; start += CHUNK_FRAMES) {
    const frames = Math.min(CHUNK_FRAMES, totalFrames - start)
    const view = await readBytes(file, fmt.dataOffset + start * blockAlign, frames * blockAlign)

    for (let f = 0; f < frames; f++) {
      const base = f * blockAlign
      let mono = 0
      for (let c = 0; c < channels; c++) mono += read(view, base + c * bytesPerSample)
      acc += mono / channels
      count++
      frame++
      if (frame >= boundary) emit()
    }

    onProgress?.(Math.round(((start + frames) * 100) / totalFrames))
  }
  if (count > 0) emit()

  const name = file.name.replace(/\.wav$/i, '') + '_16k.wav'
  return new File([encodeWav16(out.subarray(0, outIndex), SPEECH_SAMPLE_RATE)], name, {
    type: 'audio/wav',
  })
}
