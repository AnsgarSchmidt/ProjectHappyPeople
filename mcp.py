import picamera
import os
import cv2
import sys
import uuid
import time
import random
import json
import ConfigParser
import RPi.GPIO               as     GPIO
import cognitive_face         as     CF
from   subprocess             import call
from   watson_developer_cloud import VisualRecognitionV3
from   cloudant.client        import Cloudant

class PHP():

    def __init__(self):
        random.seed()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup( 3, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
        GPIO.setup( 5, GPIO.IN,  pull_up_down=GPIO.PUD_UP)
        GPIO.setup(12, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(16, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(18, GPIO.OUT, initial=GPIO.LOW)
        self._get_config()
        CF.Key.set(self._config.get("MICROSOFT", "FaceKey"))
        self._visual_recognition = VisualRecognitionV3('2016-05-20', api_key=self._config.get("IBM", "visualkey"))
        self._camera = picamera.PiCamera()
        if not os.path.isdir(self._config.get("DIRS", "Capture")):
            print "Creating Capture Dir"
            os.makedirs(self._config.get("DIRS", "Capture"))
        if not os.path.isdir(self._config.get("DIRS", "Mosaic")):
            print "Creating Mosaic Dir"
            os.makedirs(self._config.get("DIRS", "Mosaic"))
        self._db = Cloudant(self._config.get("CLOUDANT", "Username"), self._config.get("CLOUDANT", "Password"), url=self._config.get("CLOUDANT", "Host"), connect=True)

    def _generate_game_goals(self):
        self._game_goals = {}
        self._game_goals['total']     = random.randint( 5, 10)
        self._game_goals['age']       = random.randint(15, 42) * self._game_goals['total']
        self._game_goals['male']      = random.randint(0,  self._game_goals['total'])
        self._game_goals['female']    = random.randint(0, (self._game_goals['total'] - self._game_goals['male']))
        self._game_goals['glasses']   = random.randint(0,  self._game_goals['total'])
        self._game_goals['hair']      = random.randint(0,  self._game_goals['male'])
        self._game_goals['happy']     = random.randint(0,  self._game_goals['total'])
        self._game_goals['surprised'] = random.randint(0, (self._game_goals['total'] - self._game_goals['happy']))

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
            self._config.set("DIRS", "Capture", "/tmp/php/captures")

        if not self._config.has_option("DIRS", "Mosaic"):
            print "No Mosaic Directory"
            update = True
            self._config.set("DIRS", "Mosaic", "/tmp/php/mosaic")

        if not self._config.has_section('CLOUDANT'):
            print "Adding Cloudant part"
            update = True
            self._config.add_section("CLOUDANT")

        if not self._config.has_option("CLOUDANT", "Host"):
            print "No CLOUDANT Host"
            update = True
            self._config.set("CLOUDANT", "Host", "<Host>")

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

        if not self._config.has_section('IBM'):
            print "Adding IBM part"
            update = True
            self._config.add_section("IBM")

        if not self._config.has_option("IBM", "VisualKey"):
            print "No IBM VisualKey"
            update = True
            self._config.set("IBM", "VisualKey", "<VisualKey>")

        if update:
            with open(config_file, 'w') as f:
                self._config.write(f)
            sys.exit(1)

    def _capture_picture(self):
        self._current_picture_name = "%s/%s.jpg" % (self._config.get("DIRS", "Capture"), uuid.uuid4())
        self._camera.capture(self._current_picture_name)

    def _get_ms_results(self):
        # https://www.microsoft.com/cognitive-services/en-US/subscriptions
        self._ms_result = CF.face.detect(self._current_picture_name, landmarks=False, attributes='age,gender,smile,facialHair,glasses,emotion')

    def _get_ibm_results(self):
        with open(self._current_picture_name, 'rb') as image_file:
            #self._ibm_face_results = self._visual_recognition.detect_faces(images_file=image_file)
            self._ibm_result = self._visual_recognition.classify(images_file=image_file)

    def _store_in_db(self):
        if "ms_results" not in self._db.all_dbs():
            self._db.create_database('ms_results')
            print "Creating ms_results"

        if "ibm_results" not in self._db.all_dbs():
            self._db.create_database('ibm_results')
            print "Creating ibm_results"

        if self._ms_result is not None:
            ms_database = self._db['ms_results']
            j = {}
            j['result']     = self._ms_result
            j['image_name'] = self._current_picture_name
            ms_document = ms_database.create_document(j)

            if ms_document.exists():
                print 'SUCCESS MS!!'

        if self._ibm_result is not None:
            ibm_database = self._db['ibm_results']
            j = {}
            j['result']     = self._ibm_result
            j['image_name'] = self._current_picture_name
            ibm_document = ibm_database.create_document(j)

            if ibm_document.exists():
                print 'SUCCESS IBM!!'

    def _enhance_image(self):
        img   = cv2.imread(self._current_picture_name)
        logo  = cv2.imread("ibm-bluemix.png")
        slogo = cv2.resize(logo, None, fx=0.26, fy=0.26, interpolation=cv2.INTER_CUBIC)

        for currFace in self._ms_result:
            faceRectangle = currFace['faceRectangle']
            emotion       = self._extract_emotion(currFace['faceAttributes']['emotion'])
            age           = currFace['faceAttributes']['age']
            textToWrite   = "%s - %s" % (age, emotion)
            cv2.rectangle(img, (faceRectangle['left'], faceRectangle['top']),
                               (faceRectangle['left'] + faceRectangle['width'],
                                faceRectangle['top'] + faceRectangle['height']),
                               color=(255, 255, 0), thickness=3)
            cv2.putText(img, textToWrite, (faceRectangle['left'], faceRectangle['top'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        cv2.rectangle(img, (0, 0), (1680, 60), color=(0, 0, 0), thickness=60)
        textToWrite = "Goal   : Age:%03.1f / Male:%d / Female:%d / Glasses:%d / Beard:%d / Happy:%d / Surprised:%d" % (self._game_goals['age'], self._game_goals['male'], self._game_goals['female'], self._game_goals['glasses'], self._game_goals['hair'], self._game_goals['happy'], self._game_goals['surprised'])
        cv2.putText(img, textToWrite, (270, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (  0, 255,   0), 3)
        textToWrite = "Current: Age:%03.1f / Male:%d / Female:%d / Glasses:%d / Beard:%d / Happy:%d / Surprised:%d" % (self._game_results['age'], self._game_results['male'], self._game_results['female'], self._game_results['glasses'], self._game_results['hair'], self._game_results['happy'], self._game_results['surprised'])
        cv2.putText(img, textToWrite, (270, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (  0,   0, 255), 3)
        #if self._check_game():
        #    cv2.putText(img, "You Won!", (0, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
        #else:
        #    cv2.putText(img, "Find more people :-)", (0, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (  0, 0, 255), 3)

        rows, cols, channels  = slogo.shape
        roi                   = img[0:rows, 0:cols]
        img2gray              = cv2.cvtColor(slogo, cv2.COLOR_BGR2GRAY)
        ret, mask             = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv              = cv2.bitwise_not(mask)
        img1_bg               = cv2.bitwise_and(roi, roi, mask=mask_inv)
        img2_fg               = cv2.bitwise_and(slogo, slogo, mask=mask)
        dst                   = cv2.add(img1_bg, img2_fg)
        img[0:rows, 0:cols]  = dst

        cv2.imwrite('/tmp/test.png', img)

    def _cut_faces(self):
        img = cv2.imread(self._current_picture_name)

        for currFace in self._ms_result:
            faceRectangle = currFace['faceRectangle']
            x = faceRectangle['left']
            y = faceRectangle['top']
            w = faceRectangle['width']
            h = faceRectangle['height']

            crop_img = img[y:y+h, x:x+w]
            newfilename = "%s/%s.jpg" % (self._config.get("DIRS", "Mosaic"), uuid.uuid4())
            cv2.imwrite(newfilename, crop_img)

    def _extract_emotion(self, inmotion):
        score = 0.0
        emotion = "neural"
        for e in inmotion:
            if inmotion[e] > score:
                score = inmotion[e]
                emotion = e
        return emotion

    def _extract_game_results(self):
        self._game_results = {}
        self._game_results['total']     = 0
        self._game_results['age']       = 0
        self._game_results['male']      = 0
        self._game_results['female']    = 0
        self._game_results['glasses']   = 0
        self._game_results['hair']      = 0
        self._game_results['happy']     = 0
        self._game_results['surprised'] = 0

        for currFace in self._ms_result:
            self._game_results['total'] += 1
            self._game_results['age']   += currFace['faceAttributes']['age']
            if currFace['faceAttributes']['gender'] == "male":
                self._game_results['male'] += 1
            if currFace['faceAttributes']['gender'] == "female":
                self._game_results['female'] += 1
            if currFace['faceAttributes']['glasses'] != "NoGlasses":
                self._game_results['glasses'] += 1
            if currFace['faceAttributes']['facialHair']['beard']     > 0.5 or \
               currFace['faceAttributes']['facialHair']['moustache'] > 0.5 or \
               currFace['faceAttributes']['facialHair']['sideburns'] > 0.5:
                self._game_results['hair'] += 1
            if self._extract_emotion(currFace['faceAttributes']['emotion']) == "happiness":
                self._game_results['happy'] += 1
            if self._extract_emotion(currFace['faceAttributes']['emotion']) == "surprise":
                self._game_results['surprised'] += 1

    def _check_game(self):
        if self._game_results['age']       >= self._game_goals['age']      and \
           self._game_results['male']      >= self._game_goals['male']     and \
           self._game_results['female']    >= self._game_goals['female']   and \
           self._game_results['glasses']   >= self._game_goals['glasses']  and \
           self._game_results['hair']      >= self._game_goals['hair']     and \
           self._game_results['happy']     >= self._game_goals['happy']    and \
           self._game_results['surprised'] >= self._game_goals['surprised']:
            GPIO.output(18, True)
            return True
        else:
            return False

    def main_loop(self):
        in_game = True
        while True:
            GPIO.output(12, False)
            GPIO.output(16, False)
            GPIO.output(18, False)
            self._generate_game_goals()
            in_game = True
            while in_game:
                while GPIO.input(3):
                    time.sleep(0.3)
                    if not GPIO.input(5):
                        in_game = False
                        break
                    print "wait"
                print "Capture"
                GPIO.output(16, True)
                GPIO.output(12, True)
                self._capture_picture()
                GPIO.output(16, False)
                self._get_ms_results()
                self._get_ibm_results()
                self._cut_faces()
                self._extract_game_results()
                self._enhance_image()
                GPIO.output(12, False)
                print json.dumps(self._ms_result,  sort_keys=True, indent=4, separators=(',', ': '))
                print json.dumps(self._ibm_result, sort_keys=True, indent=4, separators=(',', ': '))
                print self._game_goals
                print self._game_results
                call(["killall", "fbi"])
                self._store_in_db()

if __name__ == "__main__":
    p = PHP()
    p.main_loop()

