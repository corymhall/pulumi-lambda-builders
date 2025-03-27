from pulumi.provider.experimental import component_provider_host
from pulumi_lambda_builders.build_custom import BuildCustomMake
from pulumi_lambda_builders.build_dotnet import BuildDotnet
from pulumi_lambda_builders.build_go import BuildGo
from pulumi_lambda_builders.build_java import BuildJava
from pulumi_lambda_builders.build_nodejs import BuildNodejs
from pulumi_lambda_builders.build_python import BuildPython
from pulumi_lambda_builders.build_rust import BuildRust
from pulumi_lambda_builders.build_ruby import BuildRuby


if __name__ == "__main__":
    # Call the component provider host. This will discover any ComponentResource
    # subclasses in this package, infer their schema and host a provider that
    # allows constructing these components from a Pulumi program.
    component_provider_host(
        name="lambda-builders",
        components=[
            BuildCustomMake,
            BuildDotnet,
            BuildGo,
            BuildJava,
            BuildNodejs,
            BuildPython,
            BuildRust,
            BuildRuby,
        ],
    )
