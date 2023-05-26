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


def rolling_probability(df, roll_in_hours, number_of_samples):
    # Первые индексы после сглаживания будут Nan, запоминаем их
    temp_rows = df['target_value'].iloc[:roll_in_hours*number_of_samples]
    rolling_prob = df['target_value'].rolling(window=roll_in_hours*number_of_samples, min_periods=1, axis='rows').mean()
    rolling_prob.iloc[:roll_in_hours*number_of_samples] = temp_rows
    df['target_value'] = rolling_prob
    return df


def rebuilt_anomaly_interval_streamlit(csv_predict_path, csv_rolled_path, csv_data_path,
                                       json_dir, csv_loss_path,
                                       roll_probability, number_of_samples,
                                       SHORT_THRESHOLD,
                                       LEN_SHORT_ANOMALY,
                                       COUNT_CONTINUE_SHORT,
                                       LONG_THRESHOLD,
                                       LEN_LONG_ANOMALY,
                                       COUNT_CONTINUE_LONG,
                                       COUNT_TOP=3):
    # получение данных csv группы по вероятности аномалии
    for i, (csv, loss, rolled) in enumerate(zip(
                                            sorted(os.listdir(f'{csv_predict_path}')),
                                            sorted(os.listdir(f'{csv_loss_path}')),
                                            sorted(os.listdir(f'{csv_rolled_path}'))
                                            )):
        csv_predict_name = f'{csv_predict_path}{os.sep}{csv}'
        csv_loss_name = f'{csv_loss_path}{os.sep}{loss}'
        csv_rolled_name = f'{csv_rolled_path}{os.sep}{rolled}'
        csv_data_name = csv_data_path

        json_name_begin_index = csv_predict_name.rfind('_')
        json_name_end_index = csv_predict_name.find('.csv')
        json_name = f"{json_dir}{os.sep}group{csv_predict_name[json_name_begin_index:json_name_end_index]}.json"

        dict_list = []
        try:
            logger.info(f'Read_file: {csv_predict_name}')
            anomaly_time_df = pd.read_csv(csv_predict_name)
            data_df = pd.read_csv(csv_data_name)
            #rolled_df = pd.read_csv(csv_rolled_name)

            # Сглаживание и сохранение результата
            rolled_df = rolling_probability(anomaly_time_df, roll_probability, number_of_samples)
            #rolled_df.to_csv(csv_rolled_name, index=False)

            # merge фрейма вероятности с slice csv по timestamp
            if len(rolled_df) != len(data_df):
                logger.info("merge rolled_df with data_df by timestamp")
                time_df = pd.DataFrame()
                time_df['timestamp'] = data_df['timestamp']
                rolled_df = pd.merge(time_df, rolled_df, how='left', on='timestamp')
                rolled_df.fillna(method='ffill', inplace=True)
                rolled_df.fillna(value={"target_value": 0}, inplace=True)
                #rolled_df.to_csv(csv_rolled_name, index=False)
            rolled_df.to_csv(csv_rolled_name, index=False)
            rolled_df.index = rolled_df['timestamp']
            rolled_df = rolled_df.drop(columns=['timestamp'])

            # Сглаживание и сохранение результата
            # rolled_df = rolling_probability(anomaly_time_df, roll_probability, number_of_samples)
            # rolled_df.to_csv(csv_rolled_name, index=False)

            # rolled_df.index = anomaly_time_df['timestamp']
            # rolled_df = anomaly_time_df.drop(columns=['timestamp'])

            loss_df = pd.read_csv(csv_loss_name)
            loss_df.index = loss_df['timestamp']
            loss_df = loss_df.drop(columns=['timestamp'])

            short_treshold = SHORT_THRESHOLD
            long_treshold = LONG_THRESHOLD
            interval_list, idx_list = get_anomaly_interval_streamlit(rolled_df['target_value'],
                                                                     threshold_short=short_treshold,
                                                                     threshold_long=long_treshold,
                                                                     len_long=LEN_LONG_ANOMALY,
                                                                     len_short=LEN_SHORT_ANOMALY,
                                                                     count_continue_short=COUNT_CONTINUE_SHORT,
                                                                     count_continue_long=COUNT_CONTINUE_LONG)
            for j in idx_list:
                top_list = loss_df[j[0]:j[1]].mean().sort_values(ascending=False).index[:COUNT_TOP].to_list()
                report_dict = {
                    "time": (str(rolled_df.index[j[0]]), str(rolled_df.index[j[1]])),
                    "len": j[1] - j[0],
                    "index": j,
                    "top_sensors": top_list
                }
                dict_list.append(report_dict)

            with open(json_name, "w") as outfile:
                json.dump(dict_list, outfile, indent=4)
            logger.info(f'{json_name} has been saved')

        except Exception as e:
            logger.error(e)
