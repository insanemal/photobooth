#!/usr/bin/python2
import time
import cv2
import os
import numpy as np
from google_cred import OAuth2Login
import multiprocessing
from random import shuffle

def load_config(state):
    workingdir = os.path.expanduser('./')
    filen = os.path.join(workingdir, 'booth.conf')
    with open(filen) as f:
        for line in f:
            state[line[0:line.find(':')].strip()] = line[line.find(':')+1:].strip()

def login_google(state):
    try:
        workingdir = os.path.expanduser('./')
        secrets = os.path.join(workingdir, 'gapps.json')
        cred_store = os.path.join(workingdir, 'creds.data')
        state['gapps'] = OAuth2Login(secrets,cred_store,state['gmail'])
        state['gapps_on'] = True
    except Exception, e:
        print "Login failed check your credentials\n    %s" % e
        state['gapps_on'] = False
        state['g_album'] = 'None'

def picasa_upload(filen,state):
    if (state['g_album'] != 'None') and state['gapps_on']:
        album_url = '/data/feed/api/user/%s/albumid/%s' % (state['gmail'], state['g_album'])
        photo = state['gapps'].InsertPhotoSimple(album_url,'PhotoBooth', state['gapps_caption'], filen, content_type='image/png')


def cvText(frame,text,loc,font,size):
    cv2.putText(frame, text,loc,font,size,(255,255,255,255),12,cv2.LINE_AA)
    cv2.putText(frame, text,loc,font,size,(0,0,0,0),4,cv2.LINE_AA)

def save_frame(state,frame):
    fname = os.path.join(state['path'],'booth_'+str(int(time.time()))+'.png')
    cv2.imwrite(fname,frame)
    state['worklist'].append(fname)


def normal(state):
    if state["Snap"]:
        display_time = state['countdown'] - int(time.time() - state['start_time'] )
        state['frame2'] = state['frame'].copy()
        if display_time > -1:
            cvText(state['frame'], str(display_time),(610,385),state['font'],3)
        if display_time < 1:
            if not(state['Freeze']):
                state['Freeze'] = True
                state['Freeze_frame'] = state['frame2'].copy()
                save_frame(state,state['frame2'])
            if state['Freeze']:
                state['frame'] = state['Freeze_frame'].copy()
        if display_time < -1:
            state['Snap'] = False
            state['Freeze'] = False

def fourshot_worker(state,method):
    if not(state['Freeze']):
        state['oneshot'] = False
    method(state)
    if (not(state['oneshot']) and state['Freeze']):
        state['oneshot'] = True
        if state['frame_no'] == 1:
            state['oneshot_frame'] = np.zeros((720,1280,3),np.uint8)
            state['oneshot_frame'][0:360,0:640] = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)[0:360,0:640]
        if state['frame_no'] == 2:
            state['oneshot_frame'][0:360,640:1280] = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)[0:360,0:640]
        if state['frame_no'] == 3:
            state['oneshot_frame'][360:720,0:640] = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)[0:360,0:640]
        if state['frame_no'] == 4:
            state['oneshot_frame'][360:720,640:1280] = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)[0:360,0:640]
        state['frame'] = state['oneshot_frame'].copy()
        state['Freeze_frame'] = state['oneshot_frame'].copy()
    if not(state['Snap']):
        state['frame_no'] += 1
        if state['frame_no'] < 5:
            state['start_time'] = time.time()
            state['Snap'] = True
        if state['frame_no'] == 5:
            state['frame_no'] = 1
            save_frame(state,state['Freeze_frame'])

def quad_image(frame1,frame2,frame3,frame4):
    frame = np.zeros((720,1280,3),np.uint8)
    tmp_frame = cv2.resize(frame1,None,fx=0.5,fy=0.5)
    frame[0:360,0:640] = tmp_frame[0:360,0:640]
    tmp_frame = cv2.resize(frame2,None,fx=0.5,fy=0.5)
    frame[0:360,640:1280] = tmp_frame[0:360,0:640]
    tmp_frame = cv2.resize(frame3,None,fx=0.5,fy=0.5)
    frame[360:720,0:640] = tmp_frame[0:360,0:640]
    tmp_frame = cv2.resize(frame4,None,fx=0.5,fy=0.5)
    frame[360:720,640:1280] = tmp_frame[0:360,0:640]
    return frame

