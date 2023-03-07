FROM public.ecr.aws/zinclabs/zinc:0.4.2@sha256:8b8f1e9c552db2cf3e81b93c5b43c0de65b65c3dad17ed69a820999e58b1e77b AS builder

FROM ubuntu:latest@sha256:2adf22367284330af9f832ffefb717c78239f6251d9d0f58de50b86229ed1427
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
