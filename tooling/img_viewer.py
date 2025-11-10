import cv2
from pathlib import Path
import pandas as pd

def img_viewer(log_file):
    package = Path(__file__).parent.parent
    caps = package / log_file / "segment"

    captures = [cap for cap in caps.iterdir()]
    captures = sorted(captures, key=lambda x: int(x.stem))
    classes = []
    for cap in captures:
        img = cv2.imread(str(cap))
        cv2.imshow("cap", img)
        key = cv2.waitKey(0)
        if key == 27:  # ESC key to exit early
            break
        else:
            for i in range(10):
                if key == ord(f'{i}'):
                    classes.append(i)

    cv2.destroyAllWindows()
    df = pd.read_csv(f"{log_file}pl.csv", header=0)
    if df.shape[0] == len(classes):
        data = df.to_dict()
        valid = []
        accuracy = []
        important = []
        for i, _ in enumerate(classes):

            accurate = data["Classifier result"][i] == classes[i]
            nothing = data["Classifier result"][i] == 0
            score = 1 if accurate else 0
            accuracy.append(score)
            validated = data["Validator result"][i] > 95
            if accurate and not validated:
                valid.append(0)
            elif not accurate and validated:
                valid.append(0)
            elif accurate and validated:
                valid.append(1)
            elif not accurate and not validated:
                valid.append(1)
            if accurate and not validated and nothing:
                important.append(1)
            else:
                important.append(valid[i])
        new_data = {}
        new_data["Hand classification"] = classes
        new_data["Classifier accuracy"] = accuracy
        new_data["Validation accuracy"] = valid
        new_data["Validation matters"]  = important
        dfnew = pd.DataFrame(data=new_data)
        df = df.join(dfnew)
        df.to_csv(f"{log_file}.csv", index=False)
        df.to_excel(f"{log_file}.xlsx", index=False)
    else:
        print("Excel length and img length missmatch")

if __name__ == "__main__":
    log_file = "log-test2"
    img_viewer(log_file)
