import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier
import numpy as np
import cv2
import tqdm
import os
import PIL
from sklearn.model_selection import train_test_split 
def ary_prep(addr):
    digits = []
    labels = []
    img_file = []
    for i in tqdm.tqdm(os.listdir(addr)):
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

# 資料是否有 shuffle 差別會很大
# 1. 這是有 shuffle 過的，accuracy 為 0.99
# X_train, X_test, y_train, y_test = train_test_split(X_scaled, labels, test_size=0.2)

# 2. 無 shuffle 過，一樣拿 2成的資料做 testing，accuracy 為 0.83
X_train, X_test = X_scaled[:int(len(X_scaled)*0.8)], X_scaled[int(len(X_scaled)*0.2):]
y_train, y_test = labels[:int(len(labels)*0.8)], labels[int(len(labels)*0.2):]

# CV 領域通常會用 relu 作為 activation function, 因為 logistic 會有梯度消失的問題
mlp = MLPClassifier(hidden_layer_sizes=(30,30,30), activation='relu', max_iter=5000)
mlp.fit(X_train, y_train)
print(mlp.score(X_test, y_test))

# import shutil 
# digit_ary_Test, labels_Test, img_file_Test = ary_prep("test_set")
# predicted = mlp.predict(digit_ary_Test)
# for i in tqdm.tqdm(range(0, len(img_file))):
#     if not os.path.isdir("mlp_test_result"):
#         os.mkdir("mlp_test_result")
#     # Source path 
#     source = image_Test[i]
#     if not os.path.isdir("mlp_test_result/{}".format(predicted[i])):
#         os.mkdir("mlp_test_result/{}".format(predicted[i]))
#     number = len(os.listdir("mlp_test_result/{}".format(predicted[i])))
#     # Destination path 
#     destination = "mlp_test_result/{}/{}.png".format(predicted[i], number+1)
#     # Copy the content of source to destination 
#     shutil.copyfile(source, destination) 
#     if image_Test[i].split("/")[2] != predicted[i]:
#         print("From: ", image_Test[i], " to -> ", predicted[i])