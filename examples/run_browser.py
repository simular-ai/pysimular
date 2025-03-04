from pysimular import SimularBrowser
import asyncio
from pysimular.tab import Tab

async def main():
    browser = SimularBrowser(
        "/Users/chih-lunlee/Applications/SimularBrowser.app"
    )
    # id = await browser.open_new_tab()
    # response = await browser.run("hello!")
    # await browser.close_tab(id)
    # print(f"final response:")
    # for key in response:
    #     print(f"  {key}: {response[key][:100]}")
    tasks = [test_async_browser(browser) for _ in range(1)]
    await asyncio.gather(*tasks)

async def test_async_browser(browser):
    tab = Tab(browser=browser)
    await tab.open()
    await asyncio.sleep(2)
    await tab.close()

if __name__ == "__main__":
    asyncio.run(main())