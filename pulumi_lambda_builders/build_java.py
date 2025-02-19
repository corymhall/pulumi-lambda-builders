import pulumi
import os
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


class BuildJavaArgs(TypedDict):
    code: str
    """The path to the code to build
    """

    runtime: str
    """Java version to build dependencies for."""

    architecture: Optional[str]
    """The Lambda architecture to build for
    :default: x86_64
    """


class BuildJava(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildJavaArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildJava", name, {}, opts)
        result = build_java(args)
        self.asset = result
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def build_java(args: BuildJavaArgs) -> FileArchive:
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or "x86_64"

    # TODO: add extra validation

    manifest_path = None
    dependency_manager = None
    if os.path.isfile(os.path.join(args.get("code"), "build.gradle")):
        manifest_path = os.path.join(args.get("code"), "build.gradle")
        dependency_manager = "gradle"
    elif os.path.isfile(os.path.join(args.get("code"), "build.gradle.kts")):
        manifest_path = os.path.join(args.get("code"), "build.gradle.kts")
        dependency_manager = "gradle"
    elif os.path.isfile(os.path.join(args.get("code"), "pom.xml")):
        manifest_path = os.path.join(args.get("code"), "pom.xml")
        dependency_manager = "maven"

    if not manifest_path:
        raise ValueError(
            "No build.gradle, build.gradle.kts, or pom.xml found in code directory"
        )

    builder = LambdaBuilder("java", dependency_manager, None)
    try:
        builder.build(
            source_dir=args.get("code"),
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=manifest_path,
            runtime=args.get("runtime"),
            architecture=arch,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build code: {err}")

    return FileArchive(tmp_dir)
