"""
Basetools
---------

Used to supply and create subclasses for the websites and applications 
you are trying to reach.
::


    from yarnet import WebsiteSession
    
        class Google(WebsiteSession, url="https://www.google.com"):
            "Please remeber that using this example in real life would be against 
            google's TOS, Use at your own risk..."
            async def search(self, query:str):
                async with self.client.get(f"/search?q={query}") as response:
                    return await response.text()
        
        async def example():
            async with Google() as ggl:
                await ggl.search("python")
"""


import typing

from .user_agents import UserAgents
from .config import Context

from aiohttp import ClientSession
from aiohttp.typedefs import StrOrURL


class WebsiteSession:
    """Used to configure different types of asynchronous sessions together.
    the Url parameter can be ignored if you require multiple websites to be reached 
    within the client's class...
    ::

        class Google(WebsiteSession, url="https://www.google.com"):
            async def search(self, query:str):
                async with self.client.get(f"/search?q={query}") as response:
                    return await response.text()
        
        async def example():
            async with Google() as ggl:
                await ggl.search("python")
    """

    def __init_subclass__(
        cls,
        url: typing.Optional[StrOrURL] = None,
        default_user_agent: typing.Optional[str] = None,
    ) -> None:
        """Used to supply default urls and other arguments when nessesary. to make the programming of different target websites as
        easy as possible..."""
        cls._url = url
        cls._user_agents = (
            UserAgents([default_user_agent]) if default_user_agent else None
        )

    def __init__(
        self,
        context: typing.Optional[Context] = None,
        user_agents: typing.Optional[UserAgents] = None,
        url: typing.Optional[StrOrURL] = None,
        **kw
    ) -> None:
        self.client = ClientSession(base_url=url, connector=context.get_proxy() or kw.get('connector', None), **kw)
        self.context = context
        self.user_agents = user_agents or self._user_agents
        if self.user_agents:
            self.client.headers["User-Agent"] = self.user_agents.get_useragent()

    def rotate_user_agent(self):
        """Used to switch immediately to a new user-agent"""
        if self.user_agents:
            self.client.headers["User-Agent"] = self.user_agents.get_useragent()

    async def new_tor_identity(self):
        """Rotates tor exit node if a conext with tor has been given"""
        if self.context and self.context.tor:
            await self.context.reset_identity_and_wait()

    def close(self):
        """Closes the underlying session"""
        return self.client.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        return await self.close()
