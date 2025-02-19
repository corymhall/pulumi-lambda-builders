import pulumi
from enum import Enum
from typing import Dict, Optional, TypedDict
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from pulumi.asset import FileArchive
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
)


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


class BuildDotnetArgs(TypedDict):
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    """

    runtime: str
    """Dotnet version to build dependencies for."""

    build_options: Optional[Dict[str, str]]
    """Additional command line flags to pass to the dotnet build command
    The key should be prefixed with `-` or `--` like the cli argument
    """

    architecture: Optional[str]
    """The Lambda architecture to build for"""


class BuildDotnet(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildDotnetArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildDotnet", name, {}, opts)
        result = build_dotnet(args)
        self.asset = result
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def build_dotnet(args: BuildDotnetArgs) -> FileArchive:
    builder = LambdaBuilder("dotnet", "cli-package", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or "x86_64"

    # TODO: add extra validation
    options = args.get("build_options")

    try:
        builder.build(
            source_dir=args.get("code"),
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=None,
            runtime=args.get("runtime"),
            architecture=arch,
            options=options,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
