#!/usr/bin/python
from loguru import logger


def get_anomaly_interval(loss, threshold_short, threshold_long, len_long, len_short, count_continue_short=10,
                         count_continue_long=15):
    long_interval_list = []
    short_interval_list = []
    loss_interval = []
    count = 0
    i = 0
    long_idx_list = []
    short_idx_list = []
    sum_anomaly = 0
    for val in loss:
        i += 1
        if val > threshold_long:
            loss_interval.append(val)
        else:
            count += 1
            loss_interval.append(val)
            if count > count_continue_long:
                if len(loss_interval) > len_long:
                    long_interval_list.append(loss_interval)
                    logger.info(f'Add anomaly long interval, len {len(loss_interval)}')
                    if i - len(loss_interval) > 0:
                        long_idx_list.append((i - len(loss_interval), i))
                    else:
                        long_idx_list.append((0, i))
                    sum_anomaly += len(loss_interval)
                count = 0
                loss_interval.clear()

    i = 0
    for val in loss:
        i += 1
        if val > threshold_short:
            loss_interval.append(val)
        else:
            count += 1
            loss_interval.append(val)
            if count > count_continue_short:
                if len(loss_interval) > len_short:
                    isInLong = any(start <= i - len(loss_interval) < end for start, end in long_idx_list)
                    if not isInLong:
                        short_interval_list.append(loss_interval)
                        logger.info(f'Add anomaly short interval, len {len(loss_interval)}')
                        if i - len(loss_interval) > 0:
                            short_idx_list.append((i - len(loss_interval), i))
                        else:
                            short_idx_list.append((0, i))
                        sum_anomaly += len(loss_interval)
                count = 0
                loss_interval.clear()

    logger.info(f'Sum anomaly {sum_anomaly}, part of anomaly {round(sum_anomaly / len(loss), 3)}')
    return long_interval_list + short_interval_list, long_idx_list + short_idx_list


def fill_zeros_with_last_value(df, count_next=288):
    count = 0
    for index, row in df.iterrows():
        if row['target_value'] == 0:
            if count == 0:
                start_index = index
                last_value = df.iloc[index-1]['target_value']
            count += 1
        if row['target_value'] != 0 and count != 0:
            if count < count_next:
                df.loc[start_index:index-1, 'target_value'] = last_value
            count = 0
