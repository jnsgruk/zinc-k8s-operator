FROM public.ecr.aws/zinclabs/zinc:0.4.5@sha256:fefa9ee7256a3c9e7a4f95345265ddf03daa912c5662277860bcbbe77088e662 AS builder

FROM ubuntu:latest@sha256:dfd64a3b4296d8c9b62aa3309984f8620b98d87e47492599ee20739e8eb54fbf
COPY --from=builder /go/bin/zincsearch /go/bin/zinc

EXPOSE 4080
ENTRYPOINT ["/go/bin/zinc"]
