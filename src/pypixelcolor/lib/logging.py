import logging

class EmojiFormatter(logging.Formatter):
    EMOJI_MAP = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥'
    }
    
    def format(self, record):
        emoji = self.EMOJI_MAP.get(record.levelname, '📝')
        record.levelname = f"{emoji}"
        return super().format(record)


def setup_logging(use_emojis=True, level="INFO") -> None:
    log_format = '%(levelname)s [%(asctime)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    if use_emojis:
        formatter = EmojiFormatter(log_format, datefmt=date_format)
    else:
        formatter = logging.Formatter(log_format, datefmt=date_format)
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logging.basicConfig(level=level, handlers=[handler])