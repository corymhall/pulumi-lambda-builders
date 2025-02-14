import pytest
from unittest.mock import patch
import os
from pulumi_lambda_builders.build_nodejs import build_nodejs, BuildNodejsArgs
from pulumi.asset import FileArchive

from aws_lambda_builders.exceptions import LambdaBuilderError

TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "testdata/simple-nodejs")


def test_build_nodejs_calls_builder_with_correct_args(fs):
    # Setup the fake filesystem
    fs.create_file("/fake_dir/index.js")
    fs.create_file("/fake_dir/package-lock.json")
    args = BuildNodejsArgs(
        entry="/fake_dir/project/index.ts",
        runtime="nodejs18.x",
    )

    with patch("pulumi_lambda_builders.build_nodejs.LambdaBuilder.build") as mock_build:
        build_nodejs(args)
        mock_build.assert_called_once()
        mock_build.assert_called_with(
            source_dir="/fake_dir/project",
            runtime="nodejs18.x",
            artifacts_dir=mock_build.call_args[1][
                "artifacts_dir"
            ],  # We don't know the exact temp dir
            scratch_dir=mock_build.call_args[1][
                "scratch_dir"
            ],  # We don't know the exact temp dir
            download_dependencies=True,
            dependencies_dir="/fake_dir/project/node_modules",
            architecture="x86_64",
            options={
                "entry_points": ["index.ts"],
                "minify": True,
                "format": "cjs",
                "target": "node18",
            },
        )
