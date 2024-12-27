import threading
import tkinter as tk
from PIL import Image, ImageTk
from queue import Queue, Empty

# from audio_engine import AudioEngineMock as AudioEngine
from audio_engine import AudioEngine
import numpy as np


FIXED_SQUARE_WINDOW = 768
START_REC_MESSAGE = "Start"
FREQ_RANGE_BY_ANIMAL = {
    "parrot": (4, 9),
    "bear": (-10, -16),
}


class AnimalGui:
    def __init__(self, master, animal_name: str):
        self.master = master
        self.animal_name = animal_name
        self.current_image_index = 0
        self.other_animal_window = None

        try:
            self.talking_animal = Image.open(f"talking_{animal_name}.png")
            self.looking_animal = Image.open(f"looking_{animal_name}.png")
        except Exception as e:
            raise RuntimeError(f"Error loading {animal_name} images:", e)
            if self.talking_animal:
                self.talking_animal.close()
            if self.looking_animal:
                self.looking_animal.close()

        self.talking_animal = self.talking_animal.resize(
            (FIXED_SQUARE_WINDOW, FIXED_SQUARE_WINDOW), Image.Resampling.LANCZOS
        )
        self.looking_animal = self.looking_animal.resize(
            (FIXED_SQUARE_WINDOW, FIXED_SQUARE_WINDOW), Image.Resampling.LANCZOS
        )

        self.talking_photo = ImageTk.PhotoImage(self.talking_animal)
        self.looking_photo = ImageTk.PhotoImage(self.looking_animal)

        self.current_photo = self.looking_photo
        self._is_talking = False
        self.engine = AudioEngine()
        self.is_processing = False
        self.auto_restart = False

        self.update_queue = Queue()

        self.master.title(f"ParrotBear: {animal_name.title()}")
        self.master.resizable(False, False)

        self.canvas = tk.Canvas(
            master,
            width=FIXED_SQUARE_WINDOW,
            height=FIXED_SQUARE_WINDOW,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.image_on_canvas = self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.current_photo
        )

        self.start_button = tk.Button(
            master, text=START_REC_MESSAGE, command=self.toggle_recording
        )
        self.start_button.pack(pady=10)

        self.status_label = tk.Label(master, text="Press the button to start")
        self.status_label.pack(pady=5)

        self.process_queue()

    def __del__(self):
        self.talking_animal.close()
        self.looking_animal.close()

    def toggle_recording(self):
        if self.auto_restart:
            self.stop_recording()
            if self.other_window:
                self.other_window.start_button.config(state=tk.NORMAL)
        else:
            self.start_recording()
            if self.other_window:
                self.other_window.start_button.config(state=tk.DISABLED)

    def switch_image(self, is_talking):
        if self._is_talking == is_talking:
            return

        self._is_talking = is_talking
        self.current_photo = self.talking_photo if is_talking else self.looking_photo
        self.canvas.itemconfig(self.image_on_canvas, image=self.current_photo)

    def start_recording(self):
        if self.is_processing:
            print("WARN: Already processing", flush=True)
            return

        self.start_button.config(text="Stop", state=tk.NORMAL)
        self.auto_restart = True
        self.start_recording_thread()

    def start_recording_thread(self):
        thread = threading.Thread(target=self.process_audio, daemon=True)
        thread.start()

    def process_audio(self):
        self.is_processing = True

        try:
            self.update_queue.put((False, "Recording. . . ..."))
            audio_data = self.engine.record_audio()
            pitched_voice = float(
                np.random.uniform(*FREQ_RANGE_BY_ANIMAL[self.animal_name])
            )
            self.update_queue.put((True, "Playing..."))
            high_pitch_audio = self.engine.change_pitch(audio_data, pitched_voice)

            def on_playback_complete():
                if self.auto_restart:
                    self.update_queue.put(("restart", None))
                else:
                    self.update_queue.put((False, "Ready"))
                    self.update_queue.put(("button", START_REC_MESSAGE))

            self.engine.play_audio(high_pitch_audio, on_playback_complete)

        except Exception as e:
            self.update_queue.put((False, f"Error: {str(e)}"))
            self.auto_restart = False
            self.is_processing = False
            self.update_queue.put(("button", START_REC_MESSAGE))
            # self.update_queue.put((False, "Ready"))
        finally:
            self.is_processing = False

    def stop_recording(self):
        self.auto_restart = False
        self.start_button.config(text=START_REC_MESSAGE, state=tk.NORMAL)
        self.status_label.config(text="Stopped")

    def process_queue(self):
        try:
            while True:
                item = self.update_queue.get_nowait()
                if isinstance(item, tuple):
                    # print("DEBUG: got event:" , item)
                    message_type, status_text = item
                    if message_type == "button":
                        self.start_button.config(text=status_text, state=tk.NORMAL)
                    if message_type == "restart":
                        self.start_recording_thread()
                    else:
                        self.status_label.config(text=status_text)
                        self.switch_image(message_type)
                else:
                    print("WARN got unexpected event:", item)
        except Empty:
            pass
        finally:
            # Schedule the next queue processing
            self.master.after(100, self.process_queue)


def main():
    root = tk.Tk()
    second_window = tk.Toplevel()

    root.geometry(f"{FIXED_SQUARE_WINDOW}x{FIXED_SQUARE_WINDOW + 100}+50+50")
    second_window.geometry(
        f"{FIXED_SQUARE_WINDOW}x{FIXED_SQUARE_WINDOW + 100}+{FIXED_SQUARE_WINDOW + 100}+50"
    )

    parrot_app = AnimalGui(root, "parrot")
    bear_app = AnimalGui(second_window, "bear")

    parrot_app.other_window = bear_app
    bear_app.other_window = parrot_app

    root.mainloop()


if __name__ == "__main__":
    main()
