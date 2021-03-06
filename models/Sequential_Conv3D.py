from datetime import datetime

import numpy as np
from keras.callbacks import EarlyStopping
from keras.layers import Conv3D, MaxPooling3D, Flatten, Conv1D, MaxPooling1D, Reshape
from keras.layers import Dense, Dropout
from keras.models import Sequential
from helpers.plotter import plot
from helpers.metrics import confusion_metric_vis
from keras import regularizers


def build_sequential(nb_steps, nb_width, nb_height, input_channels, filter, kernel_size):
    # define CNN model
    model = Sequential()
    # Cropping upper half and quarter left quarter right
    model.add(Conv3D(16, kernel_size, strides=(2,2,2), activation='relu', padding='same', data_format='channels_last',
                     input_shape=(nb_steps, nb_width, nb_height, input_channels)))
    model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    model.add(Conv3D(20, kernel_size, strides=(1,1,1), activation='relu', padding='same'))
    model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    model.add(Conv3D(20, kernel_size, strides=(1,1,1), activation='relu', padding='same'))
    model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    #model.add(Conv3D(40, kernel_size, strides=(1,1,1), activation='relu', padding='same', kernel_regularizer=regularizers.l2(0.01)))
    #model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    #model.add(Conv3D(40, kernel_size, strides=(1,1,1), activation='relu', padding='same'))
    #model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    #model.add(Conv3D(80, kernel_size, strides=(1,1,1), activation='relu', padding='same'))
    #model.add(MaxPooling3D(pool_size=(2, 2, 2), strides=(1,2,2)))
    #model.add(Reshape(target_shape=(nb_steps-5, -1)))
    #model.add(Conv1D(32, kernel_size=3, activation='relu'))
    #model.add(MaxPooling1D())
    #model.add(Conv1D(64, kernel_size=3,  activation='relu'))
    #model.add(MaxPooling1D())
    #model.add(Conv1D(64, kernel_size=3,  activation='relu'))
    #model.add(MaxPooling1D())
    #model.add(Conv1D(128, kernel_size=3,  activation='relu'))
    #model.add(MaxPooling1D())
    model.add(Flatten())
    #model.add(Dense(128, activation='relu', name='first_dense', kernel_regularizer=regularizers.l2(0.1)))
    #model.add(Dropout(0.5))
    model.add(Dense(32, activation="relu", name="second_dense", kernel_regularizer=regularizers.l2(0.01)))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation='sigmoid', name="last_dense"))

    model.compile(optimizer='adadelta',

                  loss='binary_crossentropy',
                  metrics=['accuracy'])  # ,final_metric

    return model


def evaluate_sequential(X, y, x_test):
    # Hyperparameter!

    #filter = 32 disabled
    patience = 1
    batch_size = 1
    epochs = 200

    kernel_size = (10,5,5)

    print("Shape before Model: ", X.shape)
    nb_samples, nb_steps, nb_width, nb_height, input_channels = X.shape
    print('\nfunctional_net ({} samples by {} series)'.format(nb_samples, nb_steps))

    #plot(X)
    model = build_sequential(kernel_size=kernel_size, nb_steps=nb_steps, nb_width=nb_width, nb_height=nb_height,
                             filter=filter, input_channels=input_channels)  # , Neurons = Neurons
    # print('\nModel with input size {}, output size {}, {} conv filters of length {}'.format(model.input_shape))

    print(model.summary())
    print('\nInput features:', X.shape, '\nOutput labels:', y.shape, sep='\n')

    earlystop = EarlyStopping(monitor='val_loss', min_delta=0.0, patience=patience, verbose=2,
                              mode='auto')
    time_before = datetime.now()
    model.fit(X, y,
              epochs=epochs, batch_size=batch_size, validation_split=0.2, shuffle=True, callbacks=[earlystop],
              )  # , class_weight=class_weights
    time_after = datetime.now()

    print("fitting took {} seconds".format(time_after - time_before))

    y_pred = model.predict(X)
    y_true = y
    try:
        confusion_metric_vis(y_true=y_true, y_pred=y_pred)
    except:
        pass

    y_test = model.predict(x_test)

    return y_test
