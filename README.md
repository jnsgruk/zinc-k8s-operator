# Zinc Operator

This repository contains the source code for a Charmed Operator that drives [Zinc] on Kubernetes.

[Zinc] is a search engine that does full text indexing. It is a lightweight alternative to
[elasticsearch] and runs in less than 100 MB of RAM. It uses [bluge] as the underlying indexing
library.

It is very simple and easy to operate as opposed to elasticsearch which requires a couple dozen
knobs to understand and tune.

It is a drop-in replacement for elasticsearch if you are just ingesting data using APIs and
searching using kibana (Kibana is not supported with zinc. Zinc provides its own UI).

## Usage

Assuming you have access to a bootstrapped Juju controller on Kubernetes, you can simply:

```bash
juju deploy zinc # --trust (use when cluster has RBAC enabled)
```

## OCI Images

This charm uses the image provided by the upstream on Amazon ECR: [zinc:v1]

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and
[CONTRIBUTING.md](./CONTRIBUTING.md) for developer guidance.

[zinc]: https://github.com/prabhatsharma/zinc
[bluge]: https://github.com/blugelabs/bluge
[elasticsearch]: https://www.elastic.co/
[zinc:v1]: public.ecr.aws/m5j1b6u0/zinc:v1
