import subprocess
import threading
import time
from AppKit import NSWorkspace
from Foundation import NSDistributedNotificationCenter
from Foundation import NSRunLoop
from Foundation import NSDate

class SimularBrowser:

    bundle_id = "com.simular.SimularBrowser"

    def __init__(self,
                 path: str,
                 anthropic_key: str = '',
                 planner_model: str = 'claude-3-5-sonnet',
                 planner_mode: str = 'system_1_2',
                 allow_subtasks: bool = False,
                 max_parallelism: int = 5,
                 enable_vision: bool = False,
                 max_steps: int = 200):
        """Browser interface for Simular app.

        Args:
            path (str): Path to the SimularBrowser application
            anthropic_key (str, optional): Anthropic API key.
            planner_model (str, optional): Model to use for planning.
            planner_mode (str, optional): Planning mode to use. Options: system_1, system_2, system_1_2, agent_s1
            allow_subtasks (bool, optional): Whether to allow subtask creation.
            max_parallelism (int, optional): Maximum number of parallel tasks.
            enable_vision (bool, optional): Whether to enable vision.
        """
        self.app_path = path
        self.completion_event = threading.Event()
        self.responses = []
        self.images = [] # base64 string
        self.anthropic_key = anthropic_key
        self.planner_model = planner_model
        self.planner_mode = planner_mode
        self.allow_subtasks = allow_subtasks
        self.max_parallelism = max_parallelism
        self.enable_vision = enable_vision
        self.max_steps = max_steps
        self.info = {}
        self.tabs = {}
        self._setup_notification_observers()

    def _setup_notification_observers(self):
        """Setup observers for app responses and completion signal."""
        center = NSDistributedNotificationCenter.defaultCenter()
        
        response_name = f"{self.bundle_id}.response"
        completion_name = f"{self.bundle_id}.completed"
        
        # print(f"Setting up observers for: {response_name} and {completion_name}")
        
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
        # print(f"Received response notification: {notification.name()}")
        # This print is long due to image data
        # print(f"Response userInfo: {notification.userInfo()}")
        if notification.userInfo():
            # Try multiple possible keys
            text_response = (notification.userInfo().get('response') or 
                             notification.userInfo().get('message') or 
                             notification.userInfo().get('query'))
            image = notification.userInfo().get('image') # base64
            if text_response or image:
                if text_response:
                    self.responses.append(text_response)
                    # print(f"Response: {text_response}")
                if image and len(image):
                    self.images.append(image)
            else:
                print(f"No recognized response key in userInfo: {notification.userInfo()}")

    def handleCompletion_(self, notification):
        """Handle completion signal from the app."""
        print("Received completion signal")

        if notification.userInfo():
            # info is a [str: any] dictionary
            info = notification.userInfo().get('info')
            self.info = info
                
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

    def send_message(self, message, reset: bool = False):
        center = NSDistributedNotificationCenter.defaultCenter()
        user_info = {
            "message": message,
            "anthropic_key": self.anthropic_key,
            "planner_model": self.planner_model,
            "planner_mode": self.planner_mode,
            "allow_subtasks": self.allow_subtasks,
            "max_parallelism": self.max_parallelism,
            "enable_vision": self.enable_vision,
            "max_steps": self.max_steps,
            "reset": reset
        }
        notification_name = self.bundle_id
        # print(f"Sending message with notification name: {notification_name}")
        print(f"Sending message with content: {user_info}")
        center.postNotificationName_object_userInfo_deliverImmediately_(
            notification_name, None, user_info, True)

    def launch_app(self, query):
        """Launch the app with arguments."""
        subprocess.run(["open", self.app_path, "--args", "--query", query])

    def run(self, query, timeout=None, reset: bool = False) -> dict:
        """Run query in Simular Browser app and wait for completion."""
        # Reset state
        self.completion_event.clear()
        self.responses = []
        self.images = []

        if self.is_app_running(self.bundle_id):
            print("App is already running. Sending arguments to the running instance...")
            self.send_message(query, reset)
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

        output = {
            "responses": self.responses,
            "images": self.images,
            "info": self.info
        }

        return output

    def __del__(self):
        """Cleanup notification observers."""
        center = NSDistributedNotificationCenter.defaultCenter()
        center.removeObserver_(self)