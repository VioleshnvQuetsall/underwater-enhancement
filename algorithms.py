import numpy as np
import matplotlib.pyplot as plt
import cv2

'''
dtype of all input and output images is asserted to be np.float64
color image: color channel order of BGR
             dimension of (H, W, C)
gray image:  dimension of (H, W)
'''


def float2uint(image):
    return (image * 255).astype(np.uint8)

def uint2float(image):
    return image.astype(np.float64) / 255

def plot_hist(image, ax=plt, title=None):
    image = float2uint(image)
    for i, c in enumerate('bgr'):
        histr = cv2.calcHist([image], [i], None, [256], [0, 256])
        ax.plot(histr, color=c)
        if ax is plt:
            ax.title(title)
            ax.xlim([0,256])
        else:
            ax.set_title(title)
            ax.set_xlim([0,256])

def plot_image(image, ax=plt, title=None, cmap='Greys_r'):
    if len(image.shape) == 3:
        image = image[..., [2, 1, 0]]
    ax.imshow(image, cmap=cmap)
    ax.axis('off')
    if ax is plt:
        ax.title(title)
    else:
        ax.set_title(title)

def gray_world(image):
    ave = np.average(image, axis=(0, 1))
    return (image * (np.average(ave) / ave))

def red_equalize(image):
    image = float2uint(image)
    eq_r = cv2.equalizeHist(image[..., 2])
    image = cv2.merge([image[..., 0], image[..., 1], eq_r])
    return uint2float(image)

def weights(image):
    # laplacian edge, saliency detection, saturation
    image = float2uint(image)
    laplace = cv2.Laplacian(cv2.cvtColor(image,
                                         cv2.COLOR_BGR2GRAY),
                                         cv2.CV_16S, ksize=3)
    laplace = np.abs(uint2float(laplace))

    saliency = cv2.saliency.StaticSaliencyFineGrained_create()
    _, saliencyMap = saliency.computeSaliency(image)

    sat = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)[..., 2]
    sat = uint2float(sat)

    return laplace, saliencyMap, sat

def normalize_weights(weights, delta=0.1):
    # operation: stack   <->  list
    # type:      ndarray <->  list
    weights = np.stack(weights) + delta
    weight_sum = np.sum(weights, axis=0)
    return list(weights / weight_sum)

def gamma_and_sharpen(image, kernel_size=9, sharp_gamma_c=1.8,
                      sharp_c=0.3, gamma_c=2.2):
    edge = image - cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    sharp_image = np.clip(image ** sharp_gamma_c + edge * sharp_c, 0, 1)
    gamma_image = image ** gamma_c

    return gamma_image, sharp_image

def compensate(image, alpha=1.0, channel=2):
    g = image[..., 1]
    c = image[..., channel]
    g_mean = np.average(g)
    c_mean = np.average(c)

    # compensate channel
    cc = c + alpha * (g_mean - c_mean) * (1 - c) * g
    image = np.copy(image)
    image[..., channel] = cc
    return image

def compensate_white_balancing(image, red_c=2.1, blue_c=3.2,
                               apply_gray_world=True):
    image = compensate(image, red_c, 2)
    image = compensate(image, blue_c, 0)
    if apply_gray_world:
        wb = cv2.xphoto.createGrayworldWB()
        image = wb.balanceWhite(float2uint(image))
        return uint2float(image)
        # return gray_world(image)
    else:
        return image

def gaussian_pyramid(image, n):
    gps = [np.copy(image)]
    for _ in range(1, n):
        gp = cv2.pyrDown(gps[-1])
        gps.append(gp)
    return gps

def laplacian_pyramid(gaussian_pyramid):
    n = len(gaussian_pyramid)
    lps = []
    for i in range(1, n):
        # laplacian = image - gaussian
        prev = gaussian_pyramid[i-1]
        curr = cv2.pyrUp(gaussian_pyramid[i])

        size = prev.shape[1], prev.shape[0]
        curr = cv2.resize(curr, size)
        lps.append(prev - curr)
    lps.append(gaussian_pyramid[-1])

    return lps

def reconstruct(laplacian_pyramid):
    # shape: H, W, C, size: W, H
    shape = laplacian_pyramid[0].shape
    size = shape[1], shape[0]

    # merge all images in the laplacian pyramid
    stack = np.stack([cv2.resize(lp, size) for lp in laplacian_pyramid])
    return np.sum(stack, axis=0)

def fusion(images, weights, n=5):
    res = []
    for i, w in zip(images, weights):
        # laplacian pyramid of image and gaussian pyramid of weight
        lps = laplacian_pyramid(gaussian_pyramid(i, n))
        gps = gaussian_pyramid(w, n)
        # add channel axis to allow broadcast
        re = reconstruct([g.reshape(*g.shape, 1) * l for l, g in zip(lps, gps)])
        res.append(re)
    reconstruct_image = np.clip(np.sum(np.stack(res), axis=0), 0, 1)
    return reconstruct_image
