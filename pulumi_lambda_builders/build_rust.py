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
class BuildRustArgs:
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    """

    architecture: Optional[str] = "x86_64"
    """The Lambda architecture to build for
    :default: x86_64
    """

    binary_name: Optional[str] = None
    """The name of the binary to build
    This is only needed if you are building a project using cargo workspaces
    """

    cargo_flags: Optional[dict] = None
    """Additional flags to pass to cargo when building the code
    The keys should be prefixed with `--` (just like CLI flags)"""


class BuildRust(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildRustArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildRust", name, {}, opts)
        result = build_rust(args)
        self.asset = result


def build_rust(args: BuildRustArgs) -> FileArchive:
    builder = LambdaBuilder("rust", "cargo", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.architecture or "x86_64"

    # TODO: add extra validation

    options = {}
    if args.binary_name:
        options["artifact_executable_name"] = args.binary_name
    if args.cargo_flags:
        options["cargo_lambda_flags"] = args.cargo_flags

    try:
        builder.build(
            source_dir=args.code,
            experimental_flags={
                "experimentalCargoLambda": True,
            },
            build_in_source=True,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=None,
            runtime="provided",
            architecture=arch,
            options=options,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
