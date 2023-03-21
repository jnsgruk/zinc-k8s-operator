FROM public.ecr.aws/zinclabs/zinc:0.4.3@sha256:8b8f1e9c552db2cf3e81b93c5b43c0de65b65c3dad17ed69a820999e58b1e77b AS builder

FROM ubuntu:latest@sha256:67211c14fa74f070d27cc59d69a7fa9aeff8e28ea118ef3babc295a0428a6d21
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
