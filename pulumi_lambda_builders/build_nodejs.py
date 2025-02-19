import pulumi
from enum import Enum
import os
import re
from typing import Optional, List, TypedDict
import tempfile
from aws_lambda_builders.builder import LambdaBuilder
from aws_lambda_builders.validator import SUPPORTED_RUNTIMES
from pulumi.asset import FileArchive
from aws_lambda_builders.exceptions import (
    LambdaBuilderError,
)

from pulumi_lambda_builders.utils import find_up


class Architecture(Enum):
    ARM_64 = "arm64"
    X86_64 = "x86_64"


class BuildNodejsArgs(TypedDict):
    entry: str
    """Path to the entry file (JavaScript or TypeScript)."""

    runtime: str
    """Node.js version to build dependencies for."""

    package_json_path: Optional[str]
    """Path to the package.json file to use for installing dependencies
    :default: the path is found by walking up parent directories searching for
    a package.json file
    """

    node_modules_path: Optional[str]
    """Path to the node_modules directory.
    :default: The path will be assumed to be in the same directory as the package-lock.json file
    """

    external: Optional[List[str]]
    """Specifies the list of packages to omit from the build
    :default: ["@aws-sdk/*", "@smithy/*"]
    """

    architecture: Optional[str]
    """The Lambda architecture to build for"""

    bundle_aws_sdk: Optional[bool]
    """Includes the AWS SDK in the bundle asset
    :default: false
    if set to true, the AWS SDK will be included in the bundle asset
    and not be resolved to the Lambda provided SDK"""

    # TODO: Add support for other esbuild options
    # esbuild_options: Optional[EsbuildOptions] = None
    # """Extra config options for the esbuild bundler"""

    minify: Optional[bool]
    """Whether to minify the output. Not supported for 'npm' bundler"""

    format: Optional[str]
    """This sets the output format for the generated JavaScript files.
    There are currently three possible values that can be configured: iife, cjs, and esm.
    """

    target: Optional[str]
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
        super().__init__("lambda-builders:index:BuildNodejs", name, {}, opts)

        result = build_nodejs(args)
        self.asset = result
        self.register_outputs(
            {
                "asset": self.asset,
            }
        )


def validate_args(args: BuildNodejsArgs):
    errors: List[pulumi.InputPropertyErrorDetails] = []
    nodejs_runtimes = [
        runtime
        for runtime in SUPPORTED_RUNTIMES
        if runtime.startswith("nodejs") and runtime != "nodejs16.x"
    ]
    if args.get("runtime") not in nodejs_runtimes:
        errors.append(
            {
                "property_path": "runtime",
                "reason": f"Runtime must be one of {', '.join(nodejs_runtimes)}",
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

    if not re.search(r"\.(js|ts)$", args.get("entry")):
        errors.append(
            {
                "property_path": "entry",
                "reason": "Entry file must be a JavaScript or TypeScript file",
            }
        )
    if not os.path.exists(os.path.abspath(args.get("entry"))):
        errors.append(
            {
                "property_path": "entry",
                "reason": f"Cannot find entry file at {args.get('entry')}",
            }
        )

    for error in errors:
        print(f"Invalid argument for {error['property_path']}: {error['reason']}")
    if errors.__len__() > 0:
        raise pulumi.InputPropertiesError("Invalid arguments", errors)


def build_nodejs(args: BuildNodejsArgs) -> FileArchive:
    tmp_dir = tempfile.mkdtemp()

    args["architecture"] = args.get("architecture") or Architecture.X86_64.value

    default_externals = ["@aws-sdk/*", "@smithy/*"]
    externals = args.get("external") or default_externals

    validate_args(args)

    manifest_file = find_lock_file(args.get("package_json_path"))
    if not manifest_file:
        raise pulumi.InputPropertyError(
            "lock_file_path",
            "Cannot find package.json file. Please provide the path to the file",
        )
    project_dir = os.path.dirname(manifest_file)
    relative_entry_path = os.path.relpath(
        os.path.abspath(args.get("entry")), project_dir
    )

    target = args.get("target")
    if not target:
        match = re.search(r"nodejs(\d+)", args.get("runtime"))
        if not match or not match.group(1):
            raise pulumi.InputPropertyError(
                "target",
                "Could not determine the target from the runtime. Please provide the target",
            )
        target = f"node{match.group(1)}"

    download_dependencies = True
    node_modules_path = args.get("node_modules_path") or os.path.join(
        project_dir, "node_modules"
    )
    if os.path.exists(node_modules_path):
        download_dependencies = False

    options = {
        "entry_points": [relative_entry_path],
        "external": externals,
        "minify": args.get("minify") or True,
        "format": args.get("format") or "cjs",
        "target": target,
    }

    if download_dependencies == True:
        found = find_up("package-lock.json", os.getcwd())
        if found is not None:
            options["use_npm_ci"] = True
        else:
            pulumi.warn(
                "node_modules not found and package-lock.json not found, installing dependencies using npm install --production"
            )
        pulumi.warn("node_modules not found, installing dependencies using npm ci")

    if args.get("format") == "esm":
        options["out_extensions"] = [".js=.mjs"]

    builder = LambdaBuilder("nodejs", "npm-esbuild", None)
    try:
        builder.build(
            source_dir=project_dir,
            artifacts_dir=tmp_dir,
            scratch_dir=tempfile.gettempdir(),
            manifest_path=manifest_file,
            download_dependencies=download_dependencies,
            dependencies_dir=node_modules_path,
            # TODO: I think this is what we want, but do we let the user config?
            build_in_source=True,
            runtime=args.get("runtime"),
            architecture=args.get("architecture") or Architecture.X86_64.value,
            options=options,
        )
    except LambdaBuilderError as err:
        raise ValueError(f"Failed to build Nodejs code: {err}")

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
    return find_up("package.json", os.getcwd())
