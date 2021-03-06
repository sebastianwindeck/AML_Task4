
import numpy as np
from scipy import ndimage
import os
import inspect
import scipy.ndimage
import pylab as pyl
import cv2
from matplotlib import pyplot as plt
from skvideo.io import vwrite

from helpers.plotter import plot



def retrieve_name(var):
    """
    Gets the name of var. Does it from the out most frame inner-wards.
    :param var: variable to get name from.
    :return: string
    """
    for fi in reversed(inspect.stack()):
        names = [var_name for var_name, var_val in fi.frame.f_locals.items() if var_val is var]
        if len(names) > 0:
            return names[0]


def scale(df, resolution=0.5):
    """
    :param df: 5d-array [sample, steps, height, width, channels]
    :param resolution: float (0,1)
    """

    df = ndimage.zoom(input=df, zoom=(1, 1, resolution, resolution, 1), order=1)
    print("Scaled")

    return df


def normalize(df):
    df_max_frame = np.max(abs(df), axis=0)
    df = df / df_max_frame.astype(float)
    print("Normalized")
    return df


def cropping(df, left, right, up, down):
    print("Shape before Cropping: ", df.shape)
    df = df[:, :, up:df.shape[2] - down, left:df.shape[3] - right, :]
    print("Shape after Cropping: ", df.shape)
    return df


def list_to_array(x_data, maxtime):
    x_array = np.zeros((x_data.shape[0], maxtime, x_data[0].shape[1], x_data[0].shape[2]))
    min_list = []
    for i in np.arange(x_data.shape[0]):
        v = x_data[i]
        x_array[i, :v.shape[0], :v.shape[1], :v.shape[2]] = v
        min_list.append(x_data[i].shape[0])

    x_array = x_array[:, :, :, :, np.newaxis]

    #plt.hist(min_list, normed=True, bins=30)
    #plt.ylabel('Frequency')
    #plt.show()

    return x_array


def max_time(x):
    maxtime = 0
    for i in np.arange(x.shape[0]):
        maxtime = np.max((maxtime, (x[i]).shape[0]))

    return maxtime


def min_time(x):
    mintime = 1000
    for i in np.arange(x.shape[0]):
        mintime = np.min((mintime, (x[i]).shape[0]))

    return mintime


def cut_time_steps(x, length):
    x = x[:, :length, :, :, :]
    print("Length Cut")
    return x

def blur_filtering(df, kernel_size = 5):
    df = df.astype(np.uint8)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            blur = cv2.GaussianBlur(df[i, j, :, :, 0], (kernel_size,kernel_size),0)
            df[i, j, :, :, 0] = blur

    return df

def binarize(df,thresh):

    for i in range(df.shape[0]):
        for t in range(df.shape[1]):
            a = np.zeros((df.shape[2],df.shape[3]))
            d = df[i,t,:,:,0]
            d = d / d.max()

            for k in range(a.shape[0]):
                for l in range(a.shape[1]):
                    if (d[k, l] > thresh * d.mean()):
                        a[k, l] = 1
                    else:
                        a[k, l] = 0
            df[i,t,:,:,0]=a

    return df

def gaussian_filtering(df, sigma):
    # input: array x of size (n_samples, n_timesteps, height, width,1)
    # input: sigma for gaussioan filter
    # output: array with same shape as x, filtered

    for i in np.arange(df.shape[0]):
        for j in np.arange(df.shape[1]):
            df[i][j, :, :] = scipy.ndimage.gaussian_filter(df[i][j, :, :], sigma)

    return df


def finderContour(df, tresh_min=5, tresh_max=255):
    df = df.astype(np.uint8)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            img = cv2.convertScaleAbs(df[i, j, :, :, 0])
            (thresh, im_bw) = cv2.threshold(img, tresh_min, tresh_max, 0)
            im2, contours, hierarchy = cv2.findContours(im_bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            drawing = np.zeros((img.shape[0], img.shape[1]), np.uint8)
            img = cv2.drawContours(drawing, contours, -1, 255, 1)
            df[i, j, :, :, 0] = img

    return df


def edge_filter(df, sigma):
    # input: array x of size (n_samples, n_timesteps, height, width)
    # the images need to be of size n x n (squares)!!!
    # input: sigma for edge filter
    # output: array with same shape as x, filtered
    # note: I have not looked at how this works. I copied it from
    # http://nbviewer.jupyter.org/github/gpeyre/numerical-tours/blob/master/python/segmentation_1_edge_detection.ipynb#
    print("Shape before Edge Filter: ", df.shape)
    n = df.shape[2]
    cconv = lambda f, h: np.real(pyl.ifft2(pyl.fft2(f) * pyl.fft2(h)))
    T = np.hstack((np.arange(0, n // 2 + 1), np.arange(-n // 2 + 1, 0)))
    [X2, X1] = np.meshgrid(T, T)
    normalize = lambda h: h / np.sum(h)
    h = lambda sigma: normalize(np.exp(-(X1 ** 2 + X2 ** 2) / (2 * sigma ** 2)))
    blur = lambda f, sigma: cconv(f, h(sigma))
    s = np.hstack(([n - 1], np.arange(0, n - 1)))
    nabla = lambda f: np.concatenate(((f - f[s, :])[:, :, np.newaxis], (f - f[:, s])[:, :, np.newaxis]), axis=2)

    for i in np.arange(df.shape[0]):
        for j in np.arange(df.shape[1]):
            df[i, j, :, :, 0] = np.sqrt(np.sum(nabla(blur(df[i, j, :, :, 0], sigma)) ** 2, 2))
    print("Shape after Edge Filter: ", df.shape)
    print('Edge filtered')
    return df


def canny_filter(df):
    df = df.astype(np.uint8)
    for i in range(df.shape[0]):
        for j in range(df.shape[1]):
            edges = cv2.Canny(df[i, j, :, :, :], 50, 50)
            df[i, j, :, :, 0] = edges

    return df


def preprocessing(x_data, max_time, normalizing=True, scaling=True, resolution=1, cut_time=True, length=100, crop=25, filter='no',binary=True):
    df = list_to_array(x_data, max_time)
    #plot(df)
    if cut_time:
        df = cut_time_steps(df, length)
       # plot(df)
    if normalizing:
        df = normalize(df)
        #plot(df)
    if scaling:
        df = scale(df, resolution)
       # plot(df)
    df = blur_filtering(df,3)
    #plot(df)
    if filter == 'edge':
        df = edge_filter(df, sigma=1)
      #  plot(df)
    elif filter == 'canny':
        df = canny_filter(df)
       # plot(df)
    elif filter == 'finder':
        df = finderContour(df, tresh_min = 10)
    else:
        pass
    df = cropping(df, left=2, right=2, up=2, down=2)


    if binary==True:
        df = binarize(df,thresh=2.5)


   # plot(df)
    file = retrieve_name(x_data)

    if not os.path.exists("data/filtered/"):
        os.makedirs("data/filtered/")

    for i in range(df.shape[0]):
        vwrite("data/filtered/filtered_" + str(file) + "_" + str(i) +".avi", df[i,:,:,:,:])

    try:
        path = 'data/numpy/' + str(file)
        path = os.path.abspath(path)
        np.save(path, df)
        print("Saved.")
    except:
        pass

    return df
