from dataclasses import dataclass
import pulumi
from enum import Enum
import os
from typing import Optional
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from pulumi.asset import FileArchive
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
    UnsupportedArchitectureError,
)


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


@dataclass
class BuildGoArgs:
    code: str
    """The path to the code to build"""

    architecture: Optional[str] = "x86_64"
    """The Lambda architecture to build for
    :default: x86_64
    """


class BuildGo(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildGoArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildGo", name, {}, opts)
        result = build_go(args)
        self.asset = result


def build_go(args: BuildGoArgs) -> FileArchive:
    builder = LambdaBuilder("go", "modules", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.architecture or "x86_64"

    try:
        builder.build(
            source_dir=args.code,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=None,
            build_in_source=True,
            runtime="provided",
            architecture=arch,
        )
    except UnsupportedArchitectureError as err:
        print(err)
        raise ValueError("Unsupported architecture")
    # The only two input properties are code & architecture & lambda_builders only throws a specific
    # error for architecture. The rest of the errors we can return as generic errors
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build Go code: {err}")

    return FileArchive(tmp_dir)
