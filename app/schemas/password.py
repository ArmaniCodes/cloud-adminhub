from typing import Annotated
from pydantic import Field

NewPassword = Annotated[
    str,
    Field(min_length=15, max_length=128)
]
