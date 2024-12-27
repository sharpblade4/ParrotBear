import pyaudio
import pyrubberband
import numpy as np
from typing import ByteString, Callable

CHUNK = 2048
PYAUDIO_FORMAT = pyaudio.paInt16
NP_FORMAT = np.int16
CHANNELS = 1
RATE = 44100
THRESHOLD = 1000
SILENCE_DURATION = 1
SILENCE_COUNTER_THRESHOLD = int(RATE / CHUNK * SILENCE_DURATION)
VOLUME_INCREASE = 1.2


class AudioEngine:
    def __init__(self) -> None:
        self._audio = pyaudio.PyAudio()
        self._in_stream = self._audio.open(
            format=PYAUDIO_FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
            input_device_index=None,
            stream_callback=None,
            start=False,
        )
        self._out_stream = self._audio.open(
            format=PYAUDIO_FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            start=False,
        )
        self._is_loaded: bool = True

    def record_audio(self) -> ByteString:
        if not self._is_loaded:
            raise RuntimeError("AudioEngine terminated")

        self._in_stream.start_stream()
        frames = []
        silent_counter = 0
        audio_buffer = np.zeros(CHUNK, dtype=NP_FORMAT)

        try:
            while True:
                data = self._in_stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)

                np.copyto(audio_buffer, np.frombuffer(data, dtype=NP_FORMAT))
                audio_level = np.max(np.abs(audio_buffer))
                if audio_level < THRESHOLD:
                    silent_counter += 1
                else:
                    silent_counter = 0

                if silent_counter >= SILENCE_COUNTER_THRESHOLD:
                    break
        except Exception as e:
            self._in_stream.stop_stream()
            raise RuntimeError(f"Error during recording: {str(e)}")

        self._in_stream.stop_stream()
        return b"".join(frames)

    def play_audio(self, audio_data: ByteString, complete_callback: Callable) -> None:
        print("engine playing audio", flush=True)
        if not self._is_loaded:
            raise RuntimeError("AudioEngine terminated")

        self._out_stream.start_stream()
        self._out_stream.write(audio_data)
        self._out_stream.stop_stream()

        while self._out_stream.is_active():
            import time

            time.sleep(0.1)
        complete_callback()

    def change_pitch(self, audio_data: ByteString, factor: float = 2.0) -> ByteString:
        print("DEBUG: changing pitch2 with factor", factor, flush=True)
        try:
            audio_array = np.frombuffer(audio_data, dtype=NP_FORMAT).astype(np.float32)
            audio_array = audio_array / 32768.0  # normalize 16-bit audio
            shifted_audio = pyrubberband.pitch_shift(
                audio_array,
                RATE,
                factor,
            )
            shifted_audio = np.clip(
                shifted_audio * 32768.0 * VOLUME_INCREASE, -32768, 32767
            )
            return shifted_audio.astype(np.int16).tobytes()

        except Exception as e:
            print(f"Error during pitch shifting: {e}")
            return audio_data

    def __del__(self):
        if hasattr(self, "_in_stream") and self._in_stream:
            self._in_stream.stop_stream()
            self._in_stream.close()
            self._in_stream = None
        if hasattr(self, "_out_stream") and self._out_stream:
            self._out_stream.stop_stream()
            self._out_stream.close()
            self._out_stream = None
        if hasattr(self, "_audio") and self._audio:
            self._audio.terminate()
            self._audio = None
        self._is_loaded = False


class AudioEngineMock:
    def __init__(self) -> None:
        pass

    def record_audio(self) -> ByteString:
        print("mock recodring_audio")
        import time

        time.sleep(2)
        frames = []
        for i in range(0, 100):
            frames.append(
                np.random.randint(-32768, 32767, CHUNK, dtype=NP_FORMAT).tobytes()
            )
        return b"".join(frames)

    def play_audio(self, audio_data: ByteString) -> None:
        print("mock play_audio")
        import time

        time.sleep(3)

    def change_pitch2(self, audio_data: ByteString, factor: float = 2.0) -> ByteString:
        print("mock change_pitch")
        return audio_data
