import pyaudio
import pyrubberband
import numpy as np
import time
from typing import ByteString

CHUNK = 1024
PYAUDIO_FORMAT = pyaudio.paInt16
NP_FORMAT = np.int16
CHANNELS = 1
RATE = 44100
THRESHOLD = 1000
SILENCE_DURATION = 2


class AudioEngine:
    def __init__(self) -> None:
        self._audio = pyaudio.PyAudio()
        self._in_stream = self._audio.open(format=PYAUDIO_FORMAT,
                                           channels=CHANNELS,
                                           rate=RATE,
                                           input=True,
                                           frames_per_buffer=CHUNK,
                                           input_device_index=None)
        self._out_stream = self._audio.open(format=PYAUDIO_FORMAT,
                                            channels=CHANNELS,
                                            rate=RATE,
                                            output=True)
        self._is_loaded: bool = True

    def terminate(self) -> None:
        self._in_stream.stop_stream()
        self._out_stream.stop_stream()
        self._in_stream.close()
        self._out_stream.close()
        self._audio.terminate()
        self._is_loaded = False

    def record_audio(self) -> ByteString:
        if not self._is_loaded:
            raise RuntimeError("AudioEngine terminated")

        self._in_stream.start_stream()
        frames = []
        silent_counter = 0
        while True:
            data = self._in_stream.read(CHUNK)
            frames.append(data)
            audio_data = np.frombuffer(data, dtype=NP_FORMAT)
            if np.max(np.abs(audio_data)) < THRESHOLD:
                silent_counter += 1
            else:
                silent_counter = 0
            if silent_counter >= int(RATE / CHUNK * SILENCE_DURATION):
                break
        self._in_stream.stop_stream()

        audio_data = b''.join(frames)
        return audio_data

    def play_audio(self, audio_data: ByteString) -> None:
        if not self._is_loaded:
            raise RuntimeError("AudioEngine terminated")
        # self._out_stream.start_stream()
        self._out_stream.write(audio_data)
        # self._out_stream.stop_stream()

    @staticmethod
    def change_pitch(audio_data: ByteString, factor: float = 2.0) -> ByteString:
        audio_array = np.frombuffer(audio_data, dtype=NP_FORMAT)
        shifted_audio = pyrubberband.pitch_shift(audio_array, RATE, factor)
        # rubberband returned data is represented in float
        shifted_audio -= shifted_audio.min()
        shifted_audio /= shifted_audio.max() if shifted_audio.max() != 0 else 1
        shifted_audio *= (audio_array.max() - audio_array.min())
        shifted_audio -= audio_array.min()
        return shifted_audio.astype(np.int16).tobytes()


def parrot_game():
    print("game begins")
    engine = AudioEngine()

    silent_counter = 0
    while True:
        print("recording")
        audio_data = engine.record_audio()
        print(len(audio_data))
        if silent_counter > 1:
            break
        if len(audio_data) <= 176128:
            print("No audio input. Please try again.")
            silent_counter += 1
            continue
        else:
            silent_counter = 0

        parrot_voice = float(np.random.randint(6, 15))
        high_pitch_audio = engine.change_pitch(audio_data, parrot_voice)

        engine.play_audio(high_pitch_audio)

        time.sleep(0.3)

    engine.terminate()


if __name__ == "__main__":
    parrot_game()

    # info = audio.get_host_api_info_by_index(0)
    # numdevices = info.get('deviceCount')

    # for i in range(0, numdevices):
    #     if (audio.get_device_info_by_host_api_device_index(
    #         0, i).get('maxInputChannels')) > 0:
    #         print("Input Device id ",
    #             i,
    #             " - ",
    #             audio.get_device_info_by_host_api_device_index(
    #                 0, i).get('name'))

    # str_input_i = input("choose input source (num):")
    # try:
    #     input_i = int(str_input_i)
    # except ValueError:
    #     input_i = None

    # input_i = None
    # stream = audio.open(format=FORMAT,
    #                     channels=CHANNELS,
    #                     rate=RATE,
    #                     input=True,
    #                     frames_per_buffer=CHUNK,
    #                     input_device_index=input_i)
