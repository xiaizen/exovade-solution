from PyQt6.QtCore import QObject, QRunnable, pyqtSignal, pyqtSlot, QThread

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    finished
        No data
    error
        tuple (exctype, value, traceback.format_exc() )
    result
        object data returned from processing, anything
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QObject):
    """
    Worker thread that inherits from QObject (not QThread directly).
    Intended to be moved to a QThread.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        """
        Initialise the runner function with passed args, kwargs.
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            exctype, value = type(e), e
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class ThreadController(QObject):
    """
    Manages a QThread and a Worker.
    """
    def __init__(self, worker_fn, *args, **kwargs):
        super().__init__()
        self.thread = QThread()
        self.worker = Worker(worker_fn, *args, **kwargs)
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.signals.finished.connect(self.thread.quit)
        self.worker.signals.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # Forward worker signals 
        self.signals = self.worker.signals

    def start(self):
        self.thread.start()
