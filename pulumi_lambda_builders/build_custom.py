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
class BuildCustomMakeArgs:
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    and should contain the makefile
    """

    make_target_id: str
    """The make target id to build
    The make target is expected to be in the format of `build-{make_target_id}`
    """

    architecture: Optional[str] = "x86_64"
    """The Lambda architecture to build for
    :default: x86_64
    """


class BuildCustomMake(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildCustomMakeArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildCustomMake", name, {}, opts)
        result = build_go(args)
        self.asset = result


def build_go(args: BuildCustomMakeArgs) -> FileArchive:
    builder = LambdaBuilder("provided", None, None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.architecture or "x86_64"

    # TODO: add extra validation

    try:
        builder.build(
            source_dir=args.code,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            build_in_source=True,
            manifest_path=None,
            runtime="provided",
            architecture=arch,
            options={
                "build_logical_id": args.make_target_id,
            },
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
