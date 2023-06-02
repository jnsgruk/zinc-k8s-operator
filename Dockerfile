FROM public.ecr.aws/zinclabs/zinc:0.4.5@sha256:fefa9ee7256a3c9e7a4f95345265ddf03daa912c5662277860bcbbe77088e662 AS builder

FROM ubuntu:latest@sha256:ac58ff7fe25edc58bdf0067ca99df00014dbd032e2246d30a722fa348fd799a5
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
