import pytest
import os

from pulumi_lambda_builders.build_python import build_python, BuildPythonArgs


TEST_DATA_FOLDER = os.path.join(os.path.dirname(__file__), "testdata/simple-python")


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


def test_invalid_runtime():
    with pytest.raises(ValueError) as context:
        build_python(BuildPythonArgs(code=TEST_DATA_FOLDER, runtime="python3.00"))
    assert (
        "Runtime must be one of 'python3.8', 'python3.9', 'python3.10', 'python3.11', or 'python3.12'"
        in str(context)
    )


def test_invalid_architecture():
    with pytest.raises(ValueError) as context:
        build_python(
            BuildPythonArgs(
                code=TEST_DATA_FOLDER, runtime="python3.11", architecture="abc"
            )
        )
    assert (
        "PythonPipBuilder:Validation - Architecture abc is not supported for runtime python3.11"
        in str(context)
    )
