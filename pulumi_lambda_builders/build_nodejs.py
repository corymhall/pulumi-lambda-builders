from dataclasses import dataclass
import pulumi
from enum import Enum
import os
import re
from typing import Optional, TypedDict, List
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from aws_lambda_builders.validator import SUPPORTED_RUNTIMES
from pulumi.asset import FileArchive
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
    UnsupportedArchitectureError,
)


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


@dataclass
class EsbuildOptions:
    external: Optional[List[str]] = None
    """Specifies the list of packages to omit from the build"""


@dataclass
class BuildNodejsArgs:
    entry: str
    """Path to the entry file (JavaScript or TypeScript)."""

    runtime: str
    """Node.js version to build dependencies for."""

    lock_file_path: Optional[str] = None
    """Path to the package-lock.json file to use for installing dependencies
    :default: the path is found by walking up parent directories searching for
    a package-lock.json file
    """

    node_modules_path: Optional[str] = None
    """Path to the node_modules directory.
    :default: The path will be assumed to be in the same directory as the package-lock.json file
    """

    external: Optional[List[str]] = None
    """Specifies the list of packages to omit from the build"""

    architecture: Optional[str] = "x86_64"
    """The Lambda architecture to build for"""

    bundler: Optional[str] = "npm-esbuild"
    """The bundler to use for building the code. Valid values are 'npm-esbuild' or 'npm'"""

    bundle_aws_sdk: Optional[bool] = False
    """Includes the AWS SDK in the bundle asset
    :default: false
    if set to true, the AWS SDK will be included in the bundle asset
    and not be resolved to the Lambda provided SDK"""

    esbuild_options: Optional[EsbuildOptions] = None
    """Extra config options for the esbuild bundler"""

    minify: Optional[bool] = True
    """Whether to minify the output. Not supported for 'npm' bundler"""

    format: Optional[str] = "cjs"
    """This sets the output format for the generated JavaScript files.
    There are currently three possible values that can be configured: iife, cjs, and esm.
    """

    target: Optional[str] = None
    """This sets the target environment for the generated JavaScript files.
    :default: The target is determined from the runtime
    """


class BuildNodejs(pulumi.ComponentResource):
    asset: FileArchive
    """The built code asset"""

    def __init__(
        self,
        name: str,
        args: BuildNodejsArgs,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        super().__init__("pulumi-lambda-builders:index:BuildNodejs", name, {}, opts)

        result = build_nodejs(args)
        self.asset = result


def validate_args(args: BuildNodejsArgs):
    errors: List[pulumi.InputPropertyErrorDetails] = []
    nodejs_runtimes = [
        runtime
        for runtime in SUPPORTED_RUNTIMES
        if runtime.startswith("nodejs") and runtime != "nodejs16.x"
    ]
    if args.runtime not in nodejs_runtimes:
        errors.append(
            {
                "property_path": "runtime",
                "reason": f"Runtime must be one of {', '.join(nodejs_runtimes)}",
            }
        )

    if args.bundler not in ["npm-esbuild", "npm"]:
        errors.append(
            {
                "property_path": "bundler",
                "reason": "Bundler must be one of 'npm-esbuild' or 'npm'",
            }
        )

    if args.architecture not in [
        Architecture.ARM_64.value,
        Architecture.X86_64.value,
    ]:
        errors.append(
            {
                "property_path": "architecture",
                "reason": f"Architecture must be one of {Architecture.ARM_64.value}, {Architecture.X86_64.value}",
            }
        )

    if not re.search(r"\.(js|ts)$", args.entry):
        errors.append(
            {
                "property_path": "entry",
                "reason": "Entry file must be a JavaScript or TypeScript file",
            }
        )
    if not os.path.exists(args.entry):
        errors.append(
            {
                "property_path": "entry",
                "reason": f"Cannot find entry file at {args.entry}",
            }
        )

    if errors.__len__() > 0:
        raise pulumi.InputPropertiesError("Invalid arguments", errors)


def build_nodejs(args: BuildNodejsArgs) -> FileArchive:
    builder = LambdaBuilder("nodejs", args.bundler, None)
    tmp_dir = tempfile.mkdtemp()

    default_externals = ["@aws-sdk/*", "@smithy/*"]

    externals = args.external or default_externals

    validate_args(args)

    lock_file = find_lock_file(args.lock_file_path)
    if not lock_file:
        raise pulumi.InputPropertyError(
            "lock_file_path",
            "Cannot find package-lock.json file. Please provide the path to the file",
        )
    project_dir = os.path.dirname(lock_file)
    relative_entry_path = os.path.relpath(project_dir, os.path.abspath(args.entry))

    target = args.target
    if not target:
        match = re.search(r"nodejs(\d+)", args.runtime)
        if not match or not match.group(1):
            raise pulumi.InputPropertyError(
                "target",
                "Could not determine the target from the runtime. Please provide the target",
            )
        target = f"node{match.group(1)}"

    download_dependencies = True
    node_modules_path = args.node_modules_path or os.path.join(
        project_dir, "node_modules"
    )
    if os.path.exists(node_modules_path):
        download_dependencies = False

    options = {
        "entry_points": [relative_entry_path],
        "external": externals,
        "minify": args.minify,
        "format": args.format,
        "target": target,
    }

    if args.format == "ems":
        options["out_extensions"] = [".js=.mjs"]

    try:
        builder.build(
            source_dir=project_dir,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=lock_file,
            download_dependencies=download_dependencies,
            dependencies_dir=node_modules_path,
            # TODO: I think this is what we want, but do we let the user config?
            build_in_source=True,
            runtime=args.runtime,
            architecture=args.architecture or Architecture.X86_64.value,
            options=options,
        )
    except UnsupportedArchitectureError as err:
        print(err)
        raise ValueError("Unsupported architecture")
    # The only two input properties are code & architecture & lambda_builders only throws a specific
    # error for architecture. The rest of the errors we can return as generic errors
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build Go code: {err}")

    return FileArchive(tmp_dir)


def find_lock_file(lock_file_path: Optional[str]) -> Optional[str]:
    if lock_file_path:
        if not os.path.exists(lock_file_path):
            raise pulumi.InputPropertyError(
                "lock_file_path",
                f"Cannot find lock file at {lock_file_path}",
            )
        if not os.path.isfile(lock_file_path):
            raise pulumi.InputPropertyError(
                "lock_file_path",
                f"Lock file path must be a file, got {lock_file_path}",
            )
        return lock_file_path
    return find_up("package-lock.json")


def find_up(filename: str, dir: str = os.getcwd()) -> Optional[str]:
    if os.path.exists(os.path.join(dir, filename)):
        return os.path.join(dir, filename)
    if dir == get_root_directory(dir):
        return None
    return find_up(filename, os.path.dirname(dir))


def get_root_directory(path: str) -> str:
    # Split the drive and path
    drive, _ = os.path.splitdrive(path)

    # For Unix-like systems, the root is simply '/'
    if path.startswith("/"):
        return "/"

    # For Windows, return the drive as the root
    return drive
