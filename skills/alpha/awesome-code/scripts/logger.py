#!/usr/bin/env python3
"""
Awesome Code - 结构化日志模块

提供统一的日志配置和结构化日志支持。
便于调试和监控。
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class LogLevel(Enum):
    """日志级别"""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LogFormat(Enum):
    """日志格式类型"""

    SIMPLE = "simple"
    DETAILED = "detailed"
    JSON = "json"


class AwesomeLogger:
    """结构化日志器"""

    # 类级别的日志器缓存
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls,
        name: str = "awesome-code",
        level: LogLevel = LogLevel.INFO,
        log_format: LogFormat = LogFormat.DETAILED,
        log_file: Optional[str | Path] = None,
    ) -> logging.Logger:
        """
        获取配置好的日志器实例

        Args:
            name: 日志器名称
            level: 日志级别
            log_format: 日志格式
            log_file: 日志文件路径（可选）

        Returns:
            配置好的日志器实例
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(level.value)

        # 清除已有的处理器
        logger.handlers.clear()

        # 格式化器
        formatter = cls._get_formatter(log_format)

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level.value)
        logger.addHandler(console_handler)

        # 文件处理器（如果指定）
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level.value)
            logger.addHandler(file_handler)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def _get_formatter(cls, log_format: LogFormat) -> logging.Formatter:
        """获取日志格式化器"""
        if log_format == LogFormat.SIMPLE:
            return logging.Formatter("%(message)s")

        elif log_format == LogFormat.DETAILED:
            return logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        elif log_format == LogFormat.JSON:
            return JSONFormatter()

        return logging.Formatter("%(message)s")

    @classmethod
    def configure_from_config(cls, config: Dict[str, Any]) -> logging.Logger:
        """
        从配置字典创建日志器

        Args:
            config: 配置字典，包含 level, format, log_file 等键

        Returns:
            配置好的日志器实例
        """
        level_str = config.get("level", "info").upper()
        level = LogLevel[level_str] if level_str in LogLevel.__members__ else LogLevel.INFO

        format_str = config.get("format", "detailed").lower()
        log_format = LogFormat[format_str.upper()] if format_str in LogFormat.__members__ else LogFormat.DETAILED

        log_file = config.get("log_file")

        return cls.get_logger(
            name=config.get("name", "awesome-code"),
            level=level,
            log_format=log_format,
            log_file=log_file,
        )


class JSONFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        import json

        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息（如果有）
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class StructuredLogger:
    """结构化日志上下文管理器"""

    def __init__(
        self,
        logger: logging.Logger,
        context: Dict[str, Any],
    ):
        self.logger = logger
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def _record_factory(self, *args: Any, **kwargs: Any) -> logging.LogRecord:
        record = self.old_factory(*args, **kwargs)
        # 添加上下文信息
        for key, value in self.context.items():
            setattr(record, key, value)
        return record

    def __enter__(self) -> StructuredLogger:
        logging.setLogRecordFactory(self._record_factory)
        return self

    def __exit__(self, *args: Any) -> None:
        logging.setLogRecordFactory(self.old_factory)


def log_execution(
    logger: Optional[logging.Logger] = None,
    level: LogLevel = LogLevel.INFO,
) -> Any:
    """
    装饰器：记录函数执行

    Args:
        logger: 日志器实例（默认使用 awesome-code 日志器）
        level: 日志级别

    Returns:
        装饰器函数
    """

    def decorator(func: Any) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal logger
            if logger is None:
                logger = AwesomeLogger.get_logger()

            func_name = func.__name__
            logger.log(level.value, f"开始执行: {func_name}")

            try:
                result = func(*args, **kwargs)
                logger.log(level.value, f"完成执行: {func_name}")
                return result
            except Exception as e:
                logger.log(LogLevel.ERROR.value, f"执行失败: {func_name} - {e}")
                raise

        return wrapper

    return decorator


# 默认日志器实例
default_logger = AwesomeLogger.get_logger()


def debug(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 DEBUG 级别日志"""
    default_logger.debug(message, *args, **kwargs)


def info(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 INFO 级别日志"""
    default_logger.info(message, *args, **kwargs)


def warning(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 WARNING 级别日志"""
    default_logger.warning(message, *args, **kwargs)


def error(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 ERROR 级别日志"""
    default_logger.error(message, *args, **kwargs)


def critical(message: str, *args: Any, **kwargs: Any) -> None:
    """记录 CRITICAL 级别日志"""
    default_logger.critical(message, *args, **kwargs)


if __name__ == "__main__":
    # 示例用法
    logger = AwesomeLogger.get_logger(
        name="awesome-code",
        level=LogLevel.DEBUG,
        log_format=LogFormat.DETAILED,
    )

    logger.debug("这是一条调试消息")
    logger.info("这是一条信息消息")
    logger.warning("这是一条警告消息")
    logger.error("这是一条错误消息")

    # 使用结构化日志上下文
    with StructuredLogger(logger, context={"user_id": "12345", "request_id": "abc-123"}):
        logger.info("处理用户请求")

    # 使用装饰器
    @log_execution(logger, LogLevel.INFO)
    def example_function(x: int, y: int) -> int:
        return x + y

    example_function(1, 2)
