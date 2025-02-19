from projen.python import PythonProject, VenvOptions

project = PythonProject(
    author_email="43035978+corymhall@users.noreply.github.com",
    author_name="corymhall",
    module_name="pulumi_lambda_builders",
    name="pulumi-lambda-builders",
    version="0.1.0",
    deps=["pulumi>=3.149,<4.0", "aws_lambda_builders"],
    venv_options=VenvOptions(envdir="venv"),
)

project.add_git_ignore("node_modules")

project.synth()
