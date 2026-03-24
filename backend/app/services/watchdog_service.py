import logging
import os

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings

logger = logging.getLogger(__name__)

_observer = Observer()


class SDCardHandler(FileSystemEventHandler):
    """
    Watches SD_CARD_WATCH_PATH for new directories (mount points).

    On RPi5 with a USB card reader, newly inserted SD cards appear as
    /media/<username>/<label>/ — a directory created event signals a new card.
    """

    def on_created(self, event) -> None:
        if event.is_directory:
            logger.info("SD card detected at: %s", event.src_path)
            # TODO: trigger video ingestion for event.src_path


def start_watchdog() -> None:
    watch_path = settings.sd_card_watch_path
    if not os.path.exists(watch_path):
        logger.warning(
            "SD card watch path does not exist: %s — watchdog not started", watch_path
        )
        return

    _observer.schedule(SDCardHandler(), path=watch_path, recursive=True)
    _observer.start()
    logger.info("Watchdog started on %s", watch_path)


def stop_watchdog() -> None:
    if _observer.is_alive():
        _observer.stop()
        _observer.join()
