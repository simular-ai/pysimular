import subprocess
import threading
import time
import uuid
import asyncio
from AppKit import NSWorkspace
from Foundation import NSDistributedNotificationCenter
from Foundation import NSRunLoop
from Foundation import NSDate
from .browser import SimularBrowser

class Tab:

    def __init__(self, browser: 'SimularBrowser', id: str = None, verbose: bool = False):
        if not id:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

        self.responses = []
        self.images = []
        self.info = {}
        self.verbose = verbose
        self.browser = browser
        self.bundle_id = browser.bundle_id
        self._setup_notification_observers()
        self._pending_requests = {}

    def reset_storage(self):
        self.responses = []
        self.images = []
        self.info = {}

    def _setup_notification_observers(self):
        center = NSDistributedNotificationCenter.defaultCenter()
        
        tab_request_name = f"{self.bundle_id}.tab_request.{self.id}"
        tab_completion_name = f"{self.bundle_id}.tab_completion.{self.id}"

        center.addObserver_selector_name_object_( #Observer for tab request
            self,
            'handleTabRequest:',
            tab_request_name,
            None
        )
        center.addObserver_selector_name_object_( #Observer for tab completion
            self,
            'handleTabCompletion:',
            tab_completion_name,
            None
        )
        self._center = center

    def handleTabRequest_(self, notification):
        '''
        Handles tab notifications from the browser.
        when browser sends a notification, we add the response to the tab
        '''
        info = notification.userInfo().get('info')
        if not info:
            return
        
        if self.verbose:
            print(f"Received tab request with info {info}")
        text_response = (info.get('response') or 
                         info.get('message') or 
                         info.get('query'))
        image = info.get('image') # base64
        if text_response:
            self.responses.append(text_response)
            if self.verbose:
                print(f"Response: {text_response}")
        if image and len(image):
            self.images.append(image)
            if self.verbose:
                print("added image to tab")
                
    def handleTabCompletion_(self, notification):
        '''
        Handles tab completion notifications from the browser.
        when browser sends a completion, we find the pending request and pop that event in the pending requests
        '''
        if self.verbose:
            print(f"Received tab completion: {notification}")
        info = notification.userInfo().get('info', {})
        request_id = notification.userInfo().get('request_id', None)
        if not request_id:
            print(f"empty request id during handling tab completion")
            if self.verbose:
                print(f"userInfo: {notification.userInfo()}")
            return

        if request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            future.set_result(info)
        else:
            print(f"unable to find pending request with id: {request_id} during handling tab completion")

    async def post(self, command, timeout=30.0, **kwargs):
        '''
        Posts a command to the browser.
        returns a future that will be resolved when the browser completes the request
        '''
        request_id = f"{self.id}_{uuid.uuid4().hex[:8]}"
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        center = NSDistributedNotificationCenter.defaultCenter()
        info = {
            "command": command,
            "request_id": request_id,
            "tab_id": self.id,
            **kwargs
        }
        if self.verbose:
            print(f"Sending command: {command}")
        center.postNotificationName_object_userInfo_deliverImmediately_(
            self.bundle_id,
            None,
            info,
            True
        )
        runloop = NSRunLoop.currentRunLoop()
        start_time = time.time()
        while not future.done():
            until_date = NSDate.dateWithTimeIntervalSinceNow_(0.1)
            runloop.runUntilDate_(until_date)
            await asyncio.sleep(0.1) # add a delay to avoid busy-waiting
            if future.done():
                self._pending_requests.pop(request_id, None)
                return future.result()

            if timeout and time.time() - start_time > timeout:
                if self.verbose:
                    print(f"Timeout after {timeout} seconds")
                self._pending_requests.pop(request_id, None)
                return None

    async def open(self, timeout=30.0):
        await self.post("open_tab", timeout=timeout)
        self.browser.tabs[self.id] = self
        return self.id
    
    async def close(self):
        await self.post("close_tab", timeout=10.0)
        try:
            self.browser.tabs.pop(self.id)
        except Exception as e:
            print(f"Error closing tab with id: {self.id}: {e}")
        return self.id
    
    async def query(self, 
                    query, 
                    model: str = 'claude-3-5-sonnet',
                    planner_mode: str = 'system_1_2',
                    allow_subtasks: bool = False,
                    max_parallelism: int = 3,
                    enable_vision: bool = False,
                    max_steps: int = 100,
                    timeout=600.0):
        self.reset_storage()

        avaliable_models = ['claude-3-5-sonnet']
        if model not in avaliable_models:
            raise ValueError(f"Invalid model: {model}. Avaliable models: {avaliable_models}")
        
        avaliable_planner_modes = ['system_1', 'system_2', 'system_1_2', 'agent_s1']
        if planner_mode not in avaliable_planner_modes:
            raise ValueError(f"Invalid planner mode: {planner_mode}. Avaliable planner modes: {avaliable_planner_modes}")
        
        kwargs = {
            'timeout': timeout,
            'query': query,
            'model': model, 
            'anthropic_key': self.browser.anthropic_key,
            'planner_mode': planner_mode,
            'allow_subtasks': allow_subtasks,
            'max_parallelism': max_parallelism,
            'enable_vision': enable_vision,
            'max_steps': max_steps
        }
        await self.post("query", **kwargs)
        return self.responses