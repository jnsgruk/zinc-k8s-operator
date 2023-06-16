FROM public.ecr.aws/zinclabs/zinc:0.4.7@sha256:fefa9ee7256a3c9e7a4f95345265ddf03daa912c5662277860bcbbe77088e662 AS builder

FROM ubuntu:latest@sha256:2a357c4bd54822267339e601ae86ee3966723bdbcae640a70ace622cc9470c83
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
