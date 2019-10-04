import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
import numpy as np
import cv2

%pylab inline
import os
import PIL

def ary_prep(addr):
    digits = []
    labels = []
    img_file = []
    for i in os.listdir(addr):
        if i.endswith('.DS_Store'):
                continue
        for image in os.listdir("{}/{}".format(addr, i)):
            if not image.endswith('.png'):
                continue
            file_path = "{}/{}/{}".format(addr, i, image)
            img = PIL.Image.open(file_path).convert('1')
            digits.append([pixel for pixel in iter(img.getdata())])
            labels.append(i)
            img_file.append(file_path)
    return np.array(digits), labels, img_file

digit_ary, labels, img_file = ary_prep("model_set")

from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
scaler.fit(digit_ary)
X_scaled = scaler.transform(digit_ary)
mlp = MLPClassifier(hidden_layer_sizes=(30,30,30), activation='logistic', max_iter=5000)
mlp.fit(X_scaled, labels)

import shutil 
for i in range(0, len(img_file)):
    if not os.path.isdir("mlp_test_result"):
        os.mkdir("mlp_test_result")
    # Source path 
    source = image_Test[i]
    if not os.path.isdir("mlp_test_result/{}".format(predicted[i])):
        os.mkdir("mlp_test_result/{}".format(predicted[i]))
    number = len(os.listdir("mlp_test_result/{}".format(predicted[i])))
    # Destination path 
    destination = "mlp_test_result/{}/{}.png".format(predicted[i], number+1)
    # Copy the content of source to destination 
    shutil.copyfile(source, destination) 
    if image_Test[i].split("/")[2] != predicted[i]:
        print("From: ", image_Test[i], " to -> ", predicted[i])