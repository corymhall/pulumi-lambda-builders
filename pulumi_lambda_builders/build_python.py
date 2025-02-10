from dataclasses import dataclass
import pulumi
from enum import Enum
import os
from typing import Optional, TypedDict
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from pulumi.asset import FileArchive
from pulumi.log import warn
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
    UnsupportedArchitectureError,
)

from aws_lambda_builders.workflows.python_pip.utils import OSUtils


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


@dataclass
class BuildPythonArgs:
    code: str
    """The path to the code to build"""

    runtime: str
    """Python version to build dependencies for. This can be either 'python3.8',
    'python3.9', 'python3.10', 'python3.11', or 'python3.12'
    """

    architecture: Optional[str] = None
    """The Lambda architecture to build for"""

    requirements_path: Optional[str] = None
    """Path to the requirements.txt file to inspect for a list of dependencies"""

    download_dependencies: Optional[bool] = None
    """If set to true, builder will run pip install -r requirements.txt"""

    dependencies_dir: Optional[str] = None
    """A directory which contains the python dependencies."""


class BuildPython(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildPythonArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("pulumi-lambda-builders:index:BuildPython", name, {}, opts)
        result = build_python(args)
        self.asset = result


def build_python(args: BuildPythonArgs) -> FileArchive:
    osutils = OSUtils()
    builder = LambdaBuilder("python", "pip", None)
    tmp_dir = tempfile.mkdtemp()
    arch = args.architecture or Architecture.X86_64.value
    code = args.code

    req = os.path.join(code, "requirements.txt")
    if args.requirements_path != None:
        req = args.requirements_path
        if not osutils.file_exists(req):
            raise ValueError(
                f"requirements.txt not found at path provided: {args.requirements_path}"
            )

    found = osutils.file_exists(req)
    dir = os.path.dirname(req)
    while not found:
        parent = os.path.dirname(dir)
        if parent == "":
            warn(
                "requirements.txt file not found. Continuing the build without dependencies."
            )
            found = True
            break
        dir_contents = os.listdir(parent)
        if "requirements.txt" in dir_contents:
            req = os.path.join(parent, "requirements.txt")
            found = True
        else:
            dir = parent

    if args.runtime not in [
        "python3.8",
        "python3.9",
        "python3.10",
        "python3.11",
        "python3.12",
    ]:
        raise ValueError(
            "Runtime must be one of 'python3.8', 'python3.9', 'python3.10', 'python3.11', or 'python3.12'"
        )

    download_dependencies = True
    if args.download_dependencies != None:
        args.download_dependencies = args.download_dependencies

    try:
        builder.build(
            source_dir=code,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.mkdtemp(prefix="lambda_"),
            manifest_path=req,
            runtime=args.runtime,
            architecture=arch,
            dependencies_dir=args.dependencies_dir,
            download_dependencies=download_dependencies,
        )
    except UnsupportedArchitectureError as err:
        print(err)
        raise ValueError("Unsupported architecture")
    # The only two input properties are code & architecture & lambda_builders only throws a specific
    # error for architecture. The rest of the errors we can return as generic errors
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build Python code: {err}")

    return FileArchive(tmp_dir)
