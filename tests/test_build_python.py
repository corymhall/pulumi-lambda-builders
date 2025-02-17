from unittest.mock import ANY, patch
import pulumi
from pyfakefs.fake_filesystem_unittest import TestCase
import pytest
import os

from pulumi_lambda_builders.build_python import build_python, BuildPythonArgs
from tests.utils import assert_input_properties_error


TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "testdata/simple-python")


def build_python_call_args(
    source_dir=ANY,
    runtime=ANY,
    manifest_path=ANY,
    architecture=ANY,
):
    return {
        "source_dir": source_dir,
        "runtime": runtime,
        "artifacts_dir": ANY,
        "scratch_dir": ANY,
        "manifest_path": manifest_path,
        "architecture": architecture,
    }


def test_success():
    res = build_python(
        args=BuildPythonArgs(
            code=TEST_DATA_FOLDER, runtime="python3.11", architecture="x86_64"
        )
    )

    files = os.listdir(res.path)
    print(res.path)
    print(files)
    assert "main.py" in files


class TestBuildPythonErrors(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setUpClassPyfakefs()
        fake_fs = cls.fake_fs()
        assert fake_fs is not None
        fake_fs.cwd = "/fake_dir/project"
        fake_fs.create_file("/fake_dir/project/app/main.py", contents="test")
        fake_fs.create_file("/fake_dir/project/requirements.txt", contents="{}")

    def test_invalid_runtime(self):
        args = BuildPythonArgs(
            code="/fake_dir/project/app",
            runtime="python3.99",  # Invalid runtime
        )
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_python(args)
        assert_input_properties_error(exc_info, "runtime", "Runtime must be one of")

    def test_invalid_architecture(self):
        args = BuildPythonArgs(
            code="/fake_dir/project/app",
            runtime="python3.8",
            architecture="invalid-arch",  # Invalid architecture
        )
        with pytest.raises(pulumi.InputPropertiesError) as exc_info:
            build_python(args)
        assert_input_properties_error(
            exc_info, "architecture", "Architecture must be one of arm64, x86_64"
        )


class TestBuildPython(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_build_python_calls_builder_with_correct_args(self):
        # Setup the fake filesystem
        self.fs.create_file("/fake_dir/project/requirements.txt")
        self.fs.create_file("/fake_dir/project/app/main.py", contents="test")
        # Mock the current working directory
        self.fs.cwd = "/fake_dir/project"
        assert os.getcwd() == "/fake_dir/project"
        args = BuildPythonArgs(
            code="app",
            runtime="python3.8",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_python(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_python_call_args(
                    source_dir="/fake_dir/project/app",
                    runtime="python3.8",
                    manifest_path="/fake_dir/project/requirements.txt",
                    architecture="x86_64",
                )
            )

    def test_build_python_find_lockfile(self):
        self.fs.create_file("/fake_dir/project/requirements.txt")
        self.fs.create_file("/fake_dir/project/app/main.py", contents="test")
        self.fs.cwd = "/fake_dir/project/app"
        args = BuildPythonArgs(
            code="./",
            runtime="python3.8",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_python(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_python_call_args(
                    manifest_path="/fake_dir/project/requirements.txt",
                )
            )

    def test_build_python_find_first_lockfile(self):
        self.fs.create_file("/fake_dir/project/requirements.txt")
        self.fs.create_file("/fake_dir/project/app/requirements.txt")
        self.fs.create_file("/fake_dir/project/app/main.py", contents="test")
        self.fs.cwd = "/fake_dir/project/app"
        args = BuildPythonArgs(
            code="./",
            runtime="python3.8",
        )

        with patch("aws_lambda_builders.builder.LambdaBuilder.build") as mock_build:
            build_python(args)
            mock_build.assert_called_once()
            mock_build.assert_called_with(
                **build_python_call_args(
                    manifest_path="/fake_dir/project/app/requirements.txt",
                )
            )
