# import custom_speech_recognition as sr
import speech_recognition as sr
# TODO: add crossplatform support for the pyaudio import
#import pyaudiowpatch as pyaudio
import pyaudio
import platform
from datetime import datetime

RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False

HUMAN_MIC_NAME = "External Microphone"
# macOS specific, see README.md#macos for the details on how to configure the BlackHole device
BLACKHOLE_MIC_NAME = "BlackHole 2ch"

class BaseRecorder:
    def __init__(self, source, source_name):
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = ENERGY_THRESHOLD
        self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD

        if source is None:
            raise ValueError("audio source can't be None")

        self.source = source
        self.source_name = source_name

    def adjust_for_noise(self, msg):
        print(f"[INFO] Adjusting for ambient noise. " + msg)
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
        print(f"[INFO] Completed ambient noise adjustment")

    def record_into_queue(self, audio_queue):
        def record_callback(_, audio:sr.AudioData) -> None:
            data = audio.get_raw_data()
            audio_queue.put((self.source_name, data, datetime.utcnow()))

        self.recorder.listen_in_background(self.source, record_callback, phrase_time_limit=RECORD_TIMEOUT)

class DefaultMicRecorder(BaseRecorder):
    def __init__(self):

        device_index = None

        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            # print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))

            # this assumes that mic has lower index number for combinded headsets (like Plantronics)
            if name == HUMAN_MIC_NAME:
                device_index = index
                break

            print("[DEBUG] \"{}\" microphone index is: {}".format(HUMAN_MIC_NAME, device_index))

        super().__init__(source=sr.Microphone(device_index=device_index, sample_rate=16000), source_name="You")
        self.adjust_for_noise("Please make some noise from the " + HUMAN_MIC_NAME + " ...")

class DefaultSpeakerRecorder(BaseRecorder):
    def __init__(self):

        os_name = platform.system()
        device_index = None

        if os_name == 'Windows':
            p = pyaudio.PyAudio()
            api_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(api_info["defaultOutputDevice"])
            print(f"[DEBUG] default speakers info: {default_speakers}")
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    print("[ERROR] No loopback device found.")
            p.terminate()
            device_index = default_speakers["index"]

        elif os_name == 'Darwin':
            for index, name in enumerate(sr.Microphone.list_microphone_names()):
                # print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(index, name))
                if name == BLACKHOLE_MIC_NAME:
                    device_index = index

            print("[DEBUG] \"{}\" microphone index is: {}".format(BLACKHOLE_MIC_NAME, device_index))

        # source = sr.Microphone(speaker=True,
        #                        device_index=device_index,
        #                        sample_rate=int(default_speakers["defaultSampleRate"]),
        #                        chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
        #                        channels=default_speakers["maxOutputChannels"])
        # TODO: experiment with Microphone params
        source = sr.Microphone(
                               device_index=device_index,
                               chunk_size=pyaudio.get_sample_size(pyaudio.paInt16))
        super().__init__(source=source, source_name="Speaker")
        self.adjust_for_noise("Please make or play some noise from the Default Speaker...")
