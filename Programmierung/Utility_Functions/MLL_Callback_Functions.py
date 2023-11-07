import os
from matplotlib import ticker
import pandas as pd
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator
import matplotlib.pyplot as plt
import io
import tensorflow as tf
from mlxtend.plotting import plot_confusion_matrix
from sklearn.metrics import confusion_matrix
import numpy as np


def Conv_Resolution(ReducedSize, Value):
    GUI_width = 4056
    GUI_hight = 3042
    return int(Value // (GUI_width / ReducedSize[1]))


def PlotHistoryAndExport(log_Path, logs=None):
    pd.options.mode.chained_assignment = None

    directory_train = os.path.dirname(log_Path + "/train/")
    directory_val = os.path.dirname(log_Path + "/validation/")

    train_event_accumulator = EventAccumulator(directory_train)
    train_event_accumulator.Reload()

    validation_event_accumulator = EventAccumulator(directory_val)
    validation_event_accumulator.Reload()

    Train_loss_event = train_event_accumulator.Scalars("epoch_loss")
    Val_loss_event = validation_event_accumulator.Scalars("epoch_loss")

    Train_acc_event = train_event_accumulator.Scalars("epoch_accuracy")
    Val_acc_event = validation_event_accumulator.Scalars("epoch_accuracy")

    Epochs = [x.step for x in Train_loss_event]
    Train_Loss = [x.value for x in Train_loss_event]
    Val_Loss = [x.value for x in Val_loss_event]
    Train_acc = [x.value for x in Train_acc_event]
    Val_acc = [x.value for x in Val_acc_event]

    Loss_Data = pd.DataFrame(
        {"Epoch": Epochs, "Train_loss": Train_Loss, "Validation_loss": Val_Loss}
    )
    Acc_Data = pd.DataFrame(
        {"Epoch": Epochs, "Train_Accuracy": Train_acc, "Validation_Accuracy": Val_acc}
    )

    Acc_Data["Train_Accuracy"] = Acc_Data["Train_Accuracy"].multiply(100)
    Acc_Data["Validation_Accuracy"] = Acc_Data["Validation_Accuracy"].multiply(100)

    for index in range(len(Loss_Data) - 1):
        if Loss_Data["Epoch"][index + 1] <= Loss_Data["Epoch"][index]:
            Loss_Data["Epoch"][index + 1] = Loss_Data["Epoch"][index] + 1
            Acc_Data["Epoch"][index + 1] = Acc_Data["Epoch"][index] + 1

    Acc_Data.to_excel(log_Path + "/Accuracy_Data.xlsx")
    Loss_Data.to_excel(log_Path + "/Loss_Data.xlsx")

    epoch_best_model = Loss_Data["Validation_loss"].idxmin()

    fig1, ax1 = plt.subplots()

    Loss_Data.plot(kind="line", x="Epoch", y="Train_loss", ax=ax1, linewidth=2)
    Loss_Data.plot(kind="line", x="Epoch", y="Validation_loss", ax=ax1, linewidth=2)
    ax1.set_xlabel("Epochs [-]")
    ax1.set_ylabel("Loss_Training [-]")
    ax1.grid(color="grey", linestyle="--", linewidth=1)
    ax1.axvline(x=epoch_best_model, color="red", linestyle="--", label="Best Epoch")
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(nbins=8, integer=True))
    ax1.legend(loc="best")
    fig1.savefig(log_Path + "/Loss_Plot.png", dpi=300)
    fig1.show()

    fig2, ax2 = plt.subplots()
    Acc_Data.plot(kind="line", x="Epoch", y="Train_Accuracy", ax=ax2, linewidth=2)
    Acc_Data.plot(kind="line", x="Epoch", y="Validation_Accuracy", ax=ax2, linewidth=2)
    ax2.set_xlabel("Epochs [-]")
    ax2.set_ylabel("Accuracy [%]")
    ax2.set_ylim(0, 105)
    ax2.axvline(x=epoch_best_model, color="red", linestyle="--", label="Best Epoch")
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(nbins=8, integer=True))
    ax2.legend(loc="best")
    ax2.grid(color="grey", linestyle="--", linewidth=1)
    fig2.savefig(log_Path + "/Accuracy_Plot.png", dpi=300)


def plot_to_image(figure, Path, save):
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    image = tf.image.decode_png(buf.getvalue(), channels=4)
    image = tf.expand_dims(image, 0)
    return image


def log_confusion_matrix(
    epochs, Validationdataset, Model, Class_Names, Writer, log_Path, logs, save
):
    conf_prediction = []
    conf_label = []

    for image_batch, labels_batch in Validationdataset:
        prediction = Model.predict(image_batch)
        conf_prediction = np.append(conf_prediction, np.argmax(prediction, axis=1))
        conf_label = np.append(conf_label, labels_batch)

    mat = confusion_matrix(conf_label, conf_prediction)
    figure = plot_confusion_matrix(
        conf_mat=mat, figsize=(10, 10), class_names=Class_Names, show_normed=True
    )

    if save == "yes":
        plt.tight_layout()
        plt.savefig(log_Path + "/Best_Confusion_Matrix.png", format="png")

    cm_image = plot_to_image(figure, log_Path, save)

    if save == "yes":
        return

    with Writer.as_default():
        tf.summary.image("Confusion Matrix", cm_image, step=epochs)
