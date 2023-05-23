import json
import os

import pandas as pd
from loguru import logger


def get_anomaly_interval_streamlit(loss, threshold_short, threshold_long,
                                   len_long, len_short,
                                   count_continue_short=10, count_continue_long=15):
    interval_list = []
    loss_interval = []
    count = 0
    i = 0
    idx_list = []
    sum_anomaly = 0
    for val in loss:
        i += 1
        if val > threshold_long:
            loss_interval.append(val)
            count = 0
        else:
            count += 1
            loss_interval.append(val)
            if count > count_continue_long:
                if len(loss_interval) > len_long:
                    interval_list.append(loss_interval)
                    logger.info(f'Add anomaly interval, len {len(loss_interval)}')
                    if i - len(loss_interval) > 0:
                        idx_list.append((i - len(loss_interval), i))
                    else:
                        idx_list.append((0, i))
                    sum_anomaly += len(loss_interval)
                count = 0
                loss_interval.clear()
    i = 0
    for val in loss:
        i += 1
        if val > threshold_short:
            loss_interval.append(val)
            count = 0
        else:
            count += 1
            loss_interval.append(val)
            if count > count_continue_short:
                if len(loss_interval) > len_short:
                    interval_list.append(loss_interval)
                    logger.info(f'Add anomaly interval, len {len(loss_interval)}')
                    if i - len(loss_interval) > 0:
                        idx_list.append((i - len(loss_interval), i))
                    else:
                        idx_list.append((0, i))
                    sum_anomaly += len(loss_interval)
                count = 0
                loss_interval.clear()

    logger.info(f'Sum anomaly {sum_anomaly}, part of anomaly {round(sum_anomaly / len(loss), 3)}')
    return interval_list, idx_list


def rebuilt_anomaly_interval_streamlit(csv_predict_path, json_dir, csv_loss_path, SHORT_THRESHOLD,
                                       LEN_SHORT_ANOMALY,
                                       COUNT_CONTINUE_SHORT,
                                       LONG_THRESHOLD,
                                       LEN_LONG_ANOMALY,
                                       COUNT_CONTINUE_LONG,
                                       COUNT_TOP=3):
    # получение данных csv группы по вероятности аномалии
    for i, (csv, loss) in enumerate(zip(sorted(os.listdir(f'{csv_predict_path}')),
                                      sorted(os.listdir(f'{csv_loss_path}')))):
        csv_predict_name = f'{csv_predict_path}{os.sep}{csv}'
        csv_loss_name = f'{csv_loss_path}{os.sep}{loss}'
        dict_list = []
        try:
            logger.info(f'Read_file: {csv_predict_name}')
            anomaly_time_df = pd.read_csv(csv_predict_name)
            anomaly_time_df.index = anomaly_time_df['timestamp']
            anomaly_time_df = anomaly_time_df.drop(columns=['timestamp'])

            loss_df = pd.read_csv(csv_loss_name)
            loss_df.index = loss_df['timestamp']
            loss_df = loss_df.drop(columns=['timestamp'])

            short_treshold = SHORT_THRESHOLD
            long_treshold = LONG_THRESHOLD
            interval_list, idx_list = get_anomaly_interval_streamlit(anomaly_time_df['target_value'],
                                                                     threshold_short=short_treshold,
                                                                     threshold_long=long_treshold,
                                                                     len_long=LEN_LONG_ANOMALY,
                                                                     len_short=LEN_SHORT_ANOMALY,
                                                                     count_continue_short=COUNT_CONTINUE_SHORT,
                                                                     count_continue_long=COUNT_CONTINUE_LONG)
            for j in idx_list:
                top_list = loss_df[j[0]:j[1]].mean().sort_values(ascending=False).index[:COUNT_TOP].to_list()
                    #loss_df[j[0]:j[1]].drop(columns='timestamp').mean().sort_values(ascending=False).index[:COUNT_TOP].to_list()
                report_dict = {
                    "time": (str(anomaly_time_df.index[j[0]]), str(anomaly_time_df.index[j[1]])),
                    "len": j[1] - j[0],
                    "index": j,
                    "top_sensors": top_list
                }
                dict_list.append(report_dict)

            with open(f"{json_dir}{os.sep}group_{i+1}.json", "w") as outfile:
                json.dump(dict_list, outfile, indent=4)

        except Exception as e:
            logger.error(e)
