"""
Config
------

Used to make it easier to create request configurations by creating an easy to 
run context manager system.This also has pre-programmed tools for using tor on 
and off so no need to go super deep yourself with tor...

The goal with config is to make it as easy as possible to setup proxies and 
optionally tor in a small and tiny manner while bringing in enogh typehinting 
so that tools such as intellisense by microsoft can easily read what exactly is 
going on...
"""

from attrs import define, field
from aiohttp_socks import ProxyConnector
from python_socks import ProxyType, parse_proxy_url
from typing import Optional
from subprocess import Popen
import asyncio
import stem
from stem.control import Controller
from stem.process import launch_tor_with_config


# TODO (Vizonex) Maybe write some examples of how yarnet's context is wrapped to custom-made subclasses?


@define(slots=False)
class Context:
    """A context used for helping wrap basic yarnet asynchronous based sessions, This is also
    used for easily creating guis and commandlines that require networking with proxies"""

    tor: bool = False
    tor_crtl_port: Optional[int] = None
    tor_cmd: Optional[str] = None
    proxy_type: Optional[ProxyType] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    """This can also be your tor password..."""
    rdns: bool = False
    """Routes all dns calls through to the proxy being used..."""
    tor_proccess: Optional[Popen[bytes]] = field(init=False, default=None)
    ctrl: Optional[Controller] = field(init=False, default=None)

    def set_tor_defaults(self):
        """Used if tor is set to true and there's not any reachable defaults in the
        configuration"""
        if self.tor:
            if not self.proxy_host:
                self.proxy_host = "localhost"
            if not self.proxy_port:
                self.proxy_port = 9050
            if not self.tor_crtl_port:
                self.tor_crtl_port = 9051
            # Ensure tor proxy is set to socks5...
            self.proxy_type = ProxyType.SOCKS5

    @classmethod
    def from_url(
        cls,
        proxy_url: Optional[str] = None,
        tor: bool = False,
        tor_crtl_port: Optional[int] = None,
        tor_password: Optional[str] = None,
        tor_cmd: Optional[str] = None,
        rdns: bool = False,
    ):
        """Used as an easier classmethod without too many arguments needed to be used..."""
        if proxy_url:
            (
                proxy_type,
                proxy_host,
                proxy_port,
                proxy_username,
                proxy_password,
            ) = parse_proxy_url(proxy_url)
            return cls(
                tor=tor,
                tor_crtl_port=tor_crtl_port,
                tor_cmd=tor_cmd,
                proxy_type=proxy_type,
                proxy_host=proxy_host,
                proxy_port=proxy_port,
                proxy_username=proxy_username,
                proxy_password=proxy_password or tor_password,
                rdns=rdns,
            )
        else:
            return cls(
                rdns=rdns,
                tor=tor,
                tor_crtl_port=tor_crtl_port,
                proxy_password=tor_password,
            )

    # TODO Add an Option for disabiling or enabling ssl verifications...
    def get_proxy(self):
        """Obtains proxy for connection to a yarnet subclass variable, returns None if there is no proxy arguments avalible..."""
        return (
            ProxyConnector(
                self.proxy_type,
                self.proxy_host,
                self.proxy_port,
                self.proxy_username,
                self.proxy_password,
                rdns=self.rdns,
            )
            if self.proxy_type
            else None
        )

    def rotate_proxy(
        self,
        proxy_type: ProxyType,
        proxy_host: str,
        proxy_port: int,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ):
        self.proxy_type = proxy_type
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

    def rotate_proxy_from_url(self, url: str):
        """Used to rotate proxies around easily..."""
        (
            self.proxy_type,
            self.proxy_host,
            self.proxy_port,
            self.proxy_username,
            self.proxy_password,
        ) = parse_proxy_url(url)

    def configure(self):
        """Used to configure tor if tor is set to being true. This will also
        launch tor to start being used as a context manager"""
        self.set_tor_defaults()
        self.tor_proccess = self._launch_tor()
        if self.tor:
            self.ctrl = Controller.from_port(port=self.ctrl_port)
            self.ctrl.authenticate(password=self.proxy_password)

    # Code is from and inspired by torrequest
    def reset_identity_async(self):
        if self.tor:
            self.ctrl.signal(stem.Signal.NEWNYM)

    async def reset_identity_and_wait(self):
        """Asynchronously rotates the tor identiy and waits for tor's exit
        node to be rotated..."""
        if self.tor:
            self.reset_identity_async()
            return await asyncio.sleep(self.ctrl.get_newnym_wait())

    def _tor_process_exists(self):
        try:
            ctrl = Controller.from_port(port=self.tor_crtl_port or 9051)
            ctrl.close()
            return True
        except:
            return False

    def _launch_tor(self) -> Optional[Popen[bytes]]:
        if self.tor and not self._tor_process_exists():
            return launch_tor_with_config(
                tor_cmd=self.tor_cmd or "tor",
                config={
                    "SocksPort": str(self.proxy_port or 9050),
                    "ControlPort": str(self.tor_crtl_port or 9051),
                },
                take_ownership=True,
            )

    def close(self):
        if self.tor:
            try:
                if self.ctrl:
                    self.ctrl.close()
            except:
                pass

            if self.tor_proccess:
                self.tor_proccess.terminate()

    def __enter__(self):
        self.configure()
        return self

    def __exit__(self, *args):
        return self.close()


@define(slots=False)
class ProxyFile:
    """Used to rotate or test a list of proxies being given to it..."""
    file:str
    has_prefix_type:bool = False
    """Text file provides eatch proxy type as `socks5://localhost:9090` for example...
    otherwise it will accept it as simply `host:port` where you need to provide what type it is yourself..."""
    proxy_type:Optional[ProxyType] = None
    roatate_forver: bool = False
    rdns:bool = False

    def _infinate_supplier(self):
        if not self.has_prefix_type:
            assert self.proxy_type is not None, "proxy_type must be supplied if not prefix type is provided by the textfile"
        def func():
            with open(self.file, "r") as r:
                for l in r:
                    if self.has_prefix_type:
                        yield Context.from_url(l.strip(), rdns=self.rdns)
                    else:
                        host, port = l.strip().split(":", 1)
                        yield Context(proxy_host=host, proxy_port=int(port))

        for ctx in func():
            yield ctx

        while self.roatate_forver:
            for ctx in func():
                yield ctx

    def __attrs_post_init__(self):
        self._generator = self._infinate_supplier()
        
    def get_proxy(self):
        return next(self._generator)
