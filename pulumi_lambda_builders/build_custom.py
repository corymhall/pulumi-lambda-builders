import pulumi
from enum import Enum
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


class BuildCustomMakeArgs(TypedDict):
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    and should contain the makefile
    """

    make_target_id: str
    """The make target id to build
    The make target is expected to be in the format of `build-{make_target_id}`
    """

    architecture: Optional[str]
    """The Lambda architecture to build for"""


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
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def build_go(args: BuildCustomMakeArgs) -> FileArchive:
    builder = LambdaBuilder("provided", None, None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or "x86_64"

    # TODO: add extra validation

    try:
        builder.build(
            source_dir=args.get("code"),
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            build_in_source=True,
            manifest_path=None,
            runtime="provided",
            architecture=arch,
            options={
                "build_logical_id": args.get("make_target_id"),
            },
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
