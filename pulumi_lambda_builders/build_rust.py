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


class BuildRustArgs(TypedDict):
    code: str
    """The path to the code to build
    This will be used as the source directory for the build
    """

    architecture: Optional[str]
    """The Lambda architecture to build for"""

    binary_name: Optional[str]
    """The name of the binary to build
    This is only needed if you are building a project using cargo workspaces
    """

    cargo_flags: Optional[Dict[str, str]]
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
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def build_rust(args: BuildRustArgs) -> FileArchive:
    builder = LambdaBuilder("rust", "cargo", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or "x86_64"

    # TODO: add extra validation

    options = {}
    if args.get("binary_name"):
        options["artifact_executable_name"] = args.get("binary_name")
    if args.get("cargo_flags"):
        options["cargo_lambda_flags"] = args.get("cargo_flags")

    try:
        builder.build(
            source_dir=args.get("code"),
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
