import os
from pysimular import SimularBrowser

app_path = os.path.join(os.getenv("HOME"), "Applications",
                        "SimularBrowser.app")
browser = SimularBrowser(app_path)
browser.run(
    "open a random website and browse like a human, summarize the results.")
