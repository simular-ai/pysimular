from pysimular import SimularBrowser
import asyncio
async def main():
    browser = SimularBrowser(
        "/Users/chih-lunlee/Applications/SimularBrowser.app"
    )
    id = await browser.open_new_tab()
    response = browser.run("hello!")
    await browser.close_tab(id)
    print(f"final response:")
    for key in response:
        print(f"  {key}: {response[key][:100]}")

if __name__ == "__main__":
    asyncio.run(main())