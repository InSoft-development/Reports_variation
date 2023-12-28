#!/usr/bin/python
import pandas as pd

import os
import json

from loguru import logger
from get_anomaly_interval import get_anomaly_interval, fill_zeros_with_last_value

METHODS = ["Potentials", "LSTM"]


def rolling_probability(df, roll_in_hours, number_of_samples):
    # Первые индексы после сглаживания будут Nan, запоминаем их
    temp_rows = df['target_value'].iloc[:roll_in_hours*number_of_samples]
    rolling_prob = df['target_value'].rolling(window=roll_in_hours*number_of_samples, min_periods=1, axis='rows').mean()
    rolling_prob.iloc[:roll_in_hours*number_of_samples] = temp_rows
    df['target_value'] = rolling_prob
    return df


if __name__ == '__main__':
    logger.info("get_default_interval.py")

    with open(f"default_interval_config.json", 'r', encoding='utf8') as j:
        default_interval_config = json.load(j)

    for method in METHODS:
        logger.info(f"method -> {method}")

        csv_predict_listdir = sorted(os.listdir(f"{method}{os.sep}csv_predict{os.sep}"))
        csv_loss_listdir = sorted(os.listdir(f"{method}{os.sep}csv_loss{os.sep}"))

        assert len(csv_predict_listdir) == len(csv_loss_listdir)

        # получение csv группы
        for group, (csv, loss) in enumerate(zip(csv_predict_listdir, csv_loss_listdir)):
            dict_list = []
            try:
                df_slices_path = f'csv_data{os.sep}slices.csv'
                df_slices = pd.read_csv(df_slices_path)

                df_predict_path = f'{method}{os.sep}csv_predict{os.sep}predict_{group + 1}.csv'
                df_predict = pd.read_csv(df_predict_path)
                df_predict.fillna(value={"target_value": 0}, inplace=True)

                df_loss_path = f'{method}{os.sep}csv_loss{os.sep}loss_{group + 1}.csv'
                df_loss = pd.read_csv(df_loss_path)
                df_loss.index = df_loss['timestamp']
                df_loss = df_loss.drop(columns=['timestamp'])

                df_rolled_path = f'{method}{os.sep}csv_rolled{os.sep}rolled_{group + 1}.csv'
                intervals_json_path = f'{method}{os.sep}json_interval{os.sep}group_{group + 1}.json'

                # Сглаживание
                df_rolled = rolling_probability(df_predict, default_interval_config["rolling"],
                                                default_interval_config["number_of_samples"])

                # merge фрейма вероятности с slice csv по timestamp
                logger.info("merge rolled_df with df_slices by timestamp")
                time_df = pd.DataFrame()
                time_df['timestamp'] = df_slices['timestamp']
                df_rolled = pd.merge(time_df, df_rolled, how='left', on='timestamp')

                # df_rolled.fillna(method='ffill', inplace=True)
                df_rolled.fillna(value={"target_value": 0}, inplace=True)
                fill_zeros_with_last_value(df_rolled)
                df_rolled.to_csv(df_rolled_path, index=False)

                logger.info(f'{df_rolled_path} has been saved')

                df_rolled.index = df_rolled['timestamp']
                df_rolled = df_rolled.drop(columns=['timestamp'])

                interval_list, idx_list = get_anomaly_interval(df_rolled['target_value'],
                                                               threshold_short=default_interval_config["SHORT_THRESHOLD"],
                                                               threshold_long=default_interval_config["LONG_THRESHOLD"],
                                                               len_long=default_interval_config["LEN_LONG_ANOMALY"],
                                                               len_short=default_interval_config["LEN_SHORT_ANOMALY"],
                                                               count_continue_short=default_interval_config["COUNT_CONTINUE_SHORT"],
                                                               count_continue_long=default_interval_config["COUNT_CONTINUE_LONG"])

                for j in idx_list:
                    top_list = df_loss[j[0]:j[1]].mean().sort_values(ascending=False).index[:default_interval_config["COUNT_TOP"]].to_list()
                    report_dict = {
                        "time": (str(df_rolled.index[j[0]]), str(df_rolled.index[j[1]])),
                        "len": j[1] - j[0],
                        "index": j,
                        "top_sensors": top_list
                    }
                    dict_list.append(report_dict)

                with open(intervals_json_path, "w") as outfile:
                    json.dump(dict_list, outfile, indent=4)
                logger.info(f'{intervals_json_path} has been saved')

            except Exception as e:
                msg = e
                logger.error(msg)
