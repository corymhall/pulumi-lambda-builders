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
)


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


@dataclass
class BuildDotnetArgs:
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    """

    runtime: str
    """Dotnet version to build dependencies for."""

    build_options: Optional[dict] = None
    """Additional command line flags to pass to the dotnet build command
    The key should be prefixed with `-` or `--` like the cli argument
    """

    architecture: Optional[str] = "x86_64"
    """The Lambda architecture to build for
    :default: x86_64
    """


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


def build_dotnet(args: BuildDotnetArgs) -> FileArchive:
    builder = LambdaBuilder("dotnet", "cli-package", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.architecture or "x86_64"

    # TODO: add extra validation
    options = args.build_options

    try:
        builder.build(
            source_dir=args.code,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=None,
            runtime=args.runtime,
            architecture=arch,
            options=options,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
