import os
import errno
from loguru import logger

logger.info(f"start utils{os.sep}prepare_structure.py")

DATA_DIR = f'..{os.sep}Data{os.sep}'
WEB_APP_DIR = f'..{os.sep}web_app{os.sep}'
WEB_APP_REPORTS_DIR = f'{WEB_APP_DIR}Reports{os.sep}'
METHODS = ["Potentials", "LSTM"]

try:
    os.mkdir(f'{WEB_APP_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)

try:
    os.mkdir(f'{WEB_APP_REPORTS_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)

try:
    os.mkdir(f'{DATA_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)

for method in METHODS:
    WEB_APP_REPORTS = f'{WEB_APP_REPORTS_DIR}{method}{os.sep}'
    METHODS_DIR = f'{DATA_DIR}{os.sep}{method}{os.sep}'

    csv_predict = f'{DATA_DIR}{method}{os.sep}csv_predict{os.sep}'
    csv_loss = f'{DATA_DIR}{method}{os.sep}csv_loss{os.sep}'
    csv_rolled = f'{DATA_DIR}{method}{os.sep}csv_rolled{os.sep}'
    json_dir = f'{DATA_DIR}{method}{os.sep}json_interval{os.sep}'

    try:
        os.mkdir(f'{METHODS_DIR}')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(f'{WEB_APP_REPORTS}')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(f'{WEB_APP_REPORTS}')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(csv_predict)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(csv_rolled)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(csv_loss)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

    try:
        os.mkdir(json_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)

logger.info(f"script finished")
