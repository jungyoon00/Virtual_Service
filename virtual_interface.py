import cv2
import numpy as np
import pyautogui
import time
from hand_tracking import HandDetector
from pynput.keyboard import Controller

##########################
wCam, hCam = 1280, 720
frameR = 100  # Frame Reduction
smoothening = 7
pressInterval = 0.01
##########################

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = HandDetector(maxHands=1)
wScr, hScr = pyautogui.size()

keys = [["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "\\"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "!", "?"]]
finalText = ""

def drawAll(img, buttonList):
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        cv2.rectangle(img, button.pos, (x + w, y + h), (255, 0, 255), cv2.FILLED)
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
    return img

class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

keyboard = Controller()

buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

backspace = Button([100 * (len(keys) + 1) + 350, 100 * (len(keys)) + 55], "<")
export = Button([100 * (len(keys) + 1) + 450, 100 * (len(keys)) + 55], "[->", [170, 85])
buttonList.append(backspace)
buttonList.append(export)

def exportWords(text):
    pyautogui.countdown(3)
    pyautogui.alert(text)

mode = False
while True:
    # 1. Find hand Landmarks
    success, img = cap.read()
    if mode:
        pass
    else:
        img = cv2.flip(img, 1)
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    # 2. Get the tip of the index and middle fingers
    if len(lmList) != 0:
        x0, y0 = lmList[4][1:]
        x1, y1 = lmList[8][1:]
        x2, y2 = lmList[12][1:]

    # 3. Check which fingers are up
    fingers = detector.fingersUp()

    #===========================================================================#

    if mode:
        cv2.rectangle(
            img, (frameR, frameR), (wCam - frameR, hCam - frameR), (255, 0, 255), 2
        )
        if len(fingers) > 0:
            # 4. Only Index Finger : Moving Mode
            if fingers[1] == 1 and fingers[2] == 0:
    
                # 5. Convert Coordinates
                x_ = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y_ = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
    
                # 6. Smoothen Values
                clocX = plocX + (x_ - plocX) / smoothening
                clocY = plocY + (y_ - plocY) / smoothening
    
                # 7. Move Mouse
                pyautogui.moveTo(wScr - clocX, clocY)
                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                plocX, plocY = clocX, clocY
    
            # 8. Both Index and middle fingers are up : Clicking Mode
            if fingers[1] == 1 and fingers[2] == 1:
    
                # 9. Find distance between fingers
                length, img, lineInfo = detector.findDistance(8, 12, img)
    
                # 10. Click mouse if distance short
                if length < 45:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()
            
            if fingers[0] == 1 and fingers[1] == 1 and fingers[4] == 1:
                
                length, _, _ = detector.findDistance(4, 8, img)

                if cv2.waitKey(1) & 0xFF == ord("v"):
                    if length > 100:
                        pyautogui.press("volumeup")
                        print("&[Volume Up]")
                    elif length <= 100:
                        pyautogui.press("volumedown")
                        print("&[Volume Down]")
    else:
        img = drawAll(img, buttonList)
        if lmList:
            for button in buttonList:
                x, y = button.pos
                w, h = button.size

                if (x <= x1 <= x+w) and (y <= y1 <= y+h):
                    cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), (175, 0, 175), cv2.FILLED)
                    cv2.putText(img, button.text, (x + 20, y + 65),
                                cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                    l, _, _ = detector.findDistance(8, 12, img, draw=False)
    
                    # when clicked
                    if l < 35:
                        if button.text == "<":
                            if len(finalText) == 0:
                                continue
                            print(f"&[Delete Text]: del {finalText[-1]}")
                            finalText = finalText[0:len(finalText)-1]
                            continue
                        elif button.text == "[->":
                            print(f"&[export Text]: '{finalText}'")
                            exportWords(finalText)
                            continue
                        print(f"[Press Keyboard]: {button.text} (Interval: {pressInterval})")
                        keyboard.press(button.text)
                        cv2.rectangle(img, button.pos, (x + w, y + h), (0, 255, 0), cv2.FILLED)
                        cv2.putText(img, button.text, (x + 20, y + 65),
                                    cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 4)
                        finalText += button.text

                        if len(finalText) > 15:
                            finalText = finalText[:15]
                        time.sleep(pressInterval)
    
        cv2.rectangle(img, (50, 350), (700, 450), (175, 0, 175), cv2.FILLED)
        cv2.putText(img, finalText, (60, 430),
                    cv2.FONT_HERSHEY_PLAIN, 5, (255, 255, 255), 5)
    
    #===========================================================================#

    # 11. Frame Rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, "Frame: "+str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1)

    # 12. Display
    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
    if cv2.waitKey(1) & 0xFF == ord("m"):
        mode = True
    if cv2.waitKey(1) & 0xFF == ord("k"):
        mode = False

cap.release()
cv2.destroyAllWindows()