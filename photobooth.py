#!/usr/bin/python2
import time
import cv2
import numpy as np

def cvText(frame,text,loc,font,size):
    cv2.putText(frame, text,loc,font,size,(255,255,255,255),2,cv2.LINE_AA)
    cv2.putText(frame, text,loc,font,size,(0,0,0,0),1,cv2.LINE_AA)


def normal(state):
    if state["Snap"]:
        display_time = state['countdown'] - int(time.time() - state['start_time'] )
        state['frame2'] = state['frame'].copy()
        if display_time > -1:
            cvText(state['frame'], str(display_time),(620,350),state['font'],3)
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
        state['frame'] = quad_image(state['frame'])
    if state['Snap']:
        fourshot_worker(state, normal)


def main():
    cap = cv2.VideoCapture(0)
    state = {'Snap':False,
             "Freeze":False,
             "countdown": 3,
             "mode": 0,
             'font': cv2.FONT_HERSHEY_SIMPLEX,
             'frame_no' : 1}

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    while(True):
        ret, state['frame'] = cap.read()
        if state['mode'] == 0:
            normal(state)
        if state['mode'] == 1:
            fourshot(state,normal)
        if not(state['Freeze']):
            cvText(state['frame'], 'Press q to quit',(10,25),state['font'],1)

        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow('frame',state['frame'])
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if not(state['Snap']):
            if key == ord(' '):
                state['Snap'] = True;
                state['start_time'] = time.time()
            if key == ord('1'):
                state['mode'] = 1
            if key == ord('0'):
                state['mode'] = 0

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
