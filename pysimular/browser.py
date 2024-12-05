import subprocess
from AppKit import NSWorkspace
from Foundation import NSDistributedNotificationCenter

class SimularBrowser:

    bundle_id = "com.simular.SimularBrowser"

    def __init__(self, path: str):
        self.app_path = path

    def is_app_running(self, bundle_id):
        """Check if the app is already running."""
        running_apps = NSWorkspace.sharedWorkspace().runningApplications()
        return any(app.bundleIdentifier() == bundle_id for app in running_apps)

    def send_message(self, message):
        center = NSDistributedNotificationCenter.defaultCenter()
        user_info = {"message": message}
        center.postNotificationName_object_userInfo_deliverImmediately_(
            self.bundle_id, None, user_info, True)

    def launch_app(self, query):
        """Launch the app with arguments."""
        subprocess.run(["open", self.app_path, "--args", "--query", query])

    def run(self, query):
        """Run query in Simular Browser app."""
        if self.is_app_running(self.bundle_id):
            print(
                "App is already running. Sending arguments to the running instance..."
            )
            self.send_message(query)
        else:
            print("Launching app with arguments...")
            self.launch_app(query)
