# Pulumi Lambda Builders

---
> [!NOTE]
> Pulumi Lambda Builders is currently experimental

---

## Background

Pulumi Lambda Builders is a library that provides utilities for easily
building/bundling Lambda Function code. The library will eventually support the below languages/build tools.

- [X] Java with Gradle
- [X] Java with Maven
- [X] Dotnet with amazon.lambda.tools
- [X] Python with Pip
- [ ] Javascript with Npm
- [X] Typescript/JavaScript with esbuild
- [X] Ruby with Bundler
- [X] Go with Mod
- [X] Rust with Cargo
- [X] Custom with Makefile

This library integrates with the
[aws-lambda-builders](https://github.com/aws/aws-lambda-builders) library which
provides the building utilities.

## Installing

TODO:

## Python with Pip

```python
import pulumi
import pulumi_aws as aws
import pulumi_lambda_builder as builder

code = builder.BuildPython("builder",
    code="path/to/code",
    runtime="python3.12",
)

test_lambda = aws.lambda_.Function("my_lambda",
    code=code.asset,
    role=iam_for_lambda.arn,
    handler="main.handler",
    runtime=aws.lambda_.Runtime.PYTHON3D12,
)
```

## TypeScript/JavaScript with Esbuild

```ts
import * as path from 'path';
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';
import * as builder from '@pulumi/lambda-builder';

const code = new builder.BuildNodejs('builder', {
  entry: path.join(__dirname, 'path/to/index.ts'),
  runtime: 'nodejs18x',
});

new aws.lambda.Function('my-lambda', {
  code: code.asset,
  role: iamForLambda.arn,
  handler: 'index.handler',
  runtime=aws.lambda.Runtime.NodeJS18dX,
});
```

## Go with mod

```go
package main

import (
	"github.com/pulumi/pulumi-aws/sdk/v6/go/aws/lambda"
	"github.com/pulumi/pulumi/sdk/v3/go/pulumi"
    "github.com/pulumi/pulumi-lambda-builders/sdk/go/builder"
)

func main() {
	pulumi.Run(func(ctx *pulumi.Context) error {
        code, err := builder.BuildGo(ctx, "builder", &builder.BuildGoArgs{
            code: "path/to/code",
        })
        if err != nil {
            return err
        }
		_, err = lambda.NewFunction(ctx, "my_lambda", &lambda.FunctionArgs{
			Code:           code.Asset,
			Role:           iamForLambda.Arn,
			Handler:        pulumi.String("bootstrap"),
			Runtime:        pulumi.String(lambda.RuntimeCustomAL2023),
		})
		if err != nil {
			return err
		}
		return nil
	})
}
```

## Custom build with Makefile

If one of the existing language builders does not work for your use case or you
need to customize the build in a way that the existing builder does not allow,
you can use a Makefile with a specific build target.

You provide a custom makefile, where you declare a build target of the form
build-{some-build-id} that contains the build commands for your runtime.
Your makefile is responsible for compiling the custom runtime if necessary, and
copying the build artifacts into the artifacts directory that is specified in
the `$(ARTIFACTS_DIR)` env var.

```ts
import * as path from 'path';
import * as pulumi from '@pulumi/pulumi';
import * as aws from '@pulumi/aws';
import * as builder from '@pulumi/lambda-builder';

const code = new builder.BuildCustomMakefile('builder', {
  entry: path.join(__dirname, 'path/to/dir/with/makefile'),
  make_target_id: 'hello-world',
});

new aws.lambda.Function('my-lambda', {
  code: code.asset,
  role: iamForLambda.arn,
  handler: 'bootstrap',
  runtime=aws.lambda.Runtime.RuntimeCustomAL2023,
});
```

**Makefile**

```makefile
build-hello-world:
  GOOS=linux GOARCH=arm64 go build -o $(ARTIFACTS_DIR)/bootstrap -ldflags "-s -w"
```

## References

* TODO: Full docs for each builder
