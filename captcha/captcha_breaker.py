import matplotlib.pyplot as plt
import cv2
import os
import re
import numpy as np


def captcha_mdfk(img_file):
    # Read file
    image = cv2.imread(img_file)
    
    # Basic Handling
    kernel = np.ones((4,4), np.uint8)
    erosion = cv2.erode(image, kernel, iterations=1)
    light = lightness(erosion, a=2, b=80)
    dilation = cv2.dilate(light, kernel, iterations=1)
    dilation = cv2.cvtColor(dilation, cv2.COLOR_BGR2GRAY)

    # Cutting images into 50x50 cubic
    contours, hierarchy = cv2.findContours(dilation.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    cnts = sorted([(c, cv2.boundingRect(c)[0]) for c in contours], key= lambda x: x[1])
    ary = []
    
    for (c, _) in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        # 太小張捨棄
        if w > 20 and h > 20:
            # 太大張就對半切
            if w > 90:
                ary.append(((x, y, int(w/3), h)))
                ary.append(((int(x+w/3), y, int(w/3), h))) 
                ary.append(((int(x+2*w/3), y, int(w/3), h))) 
            elif w > 60:
                ary.append(((x, y, int(w/2), h)))
                ary.append(((int(x+w/2), y, int(w/2), h)))  
            else:
                ary.append(((x, y, w, h)))   
    fig = plt.figure()
    
    final_ans = ""

    for id, (x, y, w, h) in enumerate(ary):
        roi = dilation[y:y+h, x:x+w]
        thresh = roi.copy()
        a = fig.add_subplot(1, len(ary), id+1)
        res = cv2.resize(thresh, (50,50))
        res = cv2.cvtColor(res, cv2.COLOR_BGR2RGB)
        ans = getNumber(res)
        if ans != '':
            if not os.path.isdir('test_set/'+ans):
                os.mkdir('test_set/'+ans)
            cv2.imwrite("test_set/{}/{}.png".format(ans, len(os.listdir('test_set/'+ans))+1), res)
        final_ans += ans
        #plt.imshow(res)

    return final_ans

# A supplement function for make black and white file
def lightness(img, a=2, b=80):
    rows,cols,channels=img.shape
    dst=img.copy()
    for i in range(rows):
        for j in range(cols):
            for c in range(3):
                # 從灰色一刀劃開，大者恆大，小者恆小
                color = img[i,j][c]*a+b if img[i,j][c] > 125 else img[i,j][c]/a-b
                if color>255:           # 防止像素值越界（0~255）
                    dst[i,j][c]=255
                elif color<0:           # 防止像素值越界（0~255）
                    dst[i,j][c]=0
                else:
                    dst[i,j][c]=color
    return dst

# Calculation Min Square
def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float"))**2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    return err

def getNumber(pic):
    max_a = 0
    max_png = None
    for png in os.listdir('Alphabet'):
        if not png.endswith('.png'):
            continue
        # Remove some characters that had never shown before
        if png in ['0.png', 'O.png', '1.png', 'I.png', 'S.png', '5.png', 'W.png', 'M.png', 'B.png']:
            continue
        ref = cv2.imread('Alphabet/'+png)
        if mse(ref, pic) > max_a:
            max_a = mse(ref, pic)
            max_png = png
    # if its hard to recognize, then give up
    return "" if max_a < 125000 else re.sub('.png', '', max_png)

for file in os.listdir('img'):
    try:
        ans = captcha_mdfk("img/"+file)
        print("Change File From: " + file + "  ->  " + str(ans))
        os.rename("img/"+file, "img/%s.png"%str(ans))
    except Exception as e:
        continue
