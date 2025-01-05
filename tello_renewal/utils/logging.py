import logging
import logging.config

import yaml


def configure_logging() -> None:
    with open("config/logging.yaml", "r") as logging_yaml:
        logging_config = yaml.safe_load(logging_yaml)

    logging.config.dictConfig(logging_config)

