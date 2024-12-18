from pysimular import SimularBrowser

browser = SimularBrowser(
    "/Users/angli/Library/Developer/Xcode/DerivedData/SimularBrowser-cxquyiratqxnoxfnmasbdrowrpim/Build/Products/Debug/SimularBrowser.app"
)
response = browser.run("hello how are you?")

print(f"final response: {response}")
