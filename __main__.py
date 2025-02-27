from pulumi.provider.experimental import component_provider_host, Metadata
import json

with open(".version.json", "r") as f:
    pyproject = json.load(f)
version = pyproject["version"]

if __name__ == "__main__":
    # Call the component provider host. This will discover any ComponentResource
    # subclasses in this package, infer their schema and host a provider that
    # allows constructing these components from a Pulumi program.
    component_provider_host(Metadata("lambda-builders", version))
