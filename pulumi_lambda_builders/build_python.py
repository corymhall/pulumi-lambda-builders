import pulumi
from enum import Enum
import os
from typing import List, Optional, TypedDict
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from pulumi.asset import FileArchive
from pulumi.log import warn
from aws_lambda_builders.validator import SUPPORTED_RUNTIMES
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
)

from pulumi_lambda_builders.utils import find_up


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


class BuildPythonArgs(TypedDict):
    code: str
    """The path to the code to build"""

    runtime: str
    """Python version to build dependencies for. This can be either 'python3.8',
    'python3.9', 'python3.10', 'python3.11', or 'python3.12'
    """

    architecture: Optional[str]
    """The Lambda architecture to build for"""

    requirements_path: Optional[str]
    """Path to the requirements.txt file to inspect for a list of dependencies"""
    """Path to the requirements.txt file to inspect for a list of dependencies"""


class BuildPython(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildPythonArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("lambda-builders:index:BuildPython", name, {}, opts)
        result = build_python(args)
        self.asset = result
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def validate_args(args: BuildPythonArgs):
    errors: List[pulumi.InputPropertyErrorDetails] = []
    python_runtimes = [
        runtime for runtime in SUPPORTED_RUNTIMES if runtime.startswith("python")
    ]
    if args.get("runtime") not in python_runtimes:
        errors.append(
            {
                "property_path": "runtime",
                "reason": f"Runtime must be one of {', '.join(python_runtimes)}",
            }
        )

    if args.get("architecture") not in [
        Architecture.ARM_64.value,
        Architecture.X86_64.value,
    ]:
        errors.append(
            {
                "property_path": "architecture",
                "reason": f"Architecture must be one of {Architecture.ARM_64.value}, {Architecture.X86_64.value}",
            }
        )

    requirements_path = args.get("requirements_path")
    if requirements_path is not None:
        if not os.path.isfile(requirements_path):
            errors.append(
                {
                    "property_path": "requirements_path",
                    "reason": f"requirements.txt not found at path provided: {args.get('requirements_path')}",
                }
            )

    for error in errors:
        print(f"Invalid argument for {error['property_path']}: {error['reason']}")
    if errors.__len__() > 0:
        raise pulumi.InputPropertiesError("Invalid arguments", errors)


def build_python(args: BuildPythonArgs) -> FileArchive:
    builder = LambdaBuilder("python", "pip", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.get("architecture") or Architecture.X86_64.value
    code = os.path.abspath(args.get("code"))

    args["architecture"] = arch

    validate_args(args)

    req = os.path.join(code, "requirements.txt")
    if args.get("requirements_path") is not None:
        req = args.get("requirements_path")

    req = find_up("requirements.txt", code)
    if not req:
        warn(
            "requirements.txt file not found. Continuing the build without dependencies."
        )

    if not os.path.isdir(code):
        code = os.path.dirname(code)
        warn(f"code path is not a directory, using parent directory {code} instead")

    try:
        builder.build(
            source_dir=code,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.mkdtemp(prefix="lambda_"),
            manifest_path=req,
            runtime=args.get("runtime"),
            architecture=arch,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build Python code: {err}")

    return FileArchive(tmp_dir)
