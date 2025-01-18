from offermee.logger import CentralLogger


key_number = 0


def get_valid_next_key():
    global key_number
    key_number += 1
    return f"_key_{key_number}"


widget_logger = CentralLogger.getLogger("widget")


def log_info(msg: object, *args: object):
    global widget_logger
    widget_logger.info(msg=msg, args=args)


def log_error(msg: object, *args: object):
    global widget_logger
    widget_logger.error(msg=msg, args=args)
