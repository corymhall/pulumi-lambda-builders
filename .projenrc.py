from projen.python import ProjenrcOptions
from hallcor.pulumi_projen_project_types import PythonComponent

project = PythonComponent(
    author_email="43035978+corymhall@users.noreply.github.com",
    author_name="corymhall",
    module_name="pulumi_lambda_builders",
    component_name="lambda-builders",
    name="pulumi-lambda-builders",
    version="0.1.0",
    deps=[
        "aws_lambda_builders",
    ],
    projenrc_python_options=ProjenrcOptions(projen_version=">=0.91"),
    dev_deps=[
        "pyfakefs",
        "numpy",
        "hallcor.pulumi-projen-project-types",
    ],
)

project.add_git_ignore("node_modules")

project.synth()
