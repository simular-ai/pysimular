import asyncio
import os
from pysimular.tab import Tab
from pysimular import SimularBrowser


async def main():
    browser = SimularBrowser(
        os.path.join(os.getenv("HOME"), "Applications", "SimularBrowser.app"))
    # Run 3 parallel tasks
    tasks = [test_async_browser(browser) for _ in range(3)]
    await asyncio.gather(*tasks)


async def test_async_browser(browser):
    tab = Tab(browser=browser, verbose=False)
    await tab.open()
    res = await tab.query("Search for the capital of the moon?",
                          model="claude-3-5-sonnet",
                          planner_mode="agent_s1")
    print(f"res: {res}")
    await tab.close()


if __name__ == "__main__":
    asyncio.run(main())
