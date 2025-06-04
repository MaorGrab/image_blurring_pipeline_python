import logging
import logging.handlers
import multiprocessing
import time


def worker_process(log_queue, worker_id):
    """
    Function run by worker processes.
    Each worker sets up its own logger that sends log records to the shared queue.
    """
    # Configure logger for the worker process
    logger = configure_process_logger(log_queue, f"Worker-{worker_id}")

    # Simulate some work and logging
    for i in range(5):
        logger.info(f"Worker {worker_id} is processing item {i}")
        time.sleep(0.5)

def configure_process_logger(log_queue, name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not any(isinstance(h, logging.handlers.QueueHandler) for h in logger.handlers):
        handler = logging.handlers.QueueHandler(log_queue)
        logger.addHandler(handler)
    logger.propagate = False  # Prevent the log messages from being propagated to the root logger
    return logger

def configure_listener_logger(log_queue):
    """
    Configures the logger for the listener process.
    This logger will handle log records received from the worker processes.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Create handlers
    console_handler = logging.StreamHandler()

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)

    # Add handlers to the root logger
    root_logger.addHandler(console_handler)

    handlers = root_logger.handlers
    listener = logging.handlers.QueueListener(log_queue, *handlers)
    return listener

def main():
    # Create a multiprocessing Queue for log records
    log_queue = multiprocessing.Queue()

    # Configure the listener logger
    listener = configure_listener_logger(log_queue)
    listener.start()

    main_logger = configure_process_logger(log_queue, 'main-log')
    main_logger.info('main logger is working')
    # Create and start worker processes
    processes = []
    for i in range(3):
        p = multiprocessing.Process(target=worker_process, args=(log_queue, i), name=f"WorkerProcess-{i}")
        processes.append(p)
        p.start()

    try:
        # Wait for all worker processes to finish
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
        main_logger.info('terminated processes')
        raise
    finally:
        # Stop the listener
        main_logger.info('done')
        listener.stop()
        log_queue.close()
        log_queue.join_thread()


if __name__ == "__main__":
    main()
