import picamera
import os
import uuid
import requests
import ConfigParser

class PHP():

    def __init__(self):
        self._get_config()
        self._camera = picamera.PiCamera()
        self._ms_face_key = "22485bc1cd4a47ffafbd8dd8c11ad2e1"

    def _get_config(self):
        update       = False
        config_file  = "config.txt"
        self._config = ConfigParser.ConfigParser()

        if os.path.isfile(config_file):
            self._config.read(config_file)
        else:
            print "Config file not found"
            update = True

        if not self._config.has_section('DIRS'):
            print "Adding DIRS part"
            update = True
            self._config.add_section("DIRS")

        if not self._config.has_option("DIRS", "Capture"):
            print "No Capture Directory"
            update = True
            self._config.set("DIRS", "Capture", "/tmp/php/captures/")

        if not self._config.has_option("DIRS", "Mosaic"):
            print "No Mosaic Directory"
            update = True
            self._config.set("DIRS", "Mosaic", "/tmp/php/mosaic/")

        if not self._config.has_section('CLOUDANT'):
            print "Adding Cloudant part"
            update = True
            self._config.add_section("CLOUDANT")

        if not self._config.has_option("CLOUDANT", "ServerAddress"):
            print "No Server Address"
            update = True
            self._config.set("CLOUDANT", "ServerAddress", "<ServerAddress>")

        if not self._config.has_option("CLOUDANT", "Username"):
            print "No Username"
            update = True
            self._config.set("CLOUDANT", "Username", "Didditulle")

        if not self._config.has_option("CLOUDANT", "Password"):
            print "No Password"
            update = True
            self._config.set("CLOUDANT", "Password", "geheim")

        if not self._config.has_section('MICROSOFT'):
            print "Adding Microsoft part"
            update = True
            self._config.add_section("MICROSOFT")

        if not self._config.has_option("MICROSOFT", "FaceKey"):
            print "No Microsoft FaceKey"
            update = True
            self._config.set("MICROSOFT", "FaceKey", "<Facekey>")

        if update:
            with open(config_file, 'w') as f:
                self._config.write(f)

    def _capture_picture(self):
        name = self._capture_dir + uuid.uuid4() + ".jpg"
        self._camera.capture(name)
        return name

    def _get_ms_results(self):
        url = 'https://westus.api.cognitive.microsoft.com/emotion/v1.0/recognize'
        maxNumRetries = 10


    def main_loop(self):
        current_image = self._capture_picture()
        print current_image

if __name__ == "__main__":
    p = PHP()
    p.main_loop()

