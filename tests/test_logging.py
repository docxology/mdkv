import logging

from mdkv.common import configure_logging, get_logger


def test_configure_and_get_logger():
    configure_logging(logging.DEBUG)
    log = get_logger("mdkv.test")
    assert isinstance(log, logging.Logger)
    log.debug("debug message")


