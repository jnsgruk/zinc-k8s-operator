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
$ juju deploy zinc-k8s # --trust (use when cluster has RBAC enabled)
```

You can monitor the deployment of Zinc using `juju status`. Once the application displays status
`active`, you can go ahead and browse to the IP address of Zinc. Before that, you'll need to fetch
the auto-generated password to login (example output):

```bash
$ juju run-action zinc-k8s/0 get-admin-password --wait
unit-zinc-k8s-0:
  UnitId: zinc-k8s/0
  id: "6"
  results:
    admin-password: ZzRkyyFRVFNy3Qv5JQ6tYEkq
  status: completed
  timing:
    completed: 2021-12-06 15:15:14 +0000 UTC
    enqueued: 2021-12-06 15:15:12 +0000 UTC
    started: 2021-12-06 15:15:13 +0000 UTC
```

You can see the application address in `juju status`, or get it like so:

```bash
$ juju status --format=json | jq -r '.applications."zinc-k8s".address'
```

You should then be able to browse to `http://<address>:4080` and login with the user `admin`.

## OCI Images

This charm uses [an altered version](https://hub.docker.com/r/jnsgruk/zinc) of the image provided by the upstream, running on `ubuntu` rather than `scratch`. 

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines
on enhancements to this charm following best practice guidelines, and the
[contributing] doc for developer guidance.

[zinc]: https://github.com/prabhatsharma/zinc
[bluge]: https://github.com/blugelabs/bluge
[elasticsearch]: https://www.elastic.co/
[zinc image]: https://gallery.ecr.aws/m5j1b6u0/zinc
[contributing]: https://github.com/jnsgruk/zinc-k8s-operator/blob/main/CONTRIBUTING.md
