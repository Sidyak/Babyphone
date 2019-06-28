#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  camera_pi.py
#  
#  
#  
import time
import io
import threading
import picamera
import pyaudio

def genHeader(sampleRate, bitsPerSample, channels, chunk):
#    datasize = 2000 * channels * bitsPerSample // 8
    datasize = 200*1024*1024
    o = bytes("RIFF",'ascii')                                               # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4,'little')                               # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE",'ascii')                                              # (4byte) File type
    o += bytes("fmt ",'ascii')                                              # (4byte) Format Chunk Marker
    o += (16).to_bytes(4,'little')                                          # (4byte) Length of above format data
    o += (1).to_bytes(2,'little')                                           # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2,'little')                                    # (2byte)
    o += (sampleRate).to_bytes(4,'little')                                  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4,'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2,'little')               # (2byte)
    o += (bitsPerSample).to_bytes(2,'little')                               # (2byte)
    o += bytes("data",'ascii')                                              # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4,'little')                                    # (4byte) Data size in bytes
    return o


class Microphone(object):
    sound = None
    audio = None
    stream = None
    form_1 = pyaudio.paInt16 #pyaudio.paInt16 # 16-bit resolution
    chans = 1 # 1 channel
    samp_rate = 44100 # 44.1kHz sampling rate
    dev_index = 1 # device index found by p.get_device_info_by_index(ii)
    chunk = 4096 # 2^12 samples buffer

    def initialize(self):
        if Microphone.audio is None:
            Microphone.audio = pyaudio.PyAudio() # create pyaudio instantiation
            # create pyaudio stream
            Microphone.stream = Microphone.audio.open(format = self.form_1, rate = self.samp_rate, channels = self.chans, \
                    input_device_index = self.dev_index,input = True, \
                    frames_per_buffer=self.chunk)
            #time.sleep(1)
            Microphone.stream.start_stream()

        sound = genHeader(self.samp_rate, 16, self.chans, self.chunk) + self.stream.read(self.chunk, exception_on_overflow = False) 
        return sound

    def get_sound(self):
        sound = self.stream.read(self.chunk, exception_on_overflow = False)

        return sound

class Camera(object):
    threadCam = None  # background thread that reads frames from camera
    frame = None  # current frame is stored here by background thread
    last_access = 0  # time of last client access to the camera

    def initialize(self):
        if Camera.threadCam is None:
            # start background frame thread
            Camera.threadCam = threading.Thread(target=self._threadCam)
            Camera.threadCam.start()
            print("threadCam has been started")
            # wait until frames start to be available
            while self.frame is None:
                time.sleep(0)

    def get_frame(self):
        Camera.last_access = time.time()
        self.initialize()
        return self.frame

    @classmethod
    def _threadCam(cls):
        print("entering threadCam")
        with picamera.PiCamera() as camera:
            # camera setup
            camera.resolution = (640, 480)
            camera.framerate = 30
            camera.hflip = True
            camera.vflip = True

            # let camera warm up
            camera.start_preview()
            time.sleep(2)

            stream = io.BytesIO()
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                # store frame
                stream.seek(0)
                cls.frame = stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()

                # if there hasn't been any clients asking for frames in
                # the last 10 seconds stop the thread
                if time.time() - cls.last_access > 10:
                    break
        
        cls.thread = None

