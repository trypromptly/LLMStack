"""
A wrapper for managing Xvfb instances.
"""
import logging
import queue
import subprocess
import threading
import time
import uuid

MAX_DISPLAYS = 10
START_DISPLAY = 100
RFB_START_PORT = 5900
DISPLAY_RES = '1024x720x24'
HOSTNAME = 'localhost'

logger = logging.getLogger(__name__)


class DisplayNotFoundException(Exception):
    pass


class VirtualDisplay:
    def __init__(self, display_id, display_res, rfb_port):
        self.id = display_id
        self.display_res = display_res
        self.rfb_port = rfb_port
        self.xvfb_process = None
        self.x11vnc_process = None
        self.token = None
        self.username = None
        self.password = None

    def __str__(self):
        return f"Display {self.id} ({self.display_res})"

    def __repr__(self):
        return f"Display {self.id} ({self.display_res})"

    def start(self):
        self.xvfb_process = subprocess.Popen(
            ['Xvfb', f':{self.id}', '-screen', '0', self.display_res, '-ac'], close_fds=True)
        logger.info(f"Started display: {self.id}")

    def stop(self):
        if self.xvfb_process:
            self.xvfb_process.terminate()
            logger.info(f"Terminated display: {self.id}")

        if self.x11vnc_process:
            self.x11vnc_process.terminate()
            logger.info(f"Terminated x11vnc process: {self.id}")

    def start_x11vnc(self):
        self.x11vnc_process = subprocess.Popen(['x11vnc', '-display', f':{self.id}', '-nopw', '-listen',
                                                'localhost', '-xkb', '-q', '-rfbport', str(self.rfb_port)], close_fds=True)
        logger.info(f"Started x11vnc process: {self.id}")

    def stop_x11vnc(self):
        if self.x11vnc_process:
            self.x11vnc_process.terminate()
            logger.info(f"Terminated x11vnc process: {self.id}")

    def set_token(self, token):
        self.token = token

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password


class VirtualDisplayPool():
    def __init__(self, redis_client, hostname=HOSTNAME, max_displays=MAX_DISPLAYS, start_display=START_DISPLAY, display_res=DISPLAY_RES, rfb_start_port=RFB_START_PORT):
        self.display_queue = queue.Queue()
        self.redis_client = redis_client
        self.max_displays = max_displays
        self.start_display = start_display
        self.display_res = display_res
        self.rfb_start_port = rfb_start_port
        self.hostname = hostname
        self.ip_address = subprocess.check_output(
            ['hostname', '-i']).decode('utf-8').strip()
        self._create_displays(max_displays, start_display,
                              display_res, rfb_start_port)

    def get_display(self, timeout=10, remote_control=False):
        display = self._get_display(timeout)

        # We start noVNC if remote_control is True
        if remote_control:
            x11vnc_process = subprocess.Popen(['x11vnc', '-display', display['DISPLAY'], '-nopw', '-listen',
                                              'localhost', '-xkb', '-q', '-rfbport', str(display['rfb_port'])], close_fds=True)
            display['x11vnc_process'] = x11vnc_process
            display['token'] = str(uuid.uuid4())

            # Add display to redis with a TTL of 1 minute
            self.redis_client.set(
                display['token'], '{"host": "' + f'{self.ip_address}:{display["rfb_port"]}' + '"}', ex=60)

            # Generate and add temp credentials to redis with a TTL of 1 minute
            username = str(uuid.uuid4())
            password = str(uuid.uuid4())
            self.redis_client.set(username, password, ex=60)

            display['username'] = username
            display['password'] = password

        return display

    def put_display(self, display):
        # Cleanup display resources
        if 'x11vnc_process' in display:
            display['x11vnc_process'].terminate()
            del display['x11vnc_process']
            logger.info(f"Terminated x11vnc process: {display['id']}")

        if 'username' in display:
            self.redis_client.delete(display['username'])
            del display['username']
            logger.info(f"Deleted username: {display['id']}")

        if 'password' in display:
            del display['password']

        if 'token' in display:
            self.redis_client.delete(display['token'])
            del display['token']
            logger.info(f"Deleted token: {display['id']}")

        self.display_queue.put(display)
        logger.info(f"Put display: {display['id']}")

    def _create_display(self, display_id, display_res, rfb_port):
        xvfb_process = subprocess.Popen(
            ['Xvfb', f':{display_id}', '-screen', '0', display_res, '-ac'], close_fds=True)

        self.display_queue.put({
            'id': display_id,
            'DISPLAY': f':{display_id}',
            'xvfb_process': xvfb_process,
            'rfb_port': rfb_port,
        })
        logger.info(f"Created display: {display_id}")

    def _create_displays(self, max_displays, start_display, display_res, rfb_start_port):
        threads = []
        for i in range(max_displays):
            thread = threading.Thread(
                target=self._create_display, args=(start_display + i, display_res, rfb_start_port + i))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def _get_display(self, timeout):
        start_time = time.time()
        while True:
            display = self.display_queue.get(timeout=timeout)
            if display['xvfb_process'].poll() is None:  # Check if process is still running
                return display
            else:
                display['xvfb_process'].kill()
                self._create_display(
                    display['id'], self.display_res, display['rfb_port'])
                logger.info(f"Recreated display: {display['id']}")

            if time.time() - start_time > timeout:
                raise DisplayNotFoundException(
                    f"Display not found in {timeout} seconds")

    # Clean up all displays when object is destroyed
    def __del__(self):
        while not self.display_queue.empty():
            display = self.display_queue.get()
            display['xvfb_process'].terminate()
            logger.info(f"Terminated display: {display['id']}")
