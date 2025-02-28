from projen import RenovatebotOptions
from projen.github import AutoApproveOptions, GitHubOptions, GitIdentity
from projen.python import ProjenrcOptions
from hallcor.pulumi_projen_project_types import PythonComponent

project = PythonComponent(
    author_email="43035978+corymhall@users.noreply.github.com",
    github_options=GitHubOptions(
        mergify=True,
    ),
    renovatebot=True,
    github_release_token="${{ secrets.PROJEN_GITHUB_TOKEN }}",
    git_identity=GitIdentity(
        email="43035978+corymhall@users.noreply.github.com",
        name="corymhall",
    ),
    renovatebot_options=RenovatebotOptions(
        schedule_interval=["before 3am on Monday"],
        labels=["auto-approve"],
    ),
    auto_approve_options=AutoApproveOptions(
        allowed_usernames=["corymhall", "renovate[bot]"],
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

unbump = project.tasks.try_find("unbump")
if unbump is not None:
    unbump.reset('echo "nothing to do here"')


project.add_git_ignore("node_modules")

project.synth()