def fourshot(state,method1,method2,method3,method4):
    if not(state['Snap']):
        if state['four_shot']:
            method1(state)
            state['frame'] = quad_image(state['frame'],state['frame'],state['frame'],state['frame'])
        if not(state['four_shot']):
            tmp_image = state['frame'].copy()

            method1(state)
            tmp_frame1 = state['frame'].copy()
            state['frame'] = tmp_image.copy()

            method2(state)
            tmp_frame2 = state['frame'].copy()
            state['frame'] = tmp_image.copy()

            method3(state)
            tmp_frame3 = state['frame'].copy()
            state['frame'] = tmp_image.copy()

            method4(state)
            tmp_frame4 = state['frame'].copy()
            state['frame'] = quad_image(tmp_frame1,tmp_frame2,tmp_frame3,tmp_frame4)
    if state['Snap']:
        if state['four_shot']:
            fourshot_worker(state, method1)
        if state['random']:
            if state['frame_no'] == 1:
                fourshot_worker(state, method1)
            if state['frame_no'] == 2:
                fourshot_worker(state, method2)
            if state['frame_no'] == 3:
                fourshot_worker(state, method3)
            if state['frame_no'] == 4:
                fourshot_worker(state, method4)


def cartoon(state):
    num_down = 2
    num_bilateral = 7
    img_colour = state['frame']

    for _ in xrange(num_down):
        img_colour = cv2.pyrDown(img_colour)

    for _ in xrange(num_bilateral):
        img_colour = cv2.bilateralFilter(img_colour, d=9, sigmaColor=9, sigmaSpace=7)

    for _ in xrange(num_down):
        img_colour = cv2.pyrUp(img_colour)

    img_grey = cv2.cvtColor(state['frame'],cv2.COLOR_RGB2GRAY)
    img_blur = cv2.medianBlur(img_grey, 7)

    img_edge = cv2.adaptiveThreshold(img_blur, 255,
                                    cv2.ADAPTIVE_THRESH_MEAN_C,
                                    cv2.THRESH_BINARY,
                                    blockSize=9,
                                    C=2)
    img_edge = cv2.cvtColor(img_edge, cv2.COLOR_GRAY2RGB)
    state['frame'] = cv2.bitwise_and(img_colour, img_edge)
    if state['Snap']:
        normal(state)

def four_col(state):
    tmp_frame = cv2.resize(state['frame'],None,fx=0.5,fy=0.5)
    tmp_grey = cv2.cvtColor(tmp_frame, cv2.COLOR_RGB2GRAY)
    tmp_invert = cv2.bitwise_not(tmp_grey)
    tmp_zeros = np.zeros((360,640),np.uint8)

    tmp_frame1 = np.zeros((360,640,3),np.uint8)
    tmp_frame2 = tmp_frame1.copy()
    tmp_frame3 = tmp_frame1.copy()
    tmp_frame4 = tmp_frame1.copy()

    tmp_frame1[0:360,0:640,0] = tmp_invert
    tmp_frame1[0:360,0:640,1] = tmp_grey
    tmp_frame1[0:360,0:640,2] = tmp_zeros

    tmp_frame2[0:360,0:640,1] = tmp_invert
    tmp_frame2[0:360,0:640,2] = tmp_grey
    tmp_frame2[0:360,0:640,0] = tmp_grey

    tmp_frame3[0:360,0:640,1] = tmp_invert
    tmp_frame3[0:360,0:640,0] = tmp_grey
    tmp_frame3[0:360,0:640,2] = tmp_invert

    tmp_frame4[0:360,0:640,2] = tmp_invert
    tmp_frame4[0:360,0:640,0] = tmp_grey
    tmp_frame4[0:360,0:640,1] = tmp_grey

    state['frame'][0:360,0:640] = tmp_frame1[0:360,0:640]
    state['frame'][0:360,640:1280] = tmp_frame2[0:360,0:640]
    state['frame'][360:720,0:640] = tmp_frame3[0:360,0:640]
    state['frame'][360:720,640:1280] = tmp_frame4[0:360,0:640]

    if state['Snap']:
        normal(state)

