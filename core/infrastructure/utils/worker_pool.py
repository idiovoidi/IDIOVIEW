from queue import PriorityQueue, Queue, Empty
from threading import Thread, Event, Lock, Semaphore
import logging
from typing import Any, Callable, Optional, TypeVar, Generic, Tuple
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Type for task data
R = TypeVar('R')  # Type for task result

class WorkerPool(Generic[T, R]):
    """Generic worker pool for processing tasks in multiple threads"""
    
    def __init__(self, 
                 process_func: Callable[[T], Optional[R]], 
                 num_workers: int = 4,
                 name: str = "Worker"):
        """
        Initialize worker pool
        
        Args:
            process_func: Function to process each task
            num_workers: Number of worker threads
            name: Base name for worker threads
        """
        self.process_func = process_func
        self.num_workers = num_workers
        self.name = name
        
        # Thread management
        self.worker_semaphore = Semaphore(num_workers * 2)
        self.processing_lock = Lock()
        self.processing_set = set()
        self.processed_items = set()
        
        # Queue management
        self.priority_queue = PriorityQueue()
        self.normal_queue = Queue()
        self.stop_event = Event()
        self.is_shutting_down = False
        
        # Start worker threads
        self.processing_threads = []
        for i in range(self.num_workers):
            thread = Thread(
                target=self._process_queue,
                daemon=True,
                name=f"{name}-{i}"
            )
            thread.start()
            self.processing_threads.append(thread)
            
    def _process_queue(self) -> None:
        """Process items from queues"""
        while not self.stop_event.is_set():
            try:
                # Try to get a task
                queue_item, queue_type = self._get_next_task()
                
                # If no task available, sleep briefly to prevent CPU spinning
                if queue_item is None:
                    time.sleep(0.05)  # Short sleep when no work available
                    continue

                # We have a task, try to acquire the semaphore
                if not self.worker_semaphore.acquire(timeout=0.5):  # Longer timeout for semaphore
                    # Couldn't get semaphore, requeue the item
                    self._requeue_task(queue_item, queue_type)
                    time.sleep(0.01)  # Brief sleep before retry
                    continue

                try:
                    # Process the task
                    task_data = self._extract_task_data(queue_item, queue_type)
                    if task_data is not None:
                        self.process_func(task_data)
                except Exception as e:
                    logger.error(f"Error processing task: {e}", exc_info=True)
                finally:
                    # Always mark task as done and release semaphore
                    try:
                        self._mark_task_done(queue_type)
                    except Exception as e:
                        logger.error(f"Error marking task as done: {e}")
                    finally:
                        self.worker_semaphore.release()

            except Exception as e:
                logger.error(f"Error in worker thread: {e}", exc_info=True)
                # Brief sleep on error to prevent tight error loops
                time.sleep(0.1)

    def _get_next_task(self) -> Tuple[Optional[Any], Optional[str]]:
        """Get next task from priority or normal queue
        
        Returns:
            Tuple of (task_item, queue_type) or (None, None) if no tasks available
        """
        # First check priority queue without blocking
        try:
            if not self.priority_queue.empty():
                item = self.priority_queue.get_nowait()
                return item, 'priority'
        except Empty:
            pass

        # If no priority items, try normal queue with timeout
        try:
            if not self.normal_queue.empty():
                item = self.normal_queue.get(timeout=0.1)  # Short timeout to remain responsive
                return item, 'normal'
        except Empty:
            pass

        # No tasks available in either queue
        return None, None

    def _requeue_task(self, queue_item: Any, queue_type: str) -> None:
        """Requeue a task that couldn't be processed"""
        try:
            if queue_type == 'priority':
                self.priority_queue.put(queue_item)
            else:
                self.normal_queue.put(queue_item)
        except Exception as e:
            logger.error(f"Error requeueing task: {e}")

    def _extract_task_data(self, queue_item: Any, queue_type: str) -> Optional[T]:
        """Extract task data from queue item based on queue type"""
        try:
            if queue_type == 'priority':
                _, task_data = queue_item
                return task_data
            return queue_item
        except Exception as e:
            logger.error(f"Error extracting task data: {e}")
            return None

    def _mark_task_done(self, queue_type: str) -> None:
        """Mark task as done in appropriate queue"""
        try:
            if queue_type == 'priority':
                self.priority_queue.task_done()
            elif queue_type == 'normal':
                self.normal_queue.task_done()
        except Exception as e:
            logger.error(f"Error marking task as done: {e}")

    def put(self, task: T, priority: bool = False) -> bool:
        """Add task to queue"""
        try:
            if self.is_shutting_down:
                return False
                
            # Add to appropriate queue
            if priority:
                self.priority_queue.put((0, task))
            else:
                self.normal_queue.put(task)
                
            return True
            
        except Exception as e:
            logger.error(f"Error queueing task: {e}")
            return False
            
    def cleanup(self):
        """Clean up resources"""
        try:
            logger.debug(f"Starting {self.name} pool cleanup")
            self.is_shutting_down = True
            self.stop_event.set()
            
            # Wait for threads to finish with timeout
            for thread in self.processing_threads:
                thread.join(timeout=1.0)
                
            # Clear queues
            while not self.priority_queue.empty():
                try:
                    self.priority_queue.get_nowait()
                except Empty:
                    break
                    
            while not self.normal_queue.empty():
                try:
                    self.normal_queue.get_nowait()
                except Empty:
                    break
                    
            logger.debug(f"Completed {self.name} pool cleanup")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            
    def __del__(self):
        """Ensure cleanup on deletion"""
        try:
            self.cleanup()
        except:
            pass 