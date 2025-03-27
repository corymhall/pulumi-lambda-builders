from projen.github import AutoApproveOptions
from projen.python import ProjenrcOptions
from hallcor.pulumi_projen_project_types import (
    GithubCredentials,
    PulumiEscSetup,
    PythonComponent,
)

project = PythonComponent(
    author_email="43035978+corymhall@users.noreply.github.com",
    auto_approve_options=AutoApproveOptions(
        allowed_usernames=["corymhall", "hallcor-projen-app[bot]"],
        label="auto-approve",
    ),
    author_name="corymhall",
    module_name="pulumi_lambda_builders",
    component_name="lambda-builders",
    name="pulumi-lambda-builders",
    version="0.1.0",
    deps=[
        "aws_lambda_builders",
    ],
    projen_credentials=GithubCredentials.from_app(
        pulumi_esc_setup=PulumiEscSetup.from_oidc_auth(
            environment="github/public",
            organization="corymhall",
        ),
    ),
    projenrc_python_options=ProjenrcOptions(projen_version=">=0.91"),
    dev_deps=[
        "pyfakefs",
        "numpy",
        "hallcor.pulumi-projen-project-types",
    ],
)

project.test_task.prepend_exec(
    "npm ci",
    cwd="tests/testdata/simple-nodejs",
    condition="if [ -d 'node_modules' ]; then exit 1; else exit 0; fi",
)

project.add_git_ignore("node_modules")
project.add_git_ignore("examples/**/sdks")

project.synth()
