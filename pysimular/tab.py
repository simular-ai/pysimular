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

    def __init__(self, browser: 'SimularBrowser', id: str = None):
        if not id:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

        self.responses = []
        self.images = []
        self.info = {}

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
        print(f"Received tab request: {notification}")
        info = notification.userInfo()
        if not info:
            return
    
        text_response = (notification.userInfo().get('response') or 
                            notification.userInfo().get('message') or 
                            notification.userInfo().get('query'))
        image = notification.userInfo().get('image') # base64
        if text_response:
            self.responses.append(text_response)
            print(f"Response: {text_response}")
        if image and len(image):
            self.images.append(image)
            print("added image to tab")
        else:
            print(f"No recognized response key in userInfo: {notification.userInfo()}")
                
    def handleTabCompletion_(self, notification):
        '''
        Handles tab completion notifications from the browser.
        when browser sends a completion, we find the pending request and pop that event in the pending requests
        '''
        print(f"Received tab completion: {notification}")
        info = notification.userInfo()
        request_id = info.get('request_id', None)
        if not info or not request_id:
            print(f"No recognized request id in userInfo: {notification.userInfo()}")
            return

        if request_id in self._pending_requests:
            future = self._pending_requests[request_id]
            future.set_result(info)
        else:
            print(f"unable to find pending request with id: {request_id}")

    async def post(self, command, timeout=30.0, **kwargs):
        '''
        Posts a command to the browser.
        returns a future that will be resolved when the browser completes the request
        '''
        request_id = f"{self.id}_{uuid.uuid4().hex[:8]}"
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        center = NSDistributedNotificationCenter.defaultCenter()
        try:
            info = {
                "command": command,
                "request_id": request_id,
                "tab_id": self.id,
                **kwargs
            }

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
                until_date = NSDate.dateWithTimeIntervalSinceNow_(0.1)  # 100ms intervals
                runloop.runUntilDate_(until_date)
                if future.done():
                    return future.result()
                
                if timeout and time.time() - start_time > timeout:
                    print(f"Timeout after {timeout} seconds")
                    break
            
            if future.done():
                print("Completed successfully")
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                print(f"Timeout error: {asyncio.TimeoutError}")
                self._pending_requests.pop(request_id, None)
                return None
        finally:
            self._pending_requests.pop(request_id, None)

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
    
    async def query(self, query, timeout=600.0):
        self.reset_storage()
        await self.post("query", timeout=timeout, query=query)
        return self.responses