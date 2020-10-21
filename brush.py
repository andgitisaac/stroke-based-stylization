import numpy as np
import skimage
from skimage import io
import scipy
from scipy import ndimage
from matplotlib import pyplot as plt

I = skimage.io.imread("data/shiba.jpg")
I = skimage.img_as_float(I)
H, W, _ = I.shape

steps = [17, 13, 9, 5, 3]
threshold = 0.2

output = np.zeros_like(I)
mask_x, mask_y = np.arange(W), np.arange(H)

for _ in range(2):
    for step in steps:
        
        radius = step * 1.414

        reference_image = np.zeros_like(I)
        for i in range(3):
            reference_image[:, :, i] = scipy.ndimage.gaussian_filter(I[:, :, i], sigma=step)

        difference = np.sum(np.abs(reference_image - output), axis=-1)

        for r_cnt, r in enumerate(range(step, H, 2 * step)):
            for c_cnt, c in enumerate(range(step, W, 2 * step)):
                chunk = difference[r - step:r + step, c - step:c + step]
                
                if np.average(chunk) <= threshold: continue

                cy, cx = np.unravel_index(np.argmax(chunk, axis=None), chunk.shape)
                cy += r_cnt * (2 * step)
                cx += c_cnt * (2 * step)

                ### Rectangle ###
                # y_min, y_max = max(0, cy - step), min(cy + step, H)
                # x_min, x_max = max(0, cx - step), min(cx + step, W)
                # output[y_min:y_max, x_min:x_max, :] = I[cy, cx, :]

                ### Circle ###
                mask = (mask_x[np.newaxis, :] - cx) ** 2 + (mask_y[:, np.newaxis] - cy) ** 2 < radius **2
                for i in range(3):
                    output[:, :, i][mask] = I[cy, cx, i]
                    

montage = np.hstack((I, output))
plt.imshow(montage)
plt.show()

