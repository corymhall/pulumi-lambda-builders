import pulumi
from enum import Enum
import os
from typing import Optional, TypedDict
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from pulumi.asset import FileArchive
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
)


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


class BuildRubyArgs(TypedDict):
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    """

    runtime: str
    """Ruby version to build dependencies for."""

    architecture: Optional[str]
    """The Lambda architecture to build for"""


class BuildRuby(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildRubyArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildRuby", name, {}, opts)
        result = build_ruby(args)
        self.asset = result
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def build_ruby(args: BuildRubyArgs) -> FileArchive:
    builder = LambdaBuilder("ruby", "bundler", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or "x86_64"

    # TODO: add extra validation

    try:
        builder.build(
            source_dir=args.get("code"),
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=None,
            runtime=args.get("runtime"),
            architecture=arch,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
