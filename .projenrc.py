from projen.python import PythonProject

project = PythonProject(
    author_email="43035978+corymhall@users.noreply.github.com",
    author_name="corymhall",
    module_name="pulumi_lambda_builders",
    name="pulumi-lambda-builders",
    version="0.1.0",
)

project.synth()