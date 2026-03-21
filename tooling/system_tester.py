import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent
sys.path.append(str(PACKAGE / "src"))

from messageq import MessageQueue
import pandas as pd
import numpy as np
import cv2
import time

def segment_captures(file_location: Path):
    def receiver_func(ch, method, properties, body):
        data = MessageQueue.body_parse_util(body)
        if "img" in data:
            receiverq.channel.stop_consuming()
            result.append(data["img"])

    labels = [label for label in file_location.iterdir()]
    segments = file_location.parent / "segments"
    segments.mkdir(exist_ok=True)
    senderq = MessageQueue("control-segmentor")
    receiverq = MessageQueue("segmentor-control")
    result = []
    for i, label in enumerate(labels):
        path = segments / label.name
        path.mkdir(exist_ok=True)
        caps = [cap for cap in label.iterdir()]
        for j, img in enumerate(caps):
            img = cv2.imread(str(img))
            data = {"img": img}
            senderq.add_msg(data.copy())
            res = receiverq.get_blocking_msg(receiver_func)
            img_name = path / f"{j}.jpg"
            print(img_name)
            cv2.imwrite(img_name, result[-1])
        result.clear()

def classifier_results(file_location):
    # initial
    def receiver_func(ch, method, properties, body):
        data = MessageQueue.body_parse_util(body)
        if "result" in data:
            receiverq.channel.stop_consuming()
            results.append(data["result"])
    
    captures = [cap for cap in file_location.iterdir()]
    captures = sorted(captures)
    senderq = MessageQueue("control-classifier")
    receiverq = MessageQueue("classifier-control")
    results = []
    times = []
    accuracy = []
    labels = []
    for i, label in enumerate(captures):
        caps = [cap for cap in label.iterdir()]
        print(label)
        if label.name not in ["10", "9"]:
            for j, img in enumerate(caps):
                img = cv2.imread(str(img))
                data = {"img": img}
                senderq.add_msg(data.copy())
                start = time.time()
                res = receiverq.get_blocking_msg(receiver_func)
                end = time.time() - start
                accuracy.append(1 if str(results[-1]) == label.name else 0)
                times.append(end)
                labels.append(label.name)

    return results, times, accuracy, labels

if __name__ == "__main__":
    test_data = PACKAGE / "test-data4" 
    caps = test_data / "capture"
    cap_results, cap_times, caps_accuracy, labels = classifier_results(caps)
    segs = test_data / "segments"
    seg_results, seg_times, seg_accuracy, labels = classifier_results(segs)

    excel_data = {
        "Labels" : labels,
        "Default cap classification": cap_results,
        "Classification times" : cap_times,
        "Classification accuracy" : caps_accuracy,
        "Segmentated classification" : seg_results,
        "Classification times with segmented" : seg_times,
        "Segmented accuracy" : seg_accuracy
        }
    print(f"Accuracy: {np.average(caps_accuracy)}\nSeg accuracy: {np.average(seg_accuracy)}")
    df = pd.DataFrame(data=excel_data)
    df.to_csv(f"text8_classification.csv", index=False)
    df.to_excel("text8_classification.xlsx", index=False)
