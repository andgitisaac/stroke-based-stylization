import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from gui import Ui_GUI

import numpy as np
import skimage
from skimage import io
import scipy
from scipy import ndimage

STEP_LIST = list(range(19, 1, -2))
DEFAULT_LEVEL = 2           # Equivalent to 2
DEFAULT_THRESHOLD = 10      # Equivalent to 0.2
DEFAULT_STROKE_SIZE = 40    # Equivalent to 1.4

class GuiProgram(Ui_GUI):
    def __init__(self, dialog):
        Ui_GUI.__init__(self)
        self.setupUi(dialog)

        self.input_img = None
        self.output_img = None
        self.level = DEFAULT_LEVEL
        self.threshold = DEFAULT_THRESHOLD
        self.stroke_size = DEFAULT_STROKE_SIZE

        # Initialize scroll bar values
        self.init_scrollbar()

        # Process the image after loading the image
        self.browse.clicked.connect(self.load_img)   

        # Update the values of scroll bars
        self.level_controller.valueChanged.connect(self.update_scrollbar)
        self.threshold_controller.valueChanged.connect(self.update_scrollbar)
        self.stroke_size_controller.valueChanged.connect(self.update_scrollbar)     

        # Process the image if user change the value using the scroller bars
        self.level_controller.valueChanged.connect(self.brush_stroke_process)
        self.threshold_controller.valueChanged.connect(self.brush_stroke_process)
        self.stroke_size_controller.valueChanged.connect(self.brush_stroke_process)

        # Save output image if save button is pressed
        self.save.clicked.connect(self.save_image)

        # Reset scroll bar if reset button is pressed
        self.reset.clicked.connect(self.reset_scrollbar)

        # Terminate program if Exit button is pressed
        self.exit.clicked.connect(self.terminate)

    # Initialize scroll bar values
    def init_scrollbar(self):
        self.level_controller.setProperty("minimum", 1)
        self.level_controller.setProperty("maximum", len(STEP_LIST))
        self.level_controller.setProperty("value", DEFAULT_LEVEL)
        self.level_controller.setTickInterval(1)

        self.threshold_controller.setProperty("minimum", 0)
        self.threshold_controller.setProperty("maximum", 50)
        self.threshold_controller.setProperty("value", DEFAULT_THRESHOLD)
        self.threshold_controller.setTickInterval(5)

        self.stroke_size_controller.setProperty("minimum", 0)
        self.stroke_size_controller.setProperty("maximum", 100)
        self.stroke_size_controller.setProperty("value", DEFAULT_STROKE_SIZE)
        self.stroke_size_controller.setTickInterval(10)

        self.update_scrollbar()

    # Update the scroll bar values
    def update_scrollbar(self):
        self.level = self.level_controller.value()
        self.level_label.setText("{}".format(self.level))

        self.threshold = (self.threshold_controller.value() - self.threshold_controller.minimum()) \
                            / (self.threshold_controller.maximum() - self.threshold_controller.minimum())
        self.threshold_label.setText("{:.2f}".format(self.threshold))

        self.stroke_size = 1.0 + (self.stroke_size_controller.value() - self.stroke_size_controller.minimum()) \
                                / (self.stroke_size_controller.maximum() - self.stroke_size_controller.minimum())
        self.stroke_size_label.setText("{:.2f}".format(self.stroke_size))
    
    # Reset the scroll bar values to default
    def reset_scrollbar(self):
        self.level_controller.setProperty("value", DEFAULT_LEVEL)
        self.threshold_controller.setProperty("value", DEFAULT_THRESHOLD)
        self.stroke_size_controller.setProperty("value", DEFAULT_STROKE_SIZE)
    
    # Terminate the program
    def terminate(self):
        sys.exit()

    # Save the output image
    def save_image(self):
        if self.output_img is not None:
            fullpath, file_ext = QtWidgets.QFileDialog.getSaveFileName(
                            self.output_window, filter="*.jpg")
            
            if not fullpath: return
            skimage.io.imsave(fullpath, self.output_img)

    # Load the image
    def load_img(self):
        fullpath, file_ext = QtWidgets.QFileDialog.getOpenFileName(
                        self.input_window, filter="*.bmp *.jpg *.png")
        if not fullpath: return
        self.input_img = skimage.io.imread(fullpath)

        if len(self.input_img.shape) != 2 and len(self.input_img.shape) != 3:
            raise ValueError("Input image must be MxN or MxNx3")
        if len(self.input_img.shape) == 2:
            self.input_img = np.dstack((self.input_img, self.input_img, self.input_img))

        self.init_scrollbar()
        self.brush_stroke_process()
        
    # Convert image to Qt image
    def im2qt(self, img):
        H, W, C = img.shape
        BytePerLine = W * C
        qt_img = QtGui.QImage(img.data, W, H, BytePerLine, QtGui.QImage.Format_RGB888)
        qt_img = QtGui.QPixmap(qt_img)
        return qt_img

    # Display the Qt image at the given window
    def display(self, window, qt_img):
        qt_img = qt_img.scaled(window.size(), QtCore.Qt.KeepAspectRatio)
        
        window.setPixmap(qt_img)
        window.setAlignment(QtCore.Qt.AlignCenter)
    
    # Image Process
    def brush_stroke_process(self):
        if self.input_img is None:
            return

        input_img = skimage.img_as_float(self.input_img)
        H, W, C = input_img.shape

        steps = STEP_LIST[:self.level]
        threshold = self.threshold
        stroke_ratio = self.stroke_size

        output_img = np.zeros_like(input_img)
        mask_x, mask_y = np.arange(W), np.arange(H)

    
        for _ in range(1):
            for step in steps:
                radius = step * stroke_ratio
                reference_image = np.zeros_like(input_img)
                for i in range(C):
                    reference_image[:, :, i] = scipy.ndimage.gaussian_filter(input_img[:, :, i], sigma=step)

                difference = np.sum(np.abs(reference_image - output_img), axis=-1)

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
                        mask = (mask_x[np.newaxis, :] - cx) ** 2 + (mask_y[:, np.newaxis] - cy) ** 2 < radius ** 2
                        for i in range(C):
                            output_img[:, :, i][mask] = input_img[cy, cx, i]
                

        self.output_img = skimage.img_as_ubyte(output_img)

        qt_img = self.im2qt(self.input_img)
        self.display(self.input_window, qt_img)

        qt_img = self.im2qt(self.output_img)
        self.display(self.output_window, qt_img)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    dialog = QtWidgets.QDialog()

    prog = GuiProgram(dialog)
    dialog.setWindowTitle("EE568 Final Project")
    dialog.show()
    sys.exit(app.exec_())