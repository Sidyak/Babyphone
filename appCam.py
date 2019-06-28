#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   appCam.py
#
#   PiCamera and PyAudio and local Web Server with Flask

from flask import Flask, render_template, Response, stream_with_context
from camera_pi import Camera      # camera class
from camera_pi import Microphone  # microphone class

app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def genVideo(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def genAudio(mic):
    """Audio streaming generator function."""
    sound = mic.initialize()
    while True:
        yield sound
        sound = mic.get_sound()


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(genVideo(Camera()),
            mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    """Audio streaming route."""
    return Response(stream_with_context(genAudio(Microphone())), mimetype='audio/x-wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port =80, debug=True, threaded=True)

