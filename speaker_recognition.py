import os
import queue
import re
import sys
import serial.tools.list_ports
from google.cloud import speech
import pyaudio

# google cloud credentials dosyasının yolu
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\JSONDOSYA\\organic-berm-427909-s1-a5a7d03b485f.json" ^# json dosyasının yolu olmalı burası

# ses örnekleme frekansı ve paketin boyutu
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# anahtar kelimeler kapıyı açmak veya kapatmak için
open_keyword = "kapıyı aç"
close_keyword = "kapıyı kapat"

# arduino serial bağlantı ayarları
arduino_port = "COM3"  # arduino'nun bağlı olduğu port
baud_rate = 9600  # baud hızı

def list_ports():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        print(p)

class MicrophoneStream(object):
    """Ses akışı sağlayan bir kayıt akışı oluşturur ve ses parçalarını üretir."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk
        self._buff = queue.Queue()
        self._closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer
        )
        self._closed = False
        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self._closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self._closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

def listen_print_loop(responses):
    print("Dinliyorum...")  # dinlemeye başladı demek
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if re.search(r'\b{}\b'.format(open_keyword), transcript, re.I):
            print("Kapı açıldı!")
            ser.write(b'open\n')  # arduinoya open komutunu gönderiyoruz
            return True

        if re.search(r'\b{}\b'.format(close_keyword), transcript, re.I):
            print("Kapı kapandı!")
            ser.write(b'close\n')  # arduinoya close komutunu gönderiyoruz
            return True

        sys.stdout.write(transcript + overwrite_chars + '\r')
        sys.stdout.flush()

        num_chars_printed = len(transcript)

    return False

def main():
    list_ports()  # list available ports before connecting
    try:
        ser = serial.Serial(arduino_port, baud_rate)
    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
        return

    client = speech.SpeechClient()

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code='tr-TR'
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (speech.StreamingRecognizeRequest(audio_content=content) for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)
        listen_print_loop(responses)

if __name__ == "__main__":
    main()