def sepia(state):
    frame = state['frame'].copy()
    m_sepia = np.asarray([[0.272, 0.534, 0.131],
                             [0.349, 0.686, 0.168],
                             [0.393, 0.769, 0.189]])
    state['frame'] = cv2.transform(frame, m_sepia)
    if state['Snap']:
        normal(state)

def grey(state):
    img_grey = cv2.cvtColor(state['frame'],cv2.COLOR_RGB2GRAY)
    state['frame'] = cv2.cvtColor(img_grey,cv2.COLOR_GRAY2RGB)
    if state['Snap']:
        normal(state)

def erode(state):
    kernel = np.ones((5,5),np.uint8)
    state['frame'] = cv2.erode(state['frame'],kernel,iterations =3)
    if state['Snap']:
        normal(state)

def other_process(state,worklist):
    sleep_timer = 0
    while not('QUIT' in worklist):
        if len(worklist) > 0:
            fname = worklist.pop()
            print 'Uploading: %s' % (fname)
            picasa_upload(fname,state)
        else:
            print 'sleeping'
            time.sleep(1)
            sleep_timer += 1
            if sleep_timer > 10000:
                login_google(state)


def main():
    state = {'Snap': False,
            "Freeze": False,
            "countdown": 3,
            "mode": 0,
            'font': cv2.FONT_HERSHEY_SIMPLEX,
            'frame_no': 1,
            'four_shot': False,
            'random': False,
            'random_list': [0,1,2,3,4,5]}
    load_config(state)
    login_google(state)
    m = multiprocessing.Manager()
    worklist = m.list()
    p = multiprocessing.Process(target = other_process,args=(state,worklist,))
    p.start()
    state['worklist'] = worklist
    filters = (normal,cartoon,four_col,sepia,grey,erode)
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    while(True):
        ret, state['frame'] = cap.read()
        if (not(state['four_shot']) and not(state['random'])):
            filters[state['mode']](state)
        if state['four_shot']:
            fourshot(state,filters[state['mode']],filters[state['mode']],filters[state['mode']],filters[state['mode']])
        if state['random']:
            fourshot(state,filters[state['random_list'][0]],filters[state['random_list'][1]],filters[state['random_list'][2]],filters[state['random_list'][3]])
#        if not(state['Freeze']):
#            cvText(state['frame'], 'Press q to quit',(10,25),state['font'],1)
        cv2.namedWindow("PhotoBooth", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("PhotoBooth", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow('PhotoBooth',state['frame'])
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if not(state['Snap']):
            if key == ord(' '):
                state['Snap'] = True;
                state['start_time'] = time.time()
            if key == ord('1'):
                state['mode'] = 0
                state['random'] = False
            if key == ord('2'):
                state['mode'] = 1
                state['random'] = False
            if key == ord('3'):
                state['mode'] = 2
                state['random'] = False
            if key == ord('4'):
                state['mode'] = 3
                state['random'] = False
            if key == ord('5'):
                state['mode'] = 4
                state['random'] = False
            if key == ord('6'):
                state['mode'] = 5
                state['random'] = False
            if key == ord('f'):
                state['four_shot'] = not(state['four_shot'])
                state['random'] = False
            if key == ord('r'):
                state['random'] = not(state['random'])
                state['four_shot'] = False
                shuffle(state['random_list'])
    cap.release()
    cv2.destroyAllWindows()
    while len(worklist) > 0:
        print 'Sleeping main'
        time.sleep(1)
    worklist.append("QUIT")
    p.join()

if __name__ == '__main__':
    main()
