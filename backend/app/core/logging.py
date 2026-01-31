"""Logging configuration."""

import logging
import sys
from pathlib import Path

from backend.app.core.config import settings


def setup_logging():
    """Configure application logging."""

    # Create formatters
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # logging.Formatter(...)：定义日志的“排版模板”。
    # %(asctime)s：时间。
    # %(name)s：logger 的名字。
    # %(levelname)s：日志等级（DEBUG/INFO/WARNING/ERROR）。
    # %(message)s：实际写的内容。
    # datefmt=...：时间格式，比如 2026-01-31 15:22:10。
    # 最终输出可能例子：2026-01-31 15:22:10 - backend.app.api - INFO - Server started。

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    # sys.stdout 的意思是：“终端输出通道”，standard output。
    # 这句话的意思是：创建一个“日志输出器”（handler），它的输出目标是 sys.stdout，也就是把日志打到终端。
    # stdout 是“流”（stream），所以叫stream handler。一条条往stdout里写文本，它就一条条出现在终端。
    console_handler.setFormatter(formatter)
    # 这句话的意思是：给这个 handler 绑一个“排版模板”（formatter），决定日志输出长什么样。

    # File handler for application logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    # exist_ok=True 的意思是：如果目录已经存在，别报错，继续，如果不存在，就创建。

    file_handler = logging.FileHandler(log_dir / "app.log")
    # TODO: Currently using a single app.log file.
    #       In production, switch to TimedRotatingFileHandler
    #       to rotate logs by date and avoid unlimited file growth.
    # 这句话的意思是：创建一个“日志写文件的管道”，目标文件是：logs/app.log。
    # 上面这个TO DO，是把日志按时间切割，虽然也可以用大小切割，但是排查历史问题不如时间直观。
    file_handler.setFormatter(formatter)
    # logging 可以“一条日志，同时发给多个地方”，StreamHandler 是“发到终端”，FileHandler 是“发到文件”。

    # Root logger
    root_logger = logging.getLogger()
    # 跟getLogger(__name__)不一样，不传名字的话拿到的就是 root logger（根 logger）。
    root_logger.setLevel(
        logging.DEBUG if settings.environment == "development" else logging.INFO
    )
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    # 这里是告诉root logger：收到日志后，把它们发到哪里。

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return root_logger


# Global logger instance
logger = logging.getLogger(__name__)
# 在 Python 里，每个 .py 文件都是一个 模块，模块有一个名字，叫 __name__。
# 假设这个文件路径是：backend/app/core/logging.py，
# 那运行时 __name__ 就等于 "backend.app.core.logging"，
# 所以上面这代码等价于logger = logging.getLogger("backend.app.core.logger")。