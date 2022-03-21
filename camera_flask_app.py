from flask import Flask, render_template, Response, request
from flask_ngrok import run_with_ngrok
import cv2
import datetime, time
import os, sys
import numpy as np
from threading import Thread
import re
import long_responses as long


global capture,rec_frame, switch, face, rec, out
capture=0
face=0
switch=1
rec=0

#make shots directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass

#Load pretrained face detection model    
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
smile_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

#instatiate flask app  
app = Flask(__name__, template_folder='./templates')
run_with_ngrok(app)

camera = cv2.VideoCapture(0)


def record(out):
    global rec_frame
    while(rec):
        time.sleep(0.05)
        out.write(rec_frame)


def detect_face(frame):
    global net
    frame_grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(frame_grayscale)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 200, 50), 4)

        the_face = frame[y:y + h, x:x + w]

        face_grayscale = cv2.cvtColor(the_face, cv2.COLOR_BGR2GRAY)

        smiles = smile_detector.detectMultiScale(face_grayscale, scaleFactor=1.7, minNeighbors=20)

        # for (x_, y_, w_, h_) in smiles:
        # cv2.rectangle(the_face, (x_, y_), (x_ + w_, y_ + h_), (100, 200, 50), 4)
        if len(smiles) > 0:
            cv2.putText(frame, 'nice, you are smiling', (x, y + h + 40), fontScale=1, fontFace=cv2.FONT_HERSHEY_TRIPLEX,
                        color=(255, 0, 255))
            #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    #frame = cv2.imshow('Smile Detector', frame)
    return frame
 

def gen_frames():  # generate frame by frame from camera
    global out, capture,rec_frame
    while True:
        success, frame = camera.read()
        if success:
            if(face):                
                frame= detect_face(frame)
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot_{}.png".format(str(now).replace(":",''))])
                cv2.imwrite(p, frame)
            
            if(rec):
                rec_frame=frame
                frame= cv2.putText(cv2.flip(frame,1),"Recording...", (0,25), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),4)
                frame=cv2.flip(frame,1)
            
                
            try:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
                
        else:
            pass


def message_probability(user_message, recognised_words, single_response=False, required_words=[]):
    message_certainty = 0
    has_required_words = True

    # Counts how many words are present in each predefined message
    for word in user_message:
        if word in recognised_words:
            message_certainty += 1

    # Calculates the percent of recognised words in a user message
    percentage = float(message_certainty) / float(len(recognised_words))

    # Checks that the required words are in the string
    for word in required_words:
        if word not in user_message:
            has_required_words = False
            break

    # Must either have the required words, or be a single response
    if has_required_words or single_response:
        return int(percentage * 100)
    else:
        return 0


def check_all_messages(message):
    highest_prob_list = {}

    # Simplifies response creation / adds it to the dict
    def response(bot_response, list_of_words, single_response=False, required_words=[]):
        nonlocal highest_prob_list
        highest_prob_list[bot_response] = message_probability(message, list_of_words, single_response, required_words)

    # Responses -------------------------------------------------------------------------------------------------------
    response('Hello!', ['hello', 'hi', 'hey', 'sup', 'heyo'], single_response=True)
    response('My Name is Danny the Happy Bot!', ['my', 'name', 'is'], required_words=['name'])
    response('See you!', ['bye', 'goodbye'], single_response=True)
    response('I\'m doing fine, and you?', ['how', 'are', 'you', 'doing'], required_words=['how'])
    response('You\'re welcome!', ['thank', 'thanks'], single_response=True)
    response('Thank you!', ['love'], single_response=True)
    response('Everything will be okay!', ['feel', 'not', 'mood'], single_response=True)

    # Longer responses
    response(long.R_ADVICE, ['give', 'advice', 'help', 'sad', 'stressed', 'angry'], single_response=True)
    response(long.R_HAPPY, ['tunes', 'songs'], single_response=True)

    best_match = max(highest_prob_list, key=highest_prob_list.get)
    # print(highest_prob_list)
    # print(f'Best match = {best_match} | Score: {highest_prob_list[best_match]}')

    return long.unknown() if highest_prob_list[best_match] < 1 else best_match


# Used to get the response
def get_response(user_input):
    split_message = re.split(r'\s+|[,;?!.-]\s*', user_input.lower())
    response = check_all_messages(split_message)
    return response


@app.route("/get")
def get_bot_response():
    userText = request.args.get('msg')
    #return str(english_bot.get_response(userText))
    #print("Here")
    return str(get_response(userText))


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/smiledec")
def smiledec():
    return render_template('smiledec.html')

@app.route("/chat")
def chat():
    return render_template('chat.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('face') == 'Smile':
            global face
            face=not face 
            if(face):
                time.sleep(4)   
        elif  request.form.get('stop') == 'Stop/Start Video':
            
            if(switch==1):
                switch=0
                camera.release()
                cv2.destroyAllWindows()
                
            else:
                camera = cv2.VideoCapture(0)
                switch=1
        elif  request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec= not rec
            if(rec):
                now=datetime.datetime.now() 
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                out = cv2.VideoWriter('vid_{}.avi'.format(str(now).replace(":",'')), fourcc, 20.0, (640, 480))
                #Start new thread for recording the video
                thread = Thread(target = record, args=[out,])
                thread.start()
            elif(rec==False):
                out.release()
                          
                 
    elif request.method=='GET':
        return render_template('smiledec.html')
    return render_template('smiledec.html')


if __name__ == '__main__':
    app.run()
    
camera.release()
cv2.destroyAllWindows()
