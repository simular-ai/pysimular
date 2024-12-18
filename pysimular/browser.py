import subprocess
import threading
import time
from AppKit import NSWorkspace
from Foundation import NSDistributedNotificationCenter
from Foundation import NSRunLoop
from Foundation import NSDate

class SimularBrowser:

    bundle_id = "com.simular.SimularBrowser"

    def __init__(self, path: str):
        self.app_path = path
        self.completion_event = threading.Event()
        self.responses = []
        self._setup_notification_observers()

    def _setup_notification_observers(self):
        """Setup observers for app responses and completion signal."""
        center = NSDistributedNotificationCenter.defaultCenter()
        
        response_name = f"{self.bundle_id}.response"
        completion_name = f"{self.bundle_id}.completed"
        
        print(f"Setting up observers for: {response_name} and {completion_name}")
        
        # Observer for intermediate responses
        center.addObserver_selector_name_object_(
            self,
            'handleResponse:',
            response_name,
            None
        )
        
        # Observer for completion signal
        center.addObserver_selector_name_object_(
            self,
            'handleCompletion:',
            completion_name,
            None
        )

        self._center = center

    def handleResponse_(self, notification):
        """Handle intermediate responses from the app."""
        print(f"Received response notification: {notification.name()}")
        print(f"Response userInfo: {notification.userInfo()}")
        if notification.userInfo():
            # Try multiple possible keys
            response = (notification.userInfo().get('response') or 
                       notification.userInfo().get('message') or 
                       notification.userInfo().get('query'))
            if response:
                self.responses.append(response)
                print(f"Response: {response}")
            else:
                print(f"No recognized response key in userInfo: {notification.userInfo()}")

    def handleCompletion_(self, notification):
        """Handle completion signal from the app."""
        print("Received completion signal")
        self.completion_event.set()
        # Stop the current run loop
        NSRunLoop.currentRunLoop().performSelector_target_argument_order_modes_(
            'stop',
            NSRunLoop.currentRunLoop(),
            None,
            0,
            None
        )

    def is_app_running(self, bundle_id):
        """Check if the app is already running."""
        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        return any(app.bundleIdentifier() == bundle_id for app in running_apps)

    def send_message(self, message):
        center = NSDistributedNotificationCenter.defaultCenter()
        user_info = {"message": message}
        notification_name = self.bundle_id
        print(f"Sending message with notification name: {notification_name}")
        print(f"Message content: {user_info}")
        center.postNotificationName_object_userInfo_deliverImmediately_(
            notification_name, None, user_info, True)

    def launch_app(self, query):
        """Launch the app with arguments."""
        subprocess.run(["open", self.app_path, "--args", "--query", query])

    def run(self, query, timeout=None):
        """Run query in Simular Browser app and wait for completion."""
        # Reset state
        self.completion_event.clear()
        self.responses = []

        if self.is_app_running(self.bundle_id):
            print("App is already running. Sending arguments to the running instance...")
            self.send_message(query)
        else:
            print("Launching app with arguments...")
            self.launch_app(query)

        runloop = NSRunLoop.currentRunLoop()
        start_time = time.time()
        
        while not self.completion_event.is_set():
            # Run the loop for a short interval
            until_date = NSDate.dateWithTimeIntervalSinceNow_(0.1)  # 100ms intervals
            runloop.runUntilDate_(until_date)
            
            # Check for timeout
            if timeout and time.time() - start_time > timeout:
                print(f"Timeout after {timeout} seconds")
                break
        
        if self.completion_event.is_set():
            print("Completed successfully")
        
        return self.responses

    def __del__(self):
        """Cleanup notification observers."""
        center = NSDistributedNotificationCenter.defaultCenter()
        center.removeObserver_(self)

