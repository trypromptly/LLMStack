from rq import SimpleWorker
from rq.timeouts import TimerDeathPenalty

class WindowsWorker(SimpleWorker):
    death_penalty_class = TimerDeathPenalty