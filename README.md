# Yarnet
Yet Another Requests Networking Enumeration Tool For Asynchrnous Python 
Applications. Yarnet's goal is to make it as easy as possible to configure 
commandline-applications and class objects that need to have access to 
internet and webscraping abilities without being super neash, weak , or slow. It allows
for easy interactions with proxies and also tor (aka the darknet).


Here's one of the few tools that `Yarnet` provides which is called a WebsiteSession used to make 
webscraping easier to configure with less code overall and is binded staight to aiohttp's `ClientSession` and allows 
for items to be made in a clean object oriented format.
```python
from yarnet import WebsiteSession

class Google(WebsiteSession, url="https://www.google.com"):
      "Please remeber that using this example in real life would be against google's TOS, Use at your own risk..."
      async def search(self, query:str):
          async with self.client.get(f"/search?q={query}") as response:
              return await response.text()

async def example():
    async with Google() as ggl:
        await ggl.search("python")
```
