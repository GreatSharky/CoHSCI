import pandas as pd
from pathlib import Path
import datetime
import csv

from img_viewer import img_viewer

def analyse_logs(log_name):
    def add_data(data):
        for key in data:
            df[key].append(data[key])
    file_path = Path(__file__).resolve().parent.parent
    classifier = file_path / log_name / "classifier.log"
    with open(classifier, "r") as file:
        cl_lines = file.readlines()

    for line in cl_lines:
        if "Classifying..." in line:
            start_time = line.split(": ")[0]
            stime = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
        elif "Classification" in line:
            end_time = line.split(": ")[0]
            etime = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
            result = line.split(" - ")[1].split(" ")[1].strip()
            dtime = etime-stime
            add_data({"Classifier start": start_time, "Classifier end" : end_time, "Classifier result" : result, "Classifier time" : str(dtime)})
    validator = file_path / log_name / "validator.log"
    with open(validator, "r") as file:
        vl_lines = file.readlines()

    for line in vl_lines:
        if "Validating ..." in line:
            start_time = line.split(": ")[0]
            stime = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
        elif "Validation result" in line:
            end_time = line.split(": ")[0]
            etime = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
            result = line.split(" - ")[1].split(": ")[2].split("}")[0].strip("'")
            dtime = etime-stime
            add_data({"Validator start": start_time, "Validator end" : end_time, "Validator result" : result, "Validator time" : str(dtime)})

    segmentor = file_path / log_name / "segment.log"
    if Path(segmentor).exists():
        with open(segmentor, "r") as file:
            sg_lines = file.readlines()

        for line in sg_lines:
            if "Msg recieved" in line:
                start_time = line.split(": ")[0]
                stime = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
            elif "Results ready" in line:
                end_time = line.split(": ")[0]
                etime = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S,%f") # 2025-10-22 12:24:26,367
                dtime = etime-stime
                add_data({"Segmentor start": start_time, "Segmentor end" : end_time, "Segmentor time" : str(dtime)})
    else:
        df["Segmentor start"] = [None for i in df["Classifier start"]]
        df["Segmentor end"] = [None for i in df["Classifier start"]]
        df["Segmentor time"] = [None for i in df["Classifier start"]]


    print(log_name)
    for key in df:
        print(key, len(df[key]))


def time_stats_from_excel(filename, columns):
    """
    Reads all sheets from an Excel file and computes average and standard deviation
    for specified time-formatted columns.

    Returns:
        dict: {sheet_name: {column_name: [mean, std]}}
    """
    # Read all sheets as a dict of DataFrames
    sheets = pd.read_excel(filename, sheet_name=None)

    results = {}

    for sheet_name, df in sheets.items():
        sheet_results = {}

        for col in columns:
            if col in df.columns:
                df[col] = pd.to_timedelta(df[col], errors="coerce")
                sheet_results[col] = [df[col].mean(), df[col].std()]

        results[sheet_name] = sheet_results

    return results



if __name__ == "__main__":
    for i in range(9,13):
        df = {
            "Segmentor start" : [], 
            "Segmentor end" : [], 
            "Segmentor time" : [],
            "Classifier start" : [], 
            "Classifier end" : [], 
            "Classifier time" : [],
            "Classifier result" : [],
            "Validator start" : [],
            "Validator end" : [],
            "Validator time" : [],
            "Validator result" : [],
            }
        log_name = f"log-{i}"
        analyse_logs(log_name)
        df = pd.DataFrame(data=df, dtype=str)
        df.to_csv(f"{log_name}pl.csv", index=False)
        df.to_excel(f"{log_name}pl.xlsx", index=False)
        print(f"Excel and csv written. {df.shape[0]} lines written.")
        img_viewer(log_name)
