import copy
import random
import numpy as np
import skimage.metrics
from skimage.io import imsave, imshow, show, imread
from matplotlib import pyplot as plt

decompositionLvl = 3
area = 1/4

def generateW(size, seed):
    rng = np.random.default_rng(seed=seed)
    w = rng.random(size)
    return w


def insertW(f, Lvl, w, alpha):
    sizef = np.shape(f)
    partf = f[sizef[0]//(2**Lvl):sizef[0]//(2**(Lvl-1)), 0:sizef[1]//(2**Lvl)]
    sizePartf = np.shape(partf)
    fmean = np.mean(partf)
    smallfw = copy.copy(partf)
    for i in range(0, len(w)):
        smallfw[i//sizePartf[1], i%sizePartf[1]] = fmean + (partf[i//sizePartf[1], i%sizePartf[1]] - fmean)*(1+alpha*w[i])
    fw = copy.copy(f)
    fw[sizef[0]//(2**Lvl):sizef[0]//(2**(Lvl-1)), 0:sizef[1]//(2**Lvl)] = smallfw
    return fw


def VeyvletHaara(img):
    size = np.shape(img)
    fHorizont = np.zeros_like(img).astype(float)
    fVert = np.zeros_like(img).astype(float)
    for i in range(0, size[0]):
        for j in range(0, size[1], 2):
            fHorizont[i][j//2] = 0.5*img[i][j] + 0.5*img[i][j+1]
            fHorizont[i][(j // 2)+(size[1]//2)] = 0.5*img[i][j] - 0.5*img[i][j + 1]

    for i in range(0, size[0], 2):
        for j in range(0, size[1]):
            fVert[i//2][j] = 0.5*fHorizont[i][j] + 0.5*fHorizont[i+1][j]
            fVert[(i//2)+(size[0]//2)][j] = 0.5*fHorizont[i][j] - 0.5*fHorizont[i+1][j]
    return fVert


def invVeyvletHaara(img):
    size = np.shape(img)
    fHorizont = np.zeros_like(img).astype(float)
    fVert = np.zeros_like(img).astype(float)
    for i in range(0, size[0]//2):
        for j in range(0, size[1]):
            fVert[2*i][j] = img[i][j] + img[i+(size[0]//2)][j]
            fVert[2*i+1][j] = img[i][j] - img[i+(size[0]//2)][j]

    for i in range(0, size[0]):
        for j in range(0, size[1]//2):
            fHorizont[i][2*j] = fVert[i][j] + fVert[i][j+(size[1]//2)]
            fHorizont[i][2*j+1] = fVert[i][j] - fVert[i][j+(size[1]//2)]
    return fHorizont


def DVTwithLvlDecomposition(img, decompositionLvl):
    size = np.shape(img)
    ResF = VeyvletHaara(img)
    partF = ResF[0:size[0]//2, 0:size[1]//2]
    for i in range(1, decompositionLvl):
        ResF[0:(size[0]//(2**i)), 0:(size[1]//(2**i))] = VeyvletHaara(partF)
        partF = ResF[0:(size[0]//(2*2**i)), 0:(size[1]//(2*2**i))]
    return ResF


def invDVTwithLvlDecomposition(img, Lvl):
    size = np.shape(img)
    ResF = copy.copy(img)
    for i in range(0, Lvl):
        partF = ResF[0:size[0] // (2 ** (Lvl - i - 1)), 0:size[1] // (2 ** (Lvl - i - 1))]
        ResF[0:size[0] // (2 ** (Lvl - i - 1)), 0:size[1] // (2 ** (Lvl - i - 1))] = invVeyvletHaara(partF)
    return ResF


def rateW(fw, f, alpha, Lvl):
    sizef = np.shape(f)
    partfw = fw[sizef[0]//(2**Lvl):sizef[0]//(2**(Lvl-1)), 0:sizef[1]//(2**Lvl)]
    partf = f[sizef[0]//(2 ** Lvl):sizef[0]//(2 ** (Lvl - 1)), 0:sizef[1]//(2 ** Lvl)]

    sizePartf = np.shape(partf)
    fmean = np.mean(partf)
    w = []
    for i in range(0, sizePartf[0]*sizePartf[1]):  #
        w.append((partfw[i//sizePartf[1], i%sizePartf[1]] - partf[i//sizePartf[1], i%sizePartf[1]]) /
                 (alpha*(partf[i//sizePartf[1], i%sizePartf[1]]-fmean)))
    return w


def detector(w, wnew):
    w_ = wnew[0:len(w)]
    # print(w)
    # print(w_)
    sum = 0
    for i in range(0, len(w)):
        sum += w[i]*w_[i]
    sum1 = np.sum(np.square(w_))
    sum2 = np.sum(np.square(w))
    print(sum, sum2, sum1)
    delimiter = np.sum(np.square(w_)) * np.sum(np.square(w))
    p = sum/np.sqrt(delimiter)
    return p


# для визуального восприятия спектра
def contrastDecomposition(img):
    size = np.shape(img)
    contrast = copy.copy(img)
    LL = copy.copy(np.abs(contrast[0:size[0] // 2, 0:size[1]//2]))
    LH = copy.copy(np.abs(contrast[0:size[0]//2, size[1]//2:]))
    HL = copy.copy(np.abs(contrast[size[0]//2:, 0:size[1]//2]))
    HH = copy.copy(np.abs(contrast[size[0]//2:, size[1]//2:]))
    lin = np.vectorize(linary)
    contrastLL = lin(LL, np.min(LL), np.max(LL))
    contrastLH = lin(LH, np.min(LH), np.max(LH))
    contrastHL = lin(HL, np.min(HL), np.max(HL))
    contrastHH = lin(HH, np.min(HH), np.max(HH))
    contrast[0:size[0] // 2, 0:size[1]//2] = contrastLL
    contrast[0:size[0]//2, size[1]//2:] = contrastLH
    contrast[size[0]//2:, 0:size[1]//2] = contrastHL
    contrast[size[0]//2:, size[1]//2:] = contrastHH
    return contrast


def contrastF(img, Lvl):
    size = np.shape(img)
    ResF = contrastDecomposition(img)
    LL = ResF[0:size[0] // 2, 0:size[1] // 2]
    for i in range(1, Lvl):
        ResF[0:(size[0] // (2 ** i)), 0:(size[1] // (2 ** i))] = contrastDecomposition(LL)
        LL = ResF[0:(size[0] // (2 * 2 ** i)), 0:(size[1] // (2 * 2 ** i))]
    return ResF


def linary(img, fmin, fmax):
    if img < fmin:
        img = 0.0
    elif img > fmax:
        img = 255.0
    else:
        img = 255*(img - fmin)/(fmax-fmin)
    return img


if __name__ == '__main__':
    C = imread("C:/Users/Никита/Desktop/стеганография/лаба2/bridge.tif").astype(int)
    #1
    sizeC = np.shape(C)
    n = int(area*(sizeC[0]//(2**decompositionLvl))*(sizeC[1]//(2**decompositionLvl)))
    W = generateW(n, 1)

    #2
    F = DVTwithLvlDecomposition(C, decompositionLvl)  # получили спектр
    CC = invDVTwithLvlDecomposition(F, decompositionLvl)
    #3
    bestA = 0
    alpha = 0.05
    ro = 0
    r = 0
    psnrMin = 1000
    psnr = 0
    for i in range(20):
    # while ro <= 0.9:
        Fw = insertW(F, decompositionLvl, W, alpha)  # встроили знак в спектр
        #4
        CW = invDVTwithLvlDecomposition(Fw, decompositionLvl)  # получили изображение со встроенным знаком
        imsave("CW.png", CW)
        #5
        savedCW = imread("CW.png")
        newFw = DVTwithLvlDecomposition(savedCW, decompositionLvl)
        #6
        newW = rateW(newFw, F, alpha, decompositionLvl)
        ro = detector(W, newW)  #???
        psnr = skimage.metrics.peak_signal_noise_ratio(C, savedCW)
        if (ro > 0.9) & (psnr < psnrMin):
            bestA = alpha
            psnrMin = psnr
            r = ro
            print(f"i: {i}\tp: {r}\tpsnr: {psnr}\ta: {alpha}")
        alpha += 0.05
    print(f"p: {r}\tpsnr: {psnr}\tbest a: {bestA}")

    #8


    # вывод изображений
    viewF = contrastF(F, decompositionLvl)
    fig = plt.figure(figsize=(20, 10))
    fig.add_subplot(1, 2, 1)
    imshow(C, cmap="gray")
    fig.add_subplot(1, 2, 2)
    imshow(viewF, cmap="gray")

    fig2 = plt.figure(figsize=(20, 10))
    fig2.add_subplot(1, 2, 1)
    imshow(C, cmap="gray")
    fig2.add_subplot(1, 2, 2)
    imshow(savedCW.astype(float), cmap="gray")

    lin = np.vectorize(linary)
    difImg = lin((C - savedCW).astype(float), np.min((C - savedCW).astype(float)), np.max((C - savedCW).astype(float)))
    difF = contrastF((Fw-newFw), decompositionLvl)
    fig3 = plt.figure(figsize=(20, 10))
    fig3.add_subplot(1, 2, 1)
    imshow(difImg, cmap="gray")
    fig3.add_subplot(1, 2, 2)
    imshow(difF, cmap="gray")
    print(np.average(np.abs(W-newW[0:len(W)])))
    show()