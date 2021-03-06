import sys

import librosa
import os
from scipy.spatial import distance
import numpy as np
from scipy import stats

accepted_strings = {'dog', 'down', 'yes', 'on', 'off'}
num_to_label = {0: "dog", 1: 'down', 2: 'yes', 3: "on", 4: "off"}
label_to_num = {"dog": 0, 'down': 1, 'yes': 2, "on": 3, "off": 4}


def findEuclideanDistance(data, mfcc):
    dst = 0
    for i in range(101):
        vector1 = data[0][:, i]
        vector2 = mfcc[:, i]
        dst += np.linalg.norm(vector1 - vector2)
        # dst += distance.euclidean(vector1, vector2)
    return dst/101


def minEuclidianDistance(mfcc, trainingDataSet):
    min = 999999999999999999999999999999999
    euclidean_choice = None
    for data in trainingDataSet:
        distance_euclidean = findEuclideanDistance(data, mfcc)
        if distance_euclidean < min:
            min = distance_euclidean
            euclidean_choice = data

    return euclidean_choice


def buildDtwMat(distMat):
    DtwMat = np.zeros([101, 101], np.float32)
    DtwMat[0, 0] = distMat[0, 0]
    for i in range(101):
        for j in range(101):
            if i == 0 and j == 0:
                DtwMat[i, j] = distMat[i, j]
            elif i > 0 and j > 0:
                DtwMat[i, j] = distMat[i, j] + min(DtwMat[i, j - 1], DtwMat[i - 1, j], DtwMat[i - 1, j - 1])
            elif i == 0:
                DtwMat[i, j] = distMat[i, j] + DtwMat[i, j - 1]
            elif j == 0:
                DtwMat[i, j] = distMat[i, j] + DtwMat[i - 1, j]
    return DtwMat


def makeEuclideanMatrix(mfcc, data):
    distMat = np.zeros([101, 101], np.float32)
    for i, vector1 in enumerate(data[0].T, 0):
        for j, vector2 in enumerate(mfcc.T, 0):
            distMat[i, j] = distance.euclidean(vector1, vector2)
    return distMat


def DTW(mfcc, trainingDataSet):
    min = 999999999999999999999999999999999
    for data in trainingDataSet:
        # first we will make distance matrix:
        distMat = makeEuclideanMatrix(mfcc, data)
        DwtMat = buildDtwMat(distMat)
        if DwtMat[100, 100] < min:
            min = DwtMat[100, 100]
            choice = data
    return choice


def test(filesPath, trainingDataSet):
    results = []
    for filename in os.listdir(filesPath):
        if filename.endswith(".wav"):
            # load the file
            filePath = os.path.join(filesPath, filename)
            y, sr = librosa.load(filePath, sr=None)
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=1024, hop_length=int(sr * 0.01))
            mfcc_d = librosa.feature.delta(mfcc)
            mfcc = np.concatenate([mfcc, mfcc_d])
            # normalize each feature ZSCORE
            for i in range(26):
                row = mfcc[i, :]
                mfcc[i, :] = stats.zscore(row)
            euclidian_choice = num_to_label[minEuclidianDistance(mfcc, trainingDataSet)[1]]
            dtw_Choice = num_to_label[DTW(mfcc, trainingDataSet)[1]]
            results.append(f"{filename} - {euclidian_choice} - {dtw_Choice}")
    with open("output.txt", "w+") as pred:
        pred.write('\n'.join(str(v) for v in results))


def loadTrainingDataSet(directory):
    trainingDataSet = []
    for dir in os.listdir(directory):
        if dir in accepted_strings:
            inner_directory = directory + dir + '/'
            for filename in os.listdir(inner_directory):
                if filename.endswith(".wav"):
                    filePath = os.path.join(inner_directory, filename)
                    y, sr = librosa.load(filePath, sr=None)
                    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=1024, hop_length=int(sr * 0.01))
                    mfcc_d = librosa.feature.delta(mfcc)
                    mfcc = np.concatenate([mfcc, mfcc_d])
                    for i in range(26):
                        # Zscore
                        row = mfcc[i, :]
                        mfcc[i, :] = stats.zscore(row)
                    trainingDataSet.append([mfcc, label_to_num[dir]])

        else:
            continue
    return trainingDataSet


if __name__ == '__main__':
    directory = r'./train_data/'
    trainingDataSet = loadTrainingDataSet(directory)
    test('./test_files/', trainingDataSet)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
