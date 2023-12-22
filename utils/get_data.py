#!/usr/bin/python
import pandas as pd

import argparse
import os
import errno

import datetime
from loguru import logger
import clickhouse_connect

METHODS = ["Potentials", "LSTM"]


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        msg = "not a valid date: {0!r}".format(s)
        raise argparse.ArgumentTypeError(msg)


def parse_args():
    parser = argparse.ArgumentParser(description="get data from database to save to output csv")
    parser.add_argument("--version", "-v", action="version", help="print version", version="1.0.0")
    parser.add_argument("--begin", "-b", type=valid_date, help="begin timestamp in format: %Y-%m-%d %H:%M:%S", required=True)
    parser.add_argument("--end", "-e", type=valid_date, help="end timestamp in format: %Y-%m-%d %H:%M:%S", required=True)
    return parser.parse_args()


if __name__ == '__main__':
    logger.info("get_data.py")
    args = parse_args()
    logger.info(args)

    # Проверка даты:
    if args.end < args.begin:
        msg = f"type date correct: begin={args.begin} > end={args.end}"
        logger.error(msg)
        exit(0)

    # Создание директорий
    try:
        os.mkdir("csv_data")
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            exit(0)

    for method in METHODS:
        try:
            os.mkdir(method)
        except OSError as e:
            if e.errno != errno.EEXIST:
                logger.error(e)
                exit(0)

        try:
            os.mkdir(f"{method}{os.sep}csv_loss")
        except OSError as e:
            if e.errno != errno.EEXIST:
                logger.error(e)
                exit(0)

        try:
            os.mkdir(f"{method}{os.sep}csv_predict")
        except OSError as e:
            if e.errno != errno.EEXIST:
                logger.error(e)
                exit(0)

        try:
            os.mkdir(f"{method}{os.sep}csv_rolled")
        except OSError as e:
            if e.errno != errno.EEXIST:
                logger.error(e)
                exit(0)

        try:
            os.mkdir(f"{method}{os.sep}json_interval")
        except OSError as e:
            if e.errno != errno.EEXIST:
                logger.error(e)
                exit(0)

    client = clickhouse_connect.get_client(host='10.23.0.87', username='default', password='asdf')

    try:
        # Получение из таблицы БД срезов
        slice_query = f"SELECT * FROM slices_play " \
                      f"WHERE timestamp >= toDateTime64('{args.begin}', 3, 'Europe/London') AND " \
                      f"timestamp <= toDateTime64('{args.end}', 3, 'Europe/London') " \
                      f"ORDER BY timestamp ASC"

        logger.info(slice_query)
        df_slice = client.query_df(slice_query)
        df_slice.drop(columns=['model_timestamp'], inplace=True)
        # df_slice['timestamp'] = pd.to_datetime(df_slice['timestamp']).dt.tz_localize(None)
        df_slice.to_csv(f"csv_data{os.sep}slices.csv")

        # Количество групп
        group_query = f"SELECT * FROM groups"
        logger.info(group_query)
        df_group = client.query_df(group_query)
        groups = df_group['id'].to_list()
        groups.remove(0)  # Нулевая группа не нужна

        for group in groups:
            logger.info(f"group -> {group}")
            for method in METHODS:
                logger.info(f"method -> {method}")
                if method == "Potentials":
                    begin_date_time_64 = f"toDateTime64('{args.begin}', 3, 'Europe/London')"
                    end_date_time_64 = f"toDateTime64('{args.end}', 3, 'Europe/London')"
                    # Получение из таблицы БД loss для группы
                    loss_query = f"SELECT * FROM potential_loss_{group} " \
                                 f"WHERE (timestamp >= {begin_date_time_64}) AND " \
                                 f"(timestamp <= {end_date_time_64}) " \
                                 f"ORDER BY timestamp ASC"
                    logger.info(loss_query)

                    df_loss = client.query_df(loss_query)
                    df_loss.to_csv(f"{method}{os.sep}csv_loss{os.sep}loss_{group}.csv", index=False)

                    # Получение из таблицы БД предсказаний для группы
                    predict_query = f"SELECT * FROM potential_predict_{group} " \
                                    f"WHERE (timestamp >= {begin_date_time_64}) AND " \
                                    f"(timestamp <= {end_date_time_64}) " \
                                    f"ORDER BY timestamp ASC"
                    logger.info(predict_query)

                    df_db_predict = client.query_df(predict_query)

                    df_predict = pd.DataFrame()
                    df_predict['target_value'] = df_db_predict['probability']
                    df_predict['timestamp'] = df_db_predict['timestamp']

                    df_predict.to_csv(f"{method}{os.sep}csv_predict{os.sep}predict_{group}.csv", index=False)

                if method == "LSTM":
                    # Получение из таблицы БД loss и predict для группы
                    lstm_query = f"SELECT * FROM lstm_group{group} " \
                                 f"WHERE timestamp >= toDateTime('{args.begin}',  3, 'Europe/London') AND " \
                                 f"timestamp <= toDateTime('{args.end}',  3, 'Europe/London') " \
                                 f"ORDER BY timestamp ASC"
                    logger.info(lstm_query)

                    df_lstm = client.query_df(lstm_query)

                    df_loss = df_lstm.drop(columns=['target_value', 'prob', 'count'])
                    df_loss.to_csv(f"{method}{os.sep}csv_loss{os.sep}loss_{group}.csv", index=False)

                    df_predict = pd.DataFrame()
                    df_predict['timestamp'] = df_lstm['timestamp']
                    df_predict['target_value'] = df_lstm['target_value']

                    df_predict.to_csv(f"{method}{os.sep}csv_predict{os.sep}predict_{group}.csv", index=False)

        logger.info("finished")

    finally:
        client.close()
        logger.info("disconnected")


    # with open("config_SOCHI.json", 'r', encoding='utf8') as j:
    #     config_json = json.load(j)
    # print("config SOCHI")
    # with open(f"{DATA_DIR}{os.sep}{config_json['paths']['files']['json_sensors']}", 'r', encoding='utf8') as f:
    #     json_dict = json.load(f)
    #
    # index_group = [list(x.keys())[0] for x in json_dict["groups"]]
    # if index_group[0] == '0':
    #     index_group.remove('0')
    # for group in index_group:
    #     path_to_probability = f"{DATA_DIR}{os.sep}{group}{os.sep}" \
    #                           f"{config_json['paths']['files']['probability_csv']}{group}.csv"
    #     path_to_potentials = f"{DATA_DIR}{os.sep}{group}{os.sep}" \
    #                          f"{config_json['paths']['files']['potentials_csv']}{group}.csv"
    #     path_to_anomaly_time = f"{DATA_DIR}{os.sep}{group}{os.sep}" \
    #                            f"{config_json['paths']['files']['anomaly_time_prob']}{group}.csv"
    #     calculate_anomaly_time_all_df(path_to_probability, path_to_anomaly_time)
