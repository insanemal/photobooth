#!/usr/bin/python2
import time
import cv2
import numpy as np

def cvText(frame,text,loc,font,size):
    cv2.putText(frame, text,loc,font,size,(255,255,255,255),12,cv2.LINE_AA)
    cv2.putText(frame, text,loc,font,size,(0,0,0,0),4,cv2.LINE_AA)

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
                cv2.imwrite('/home/malcolm/test_'+str(int(time.time()))+'.png',state['frame2'])
            if state['Freeze']:
                state['frame'] = state['Freeze_frame'].copy()
        if display_time == -2:
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
            cv2.imwrite('/home/malcolm/test_'+str(int(time.time()))+'.png',state['Freeze_frame'])

def quad_image(frame):
    tmp_frame = cv2.resize(frame,None,fx=0.5,fy=0.5)
    frame[0:360,0:640] = tmp_frame[0:360,0:640]
    frame[0:360,640:1280] = tmp_frame[0:360,0:640]
    frame[360:720,0:640] = tmp_frame[0:360,0:640]
    frame[360:720,640:1280] = tmp_frame[0:360,0:640]
    return frame

def fourshot(state,method):
    if not(state['Snap']):
        method(state)
        state['frame'] = quad_image(state['frame'])
    if state['Snap']:
        fourshot_worker(state, method)

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

def main():
    cap = cv2.VideoCapture(0)
    state = {'Snap':False,
             "Freeze":False,
             "countdown": 3,
             "mode": 0,
             'font': cv2.FONT_HERSHEY_SIMPLEX,
             'frame_no' : 1,
             'four_shot' : False}
    filters = (normal,cartoon,four_col,sepia)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    while(True):
        ret, state['frame'] = cap.read()
        if not(state['four_shot']):
            filters[state['mode']](state)
        if state['four_shot']:
            fourshot(state,filters[state['mode']])
        if not(state['Freeze']):
            cvText(state['frame'], 'Press q to quit',(10,25),state['font'],1)
        cv2.imshow('frame',state['frame'])
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if not(state['Snap']):
            if key == ord(' '):
                state['Snap'] = True;
                state['start_time'] = time.time()
            if key == ord('1'):
                state['mode'] = 0
            if key == ord('2'):
                state['mode'] = 1
            if key == ord('3'):
                state['mode'] = 2
            if key == ord('4'):
                state['mode'] = 3
            if key == ord('f'):
                state['four_shot'] = not(state['four_shot'])
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
