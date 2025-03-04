from pysimular import SimularBrowser
import asyncio
from pysimular.tab import Tab

async def main():
    browser = SimularBrowser(
        "/Users/chih-lunlee/Applications/SimularBrowser.app"
    )
    # Run 3 parallel tasks
    tasks = [test_async_browser(browser) for _ in range(3)]
    await asyncio.gather(*tasks)

async def test_async_browser(browser):
    tab = Tab(browser=browser, verbose=False)
    await tab.open()
    res = await tab.query("What is the capital of the moon?", model="claude-3-5-sonnet", planner_mode="system_1")
    # print(f"res: {res}")
    await tab.close()

if __name__ == "__main__":
    asyncio.run(main())