"""
User-Agents
-----------

A primary module for helping with supplying user-agents

"""

from typing import NamedTuple, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from pathlib import Path
    from typing_extensions import Self
    PathOrStr = Union[Path, str, bytes]

import random


# NOTE: I am working on my own Verison of python's std libary that used the
# romu random as a base in cython and C so it should be faster than
# Random by quite a bit and easier on the memory, Hence why I made an
# rng_base around the random itself...


class UserAgents(NamedTuple):
    """Used to supply your own randomizable user-agents to your requests"""

    user_agents: list[str]
    rng_base: random.Random = random.Random()
    """Used to supply your own randomizer tools"""

    def get_useragent(self) -> str:
        return (
            self.user_agents[0]
            if len(self.user_agents) < 2
            else self.rng_base.choice(self.user_agents)
        )

    if not TYPE_CHECKING:

        @classmethod
        def read_text_file(cls, file: str, rng_base: random.Random = random.Random()):
            return cls(open(file).readlines(), rng_base)

    else:

        @classmethod
        def read_text_file(
            cls: Self, file: PathOrStr, rng_base: random.Random = random.Random()
        ) -> Self:
            """Used to supply a text-file with user-agents to use"""
            ...
