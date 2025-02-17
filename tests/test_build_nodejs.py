import pytest
from unittest.mock import patch, ANY

import pulumi
from pyfakefs.fake_filesystem_unittest import TestCase
import os
from pulumi_lambda_builders.build_nodejs import build_nodejs, BuildNodejsArgs
from tests.utils import assert_input_properties_error

TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "testdata/simple-nodejs")


def test_esbuild():
    res = build_nodejs(
        args=BuildNodejsArgs(
            entry=os.path.join(TEST_DATA_FOLDER, "app/index.ts"),
            runtime="nodejs18.x",
            lock_file_path=os.path.join(TEST_DATA_FOLDER, "package-lock.json"),
        )
    )

    files = os.listdir(res.path)
    print(res.path)
    print(files)
    assert "index.js" in files


def build_nodejs_call_args(
    source_dir=ANY,
    runtime=ANY,
    artifacts_dir=ANY,
    scratch_dir=ANY,
    manifest_path=ANY,
    download_dependencies=ANY,
    dependencies_dir=ANY,
    build_in_source=ANY,
    architecture=ANY,
    options=ANY,
):
    return {
        "source_dir": source_dir,
        "runtime": runtime,
        "artifacts_dir": artifacts_dir,
        "scratch_dir": scratch_dir,
        "manifest_path": manifest_path,
        "download_dependencies": download_dependencies,
        "dependencies_dir": dependencies_dir,
        "build_in_source": build_in_source,
        "architecture": architecture,
        "options": options,
    }


class TestBuildNodejsErrors(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setUpClassPyfakefs()
        fake_fs = cls.fake_fs()
        assert fake_fs is not None
        fake_fs.cwd = "/fake_dir/project"
        fake_fs.create_file("/fake_dir/project/app/index.ts", contents="test")
        fake_fs.create_file("/fake_dir/project/package-lock.json", contents="{}")

    def test_invalid_runtime(self):
        args = BuildNodejsArgs(
            entry="app/index.ts",
            runtime="nodejs14.x",  # Invalid runtime
        )
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_nodejs(args)
        assert_input_properties_error(exc_info, "runtime", "Runtime must be one of")

    def test_invalid_architecture(self):
        args = BuildNodejsArgs(
            entry="app/index.ts",
            runtime="nodejs18.x",
            architecture="invalid-arch",  # Invalid architecture
        )
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_nodejs(args)
        assert_input_properties_error(
            exc_info, "architecture", "Architecture must be one of arm64, x86_64"
        )

    def test_nonexistent_entry_file(self):
        args = BuildNodejsArgs(
            entry="app/nonexistent.ts",  # Nonexistent file
            runtime="nodejs18.x",
        )
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_nodejs(args)
        assert_input_properties_error(
            exc_info, "entry", "Cannot find entry file at app/nonexistent.ts"
        )


class TestBuildNodejsErrorsCustom(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_invalid_entry_file_type(self):
        args = BuildNodejsArgs(
            entry="app/index.txt",  # Invalid file type
            runtime="nodejs18.x",
        )
        self.fs.create_file("/fake_dir/project/app/index.txt", contents="test")
        self.fs.cwd = "/fake_dir/project"
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_nodejs(args)
        assert_input_properties_error(
            exc_info, "entry", "Entry file must be a JavaScript or TypeScript file"
        )

    def test_cannot_find_lockfile(self):
        self.fs.create_file("/fake_dir/project/app/index.ts", contents="test")
        self.fs.create_file("/fake_dir/project/package-lock.json", contents="{}")
        self.fs.cwd = "/fake_dir"

        args = BuildNodejsArgs(
            entry="project/app/index.ts",
            runtime="nodejs18.x",
        )
        with pytest.raises(pulumi.InputPropertyError) as exc_info:
            build_nodejs(args)
        assert_input_properties_error(
            exc_info,
            "lock_file_path",
            "Cannot find package-lock.json file. Please provide the path to the file",
        )


class TestBuildNodejs(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_build_nodejs_calls_builder_with_correct_args(self):
        # Setup the fake filesystem
        self.fs.create_file("/fake_dir/project/package-lock.json")
        self.fs.create_file("/fake_dir/project/app/index.ts", contents="test")
        # Mock the current working directory
        self.fs.cwd = "/fake_dir/project"
        assert os.path.abspath("app/index.ts") == "/fake_dir/project/app/index.ts"
        assert os.path.exists(os.path.abspath("app/index.ts"))
        assert os.getcwd() == "/fake_dir/project"
        args = BuildNodejsArgs(
            entry="app/index.ts",
            runtime="nodejs18.x",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_nodejs(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_nodejs_call_args(
                    source_dir="/fake_dir/project",
                    runtime="nodejs18.x",
                    manifest_path="/fake_dir/project/package-lock.json",
                    download_dependencies=True,
                    dependencies_dir="/fake_dir/project/node_modules",
                    build_in_source=True,
                    architecture="x86_64",
                    options={
                        "entry_points": ["app/index.ts"],
                        "external": ["@aws-sdk/*", "@smithy/*"],
                        "minify": True,
                        "format": "cjs",
                        "target": "node18",
                    },
                )
            )

    def test_build_nodejs_find_lockfile(self):
        self.fs.create_file("/fake_dir/project/package-lock.json")
        self.fs.create_file("/fake_dir/project/app/index.ts", contents="test")
        self.fs.cwd = "/fake_dir/project/app"
        args = BuildNodejsArgs(
            entry="index.ts",
            runtime="nodejs18.x",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_nodejs(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_nodejs_call_args(
                    manifest_path="/fake_dir/project/package-lock.json",
                    options={
                        "entry_points": ["app/index.ts"],
                        "external": ["@aws-sdk/*", "@smithy/*"],
                        "minify": True,
                        "format": "cjs",
                        "target": "node18",
                    },
                )
            )

    def test_build_nodejs_find_first_lockfile(self):
        self.fs.create_file("/fake_dir/project/package-lock.json")
        self.fs.create_file("/fake_dir/project/app/package-lock.json")
        self.fs.create_file("/fake_dir/project/app/index.ts", contents="test")
        self.fs.cwd = "/fake_dir/project/app"
        args = BuildNodejsArgs(
            entry="index.ts",
            runtime="nodejs18.x",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_nodejs(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_nodejs_call_args(
                    manifest_path="/fake_dir/project/app/package-lock.json",
                    options={
                        "entry_points": ["index.ts"],
                        "external": ["@aws-sdk/*", "@smithy/*"],
                        "minify": True,
                        "format": "cjs",
                        "target": "node18",
                    },
                )
            )
