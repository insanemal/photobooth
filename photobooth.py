#!/usr/bin/python2
import time
import cv2

def normal(state):
    if state["Snap"]:
        font = cv2.FONT_HERSHEY_SIMPLEX
        display_time = state['countdown'] - int(time.time() - state['start_time'] )
        state['frame2'] = state['frame'].copy()
        if display_time > -1:
            cv2.putText(state['frame'], str(display_time),(620,350),font,3,(255,255,255,255),2,cv2.LINE_AA)
            cv2.putText(state['frame'], str(display_time),(620,350),font,3,(0,0,0,0),1,cv2.LINE_AA)
        if display_time < 1:
            if not(state['Freeze']):
                state['Freeze'] = True
                state['Freeze_frame'] = state['frame2'].copy()
                cv2.imwrite('/home/malcolm/test_'+str(int(time.time()))+'.png',state['frame2'])
            if state['Freeze']:
                state['frame'] = state['Freeze_frame']
        if display_time == -2:
            state['Snap'] = False
            state['Freeze'] = False



def main():
    cap = cv2.VideoCapture(0)
    state = {'Snap':False,
             "Freeze":False,
             "countdown": 3,
             "mode": 0}

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    while(True):
        ret, state['frame'] = cap.read()
        font = cv2.FONT_HERSHEY_SIMPLEX
        if state['mode'] == 0:
            normal(state)
        if not(state['Freeze']):
            cv2.putText(state['frame'], 'Press q to quit',(10,25),font,1,(255,255,255),2,cv2.LINE_AA)
            cv2.putText(state['frame'], 'Press q to quit',(10,25),font,1,(0,0,0),1,cv2.LINE_AA)

        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow('frame',state['frame'])
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord(' '):
            #cv2.imwrite('/home/malcolm/test.png', frame2)
            if not(state['Snap']):
                state['Snap'] = True;
                state['start_time'] = time.time()

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
